"""從 coolpc 表格文字中解析出商品名稱與價格的純函式。"""
from __future__ import annotations

from typing import Optional, Tuple


def parse_item(text: str) -> Optional[Tuple[str, int, int]]:
    """把類似 'name,$old $new' 的字串解析成 (名稱, 舊價, 新價)。

    沒有 ',' 或逗號在開頭時（代表不是商品列）回傳 None。
    只有一個價格時，新價會沿用舊價。
    """
    pos = text.find(",")
    if pos <= 0:  # 對齊原始邏輯：pos 必須 > 0
        return None

    name = text[:pos].strip()
    rest = text[pos + 1:]

    price1, end1 = _find_price(rest)
    if price1 is None:
        return None

    price2, _ = _find_price(rest[end1:])
    if price2 is None:
        price2 = price1

    return name, price1, price2


def _find_price(text: str) -> Tuple[Optional[int], int]:
    """找出第一個以 '$' 開頭的整數；千分位逗號會被忽略。

    回傳 (價格, 在 text 中的結束索引)；找不到時回傳 (None, -1)。
    """
    pos = text.find("$")
    if pos < 0:
        return None, -1

    digits = ""
    i = pos + 1
    while i < len(text):
        c = text[i]
        if c.isdigit():
            digits += c
        elif c == ",":
            pass  # 千分位分隔符，跳過（原始版本在這裡會誤判）
        else:
            break
        i += 1

    if not digits:
        return None, i
    return int(digits), i
