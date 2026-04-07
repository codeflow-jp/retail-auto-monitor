# 🛒 Amazon Price Monitor — LINE通知付き価格監視ツール

> 指定したAmazon商品の価格を自動監視し、目標価格を下回った瞬間にLINEへ通知するPython製ツールです。

---

## ✅ できること

| 機能 | 詳細 |
|------|------|
| 価格の自動取得 | Seleniumによるブラウザ自動操作で、検索結果から商品情報をスクレイピング |
| リアルタイムLINE通知 | 目標価格以下を検知した瞬間、LINE Messaging APIでスマホへプッシュ通知 |
| データの自動保存 | 取得した価格履歴をCSVへ重複排除して蓄積 |
| スプレッドシート連携 | Google Sheets APIを通じて監視データをクラウド上に自動記録 |

---

## 🖼️ 動作イメージ

```
① Amazonの検索結果ページを自動巡回
        ↓
② 各商品ページから「商品名・価格」を取得
        ↓
③ 目標価格以下 → LINEにプッシュ通知
        ↓
④ 取得データをCSV・Googleスプレッドシートに自動保存
```

---

## 🛠️ 使用技術

| カテゴリ | 技術・ライブラリ |
|----------|----------------|
| 言語 | Python 3.14 |
| ブラウザ自動操作 | Selenium / ChromeDriver |
| 通知 | LINE Messaging API |
| データ管理 | pandas / CSV |
| クラウド連携 | Google Sheets API（gspread） |
| セキュリティ | python-dotenv（機密情報の環境変数管理） |
| 稼働環境 | Windows 11 / Chrome |

---

## 🔧 セットアップ手順

### 1. リポジトリをクローン
```bash
git clone https://github.com/yourname/amazon-price-monitor.git
cd amazon-price-monitor
```

### 2. 必要ライブラリをインストール
```bash
pip install selenium webdriver-manager requests pandas gspread oauth2client python-dotenv tqdm
```

### 3. 環境変数を設定
プロジェクトルートに `.env` ファイルを作成し、以下を記述：
```
LINE_TOKEN=あなたのLINE Messaging APIトークン
LINE_USER_ID=あなたのLINEユーザーID
```

### 4. Googleスプレッドシート連携（任意）
- GCP でサービスアカウントを作成し、`secret_key.json` をプロジェクトルートに配置
- スプレッドシート名を `Amazon監視データ` に設定し、サービスアカウントを共有

### 5. 実行
```bash
python amazon_selenium.py
```

---

## ⚙️ カスタマイズ

`amazon_selenium.py` の末尾で以下を変更できます：

```python
SEARCH_URL  = "監視したいAmazonの検索URL"
TARGET_PRICE = 58000  # 通知を受け取りたい目標価格（円）
```

---

## 🚧 開発で解決した技術課題

| 課題 | 原因 | 解決策 |
|------|------|--------|
| LINE通知が届かない | LINE Notifyのサービス終了 | Messaging APIへ全面移行し、コードを再設計 |
| ネットワーク接続エラー | DNS設定の不安定さ | Google Public DNS（8.8.8.8）に変更し安定化 |
| データが保存されずクラッシュ | 変数スコープの設計ミス | `__init__` で適切に初期化、ループ構造を改善 |
| エラー原因の特定が困難 | 裸の `except` で全エラーを握り潰していた | `except Exception as e` に変更しログ出力を追加 |

---

## 🔮 今後の拡張予定

- **複数商品の同時監視** — CSVから複数URLを読み込み、一括チェック
- **Googleスプレッドシートへの価格推移グラフ自動生成** — GASとの連携
- **Windowsタスクスケジューラによる完全自動実行** — 定時実行の自動化

---

## 📁 ファイル構成

```
amazon-price-monitor/
├── amazon_selenium.py   # メインスクリプト
├── amazon_list.csv      # 価格履歴データ（自動生成）
├── secret_key.json      # GCP サービスアカウントキー（非公開）
├── .env                 # 環境変数（非公開）
├── .gitignore           # secret_key.json / .env を除外
└── README.md
```

---

## 📝 ライセンス

MIT License