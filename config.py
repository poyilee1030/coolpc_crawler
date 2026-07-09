"""集中管理設定。

祕密金鑰與可調參數都來自環境變數（可透過 .env 檔載入），
完整清單見 .env.example。
"""
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv 為選用；沒有它也能直接讀環境變數
    pass


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

COOLPC_URL = "https://www.coolpc.com.tw/m/"

# 類別 id -> (資料庫/資料表用的英文 key, 通知顯示用的中文名稱)
CATEGORIES = {
    4: ("cpu", "處理器 CPU"),
    5: ("mb", "主機板"),
    6: ("ram", "記憶體"),
    7: ("ssd", "固態硬碟 SSD"),
    8: ("hdd", "傳統硬碟 HDD"),
    10: ("air_cooler", "空冷散熱"),
    11: ("water_cooler", "水冷散熱"),
    12: ("vga", "顯示卡"),
    13: ("monitor", "螢幕"),
    14: ("case", "機殼"),
    15: ("power", "電源供應器"),
    16: ("case_cooler", "機殼散熱/配件"),
    17: ("keyboard", "鍵盤"),
    18: ("mouse", "滑鼠"),
    19: ("network", "網路卡/AP"),
    20: ("nas", "NAS/IP Cam"),
    21: ("tv_box", "電視卡/棒/盒"),
    22: ("speaker", "喇叭/耳麥/音效"),
    23: ("cd_dvd", "燒錄機"),
    24: ("usb", "USB/HD 週邊"),
    30: ("welfare", "福利品出清"),
}

# 預設要爬的類別（順序與原始 main.py 相同）
DEFAULT_CATEGORY_IDS = [4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 30]


def _get_int(name, default):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _get_bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    db_dir: str = os.path.join(PROJECT_ROOT, "data")
    headless: bool = True
    implicit_wait: int = 5
    price_change_threshold: int = 10
    crawl_interval_minutes: int = 0  # 0 = 只跑一次
    category_ids: list = field(default_factory=lambda: list(DEFAULT_CATEGORY_IDS))
    ignore_items: list = field(default_factory=list)

    @classmethod
    def from_env(cls):
        ids_raw = os.environ.get("CATEGORY_IDS", "").strip()
        if ids_raw:
            category_ids = [int(x) for x in ids_raw.split(",") if x.strip()]
        else:
            category_ids = list(DEFAULT_CATEGORY_IDS)

        db_dir = os.environ.get("DB_DIR", "data")
        if not os.path.isabs(db_dir):
            db_dir = os.path.join(PROJECT_ROOT, db_dir)

        return cls(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            db_dir=db_dir,
            headless=_get_bool("HEADLESS", True),
            implicit_wait=_get_int("IMPLICIT_WAIT", 5),
            price_change_threshold=_get_int("PRICE_CHANGE_THRESHOLD", 10),
            crawl_interval_minutes=_get_int("CRAWL_INTERVAL_MINUTES", 0),
            category_ids=category_ids,
        )
