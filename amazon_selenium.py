import time
import os
import requests   # LINE Messaging APIとの通信に使用。
import pandas as pd
import json
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

class AmazonPriceMonitor:
    def __init__(self, threshold_price, line_token, line_user_id):
        """
        初期設定：パスの絶対パス化とブラウザの起動
        """
        self.threshold_price = threshold_price
        self.line_token = line_token
        self.line_user_id = line_user_id
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_file = os.path.join(self.base_dir, "amazon_list.csv")
        self.user_data_path = os.path.join(self.base_dir, 'chrome_temp_profile')
        
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """ブラウザの初期設定（Selenium）"""
        options = Options()
        options.add_argument(f'--user-data-dir={self.user_data_path}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def send_line_notification(self, message):
        """
        LINE Messaging APIを使用してスマホへ通知を送る
        """
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.line_token}"
        }
        payload = {
            "to": self.line_user_id,
            "messages": [{"type": "text", "text": message}]
        }

        try:
            # タイムアウトを10秒に設定
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"\n[エラー] LINE通知の送信に失敗しました: {e}")
            return False
   
    def get_product_details(self, url):
        """商品ページからタイトルと価格を取得"""
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 15)
        try:
            title = wait.until(EC.presence_of_element_located((By.ID, "productTitle"))).text.strip()
            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                price_int = int("".join(filter(str.isdigit, price_element.text)))
            except Exception as e:
                print(f"[価格取得失敗] {e}")
                price_int = 0
            return title, price_int
        except Exception as e:
            return None, None

    def fetch_links(self, search_url, limit=5):
        """検索結果から商品リンクを収集"""
        self.driver.get(search_url)
        time.sleep(3)
        links = []
        items = self.driver.find_elements(By.CSS_SELECTOR, 'div.s-result-item a.a-link-normal')
        for item in items:
            link = item.get_attribute('href')
            if link and ("/dp/" in link or "/gp/" in link):
                if link not in links:
                    links.append(link)
        return links[:limit]

    def save_data(self, new_data):
        """重複を排除してCSVへ保存"""
        if not new_data:
            print("\n[報告] 新しい価格変化はありませんでした。")
            return

        df_new = pd.DataFrame(new_data)
        if not os.path.isfile(self.csv_file):
            df_new.to_csv(self.csv_file, index=False, encoding="utf-8-sig")
        else:
            df_old = pd.read_csv(self.csv_file)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            # 「商品名」と「価格」が全く同じ行は最新の1つだけ残して消去
            df_final = df_combined.drop_duplicates(subset=['商品名', '価格'], keep='first')
            df_final.to_csv(self.csv_file, index=False, encoding="utf-8-sig")
        print(f"\n[完了] データを保存しました（新規追加: {len(new_data)}件）")

    def save_to_spreadsheet(self, name, price):
        """取得したデータをGoogleスプレッドシートに追記する"""
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        from datetime import datetime

        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        try:
            secret_key_path = os.path.join(self.base_dir, 'secret_key.json')
            creds = ServiceAccountCredentials.from_json_keyfile_name(secret_key_path, scope)
            client = gspread.authorize(creds)
            # スプレッドシート名が正確に一致している必要があります
            sheet = client.open('Amazon監視データ').sheet1

            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([date_str, name, price])
            print(f"【記録】スプレッドシートへ保存完了: {name}")
        except Exception as e:
            print(f"【エラー】スプレッドシート保存失敗: {e}")

    def run(self, search_url):
        """メイン処理の実行"""
        try:
            links = self.fetch_links(search_url)
            results = []

            for link in tqdm(links, desc="価格チェック中"):
                name, price = self.get_product_details(link)
                if name and price > 0:
                    results.append({
                        "取得日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "商品名": name,
                        "価格": price
                    })
                    
                    # 目標価格以下ならLINE通知を発動
                    if price <= self.threshold_price:
                        msg = f"\n【買い時通知】\n{name}\n現在価格: {price}円\n設定値({self.threshold_price}円)以下です！"
                        self.send_line_notification(msg)
                
                time.sleep(2)

            for item in results:
                self.save_to_spreadsheet(item["商品名"], item["価格"])
            self.save_data(results)

        finally:
            self.driver.quit()

if __name__ == "__main__":
    MY_LINE_TOKEN = os.getenv("LINE_TOKEN")
    MY_LINE_USER_ID = os.getenv("LINE_USER_ID")
    SEARCH_URL = "https://www.amazon.co.jp/s?k=%E3%82%B9%E3%82%A4%E3%83%83%E3%83%81%EF%BC%92&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=PNFXO86G5SS4&sprefix=%E3%82%B9%E3%82%A4%E3%83%83%E3%83%812%2Caps%2C220&ref=nb_sb_noss_1"
    TARGET_PRICE = 58000

    monitor = AmazonPriceMonitor(threshold_price=TARGET_PRICE, line_token=MY_LINE_TOKEN, line_user_id=MY_LINE_USER_ID)
    monitor.run(SEARCH_URL)