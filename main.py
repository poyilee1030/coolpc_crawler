"""進入點：爬取 coolpc、與 SQLite 比對價格、有異動就發通知。

設定全部來自環境變數 / .env（見 .env.example）。
若 CRAWL_INTERVAL_MINUTES > 0 會常駐每隔 N 分鐘跑一次；
否則只跑一次（建議交給 Windows 工作排程器 / cron）。
"""
import logging
import time

from config import Settings
from crawler import CoolpcCrawler
from notifier import build_notifier


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = Settings.from_env()
    notifier = build_notifier(settings)

    interval = settings.crawl_interval_minutes
    while True:
        CoolpcCrawler(settings, notifier).run()
        if interval <= 0:
            break
        logging.info("休息 %s 分鐘後再爬一次...", interval)
        time.sleep(interval * 60)


if __name__ == "__main__":
    main()
