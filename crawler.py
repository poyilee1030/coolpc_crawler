"""以 Selenium 4 爬取 coolpc.com.tw，比對價格並在異動時發通知。"""
from __future__ import annotations

import datetime
import logging
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import CATEGORIES, COOLPC_URL, Settings
from database import CategoryDatabase
from notifier import Notifier
from price_parser import parse_item

logger = logging.getLogger(__name__)


class CoolpcCrawler:
    def __init__(self, settings: Settings, notifier: Notifier):
        self.settings = settings
        self.notifier = notifier
        self.driver = None

    def run(self) -> None:
        self.driver = self._build_driver()
        try:
            for category_id in self.settings.category_ids:
                try:
                    self._crawl_category(category_id)
                except Exception:  # 單一類別失敗不該中斷整輪
                    logger.exception("類別 %s 爬取失敗", category_id)
        finally:
            self.driver.quit()
            self.driver = None

    def _build_driver(self):
        # Selenium 4.6+ 內建 Selenium Manager，會自動下載對應的 chromedriver，
        # 不再需要手動放 chromedriver.exe。
        options = Options()
        if self.settings.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,2000")
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(self.settings.implicit_wait)
        return driver

    def _crawl_category(self, category_id: int) -> None:
        key, display = CATEGORIES[category_id]
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info("爬取 %s（%s）", key, display)

        self.driver.get(COOLPC_URL)

        with CategoryDatabase(self.settings.db_dir, key) as db:
            spans = self.driver.find_elements(By.XPATH, '//span[contains(text(), "")]')
            if category_id >= len(spans):
                logger.warning(
                    "類別索引 %s 超出範圍（共 %s 個 span）", category_id, len(spans)
                )
                return
            spans[category_id].click()

            tables = self.driver.find_elements(By.XPATH, '//table[contains(text(), "")]')
            start, end = 3, len(tables) - 2
            for idx in range(start, end):
                table = tables[idx]
                header = table.text.strip()
                table.click()
                changes = self._collect_changes(db, now, table)
                if changes:
                    body = "\n".join(changes)
                    self.notifier.send(f"【{display}】{header}\n{body}")

    def _collect_changes(self, db, now, table) -> List[str]:
        changes: List[str] = []
        for tbody in table.find_elements(By.CSS_SELECTOR, "tbody"):
            for row in tbody.find_elements(By.CSS_SELECTOR, "tr"):
                for td in row.find_elements(By.TAG_NAME, "td"):
                    line = self._process_cell(db, now, td.text)
                    if line:
                        changes.append(line)
        return changes

    def _process_cell(self, db, now, text) -> Optional[str]:
        parsed = parse_item(text)
        if not parsed:
            return None

        name, old_price, new_price = parsed
        if name in self.settings.ignore_items:
            return None

        existing = db.get_latest(name)
        if existing is None:
            # 新商品
            db.insert(now, name, old_price, new_price)
            return f"🆕 新商品　{name}：${new_price}"

        prev_new = _to_int(existing[1])
        if prev_new is None:
            return None  # 通常是分類標題等非價格列

        diff = abs(prev_new - new_price)
        if diff <= self.settings.price_change_threshold:
            return None  # 價差在門檻內，忽略

        db.update(now, name, prev_new, new_price)
        arrow = "↘ 降價" if prev_new > new_price else "↗ 漲價"
        return f"{arrow} {diff}　{name}：${prev_new} → ${new_price}"


def _to_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
