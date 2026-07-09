<p float="left">
  <img src="/coolpc.jpg" width="480" />
</p>

# coolpc_crawler

這個爬蟲會抓取原價屋（coolpc）指定類別的所有商品與價格，
每個類別各建立一個 SQLite 資料庫，並在偵測到價格異動時發送通知。

> **通知方式已改用 Telegram。**
> LINE Notify 已於 2025-03-31 終止服務，原本的 `line_notify.py` 已移除，
> 改為可抽換的 `notifier.py`（預設 Telegram，未設定時退回主控台輸出）。

---

## 專案結構

| 檔案 | 說明 |
|------|------|
| `main.py` | 進入點：載入設定、建立 notifier、執行爬蟲 |
| `config.py` | 所有設定與類別對照表（讀環境變數 / `.env`） |
| `crawler.py` | Selenium 4 爬蟲與價格比對邏輯 |
| `database.py` | SQLite 存取（每類別一個 `.sqlite3`，欄位結構與舊版相容） |
| `price_parser.py` | 從表格文字解析名稱與價格的純函式 |
| `notifier.py` | 通知後端（Telegram / 主控台，易於擴充 Discord、Email） |

---

## 安裝

1. 安裝 Python 3.9 以上。
2. 安裝套件：

   ```bash
   pip install -r requirements.txt
   ```

3. 確認本機已安裝 Chrome 瀏覽器。
   **不需要**再手動下載 `chromedriver.exe` —— Selenium 4.6+ 內建的
   Selenium Manager 會自動下載對應版本。

---

## 設定 Telegram 通知

1. 在 Telegram 搜尋 **@BotFather**，用 `/newbot` 建立 bot，取得 **token**。
2. 主動跟你的 bot 傳一則訊息（或把它加進群組並發言）。
3. 瀏覽器打開 `https://api.telegram.org/bot<你的token>/getUpdates`，
   在回傳 JSON 中找到 `chat.id`。
4. 複製 `.env.example` 成 `.env`，填入：

   ```
   TELEGRAM_BOT_TOKEN=你的token
   TELEGRAM_CHAT_ID=你的chat_id
   ```

> 未填 Telegram 設定時，程式不會報錯，會改用主控台輸出（方便先測試爬蟲）。

---

## 執行

```bash
python main.py
```

- 預設 `CRAWL_INTERVAL_MINUTES=0`：跑一次就結束，建議搭配
  **Windows 工作排程器** 或 **cron** 定時執行（例如每小時）。
- 若設成大於 0（例如 `60`），程式會常駐，每隔 N 分鐘自動爬一次。

---

## 可調設定（`.env`）

| 變數 | 預設 | 說明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |
| `TELEGRAM_CHAT_ID` | — | 接收通知的 chat id |
| `DB_DIR` | `data` | SQLite 檔存放目錄（相對路徑以專案根為基準） |
| `HEADLESS` | `true` | Chrome 是否無頭模式 |
| `IMPLICIT_WAIT` | `5` | Selenium 隱式等待秒數 |
| `PRICE_CHANGE_THRESHOLD` | `10` | 價差超過多少元才通知 |
| `CRAWL_INTERVAL_MINUTES` | `0` | 每隔幾分鐘爬一次；0 = 只跑一次 |
| `CATEGORY_IDS` | 預設清單 | 要爬的類別 id，逗號分隔，例：`4,12,15` |

類別 id 對照表見 `config.py` 的 `CATEGORIES`。

---

## English summary

This crawler fetches products and prices from coolpc for the selected
categories, stores each category in its own SQLite database, and notifies you
of price changes.

**Notifications now use Telegram** — LINE Notify was shut down on 2025-03-31, so
`line_notify.py` was removed and replaced by a pluggable `notifier.py`.

Setup: `pip install -r requirements.txt`, install Chrome (no manual chromedriver
needed — Selenium Manager handles it), copy `.env.example` to `.env`, fill in
your Telegram bot token and chat id, then run `python main.py`. Configure the
run via the environment variables listed above.
