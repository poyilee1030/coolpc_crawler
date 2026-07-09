"""SQLite 持久化 —— 每個商品類別一個資料庫檔。

資料表結構刻意與原始專案保持一致（中文欄位名、`<category>_table`），
讓既有的 .sqlite3 檔仍可沿用。
"""
from __future__ import annotations

import os
import sqlite3
from typing import Optional, Tuple

# 時間、名稱、舊價格、新價格
LABELS = ["時間", "名稱", "舊價格", "新價格"]


class CategoryDatabase:
    """單一類別的 SQLite 存取封裝，建議以 context manager 使用。"""

    def __init__(self, db_dir: str, category_key: str):
        self.category_key = category_key
        self.table = f"{category_key}_table"
        os.makedirs(db_dir, exist_ok=True)
        self.path = os.path.join(db_dir, f"{category_key}.sqlite3")
        self.conn = sqlite3.connect(self.path)
        self._create_table()

    def _create_table(self) -> None:
        cols = ", ".join(f'"{label}" TEXT' for label in LABELS)
        self.conn.execute(
            f'CREATE TABLE IF NOT EXISTS "{self.table}" '
            f"(id INTEGER PRIMARY KEY, {cols});"
        )
        self.conn.commit()

    def get_latest(self, name: str) -> Optional[Tuple[str, str]]:
        """回傳該商品最新一筆的 (舊價格, 新價格)，沒有則回傳 None。"""
        cur = self.conn.execute(
            f'SELECT "舊價格", "新價格" FROM "{self.table}" '
            f'WHERE "名稱"=? ORDER BY id DESC LIMIT 1;',
            (name,),
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else None

    def insert(self, time: str, name: str, old_price, new_price) -> None:
        self.conn.execute(
            f'INSERT INTO "{self.table}" ("時間", "名稱", "舊價格", "新價格") '
            f"VALUES (?, ?, ?, ?);",
            (time, name, str(old_price), str(new_price)),
        )
        self.conn.commit()

    def update(self, time: str, name: str, old_price, new_price) -> None:
        self.conn.execute(
            f'UPDATE "{self.table}" SET "時間"=?, "舊價格"=?, "新價格"=? '
            f'WHERE "名稱"=?;',
            (time, str(old_price), str(new_price), name),
        )
        self.conn.commit()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
