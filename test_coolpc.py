"""單元測試，只依賴標準函式庫，執行：

    py -m unittest test_coolpc -v      # Windows
    python -m unittest test_coolpc -v  # 其他平台

不需要安裝 selenium / requests / python-dotenv 就能跑（crawler 會延遲匯入
selenium，notifier 會延遲匯入 requests）。
"""
import logging
import tempfile
import unittest

# 測試中會刻意觸發「未設定 Telegram」等警告，關掉 logging 讓輸出乾淨。
logging.disable(logging.CRITICAL)

from config import Settings
from crawler import CoolpcCrawler, _to_int
from database import CategoryDatabase
from notifier import ConsoleNotifier, TelegramNotifier, _split_message, build_notifier
from price_parser import _find_price, parse_item


class TestPriceParser(unittest.TestCase):
    def test_basic_two_prices(self):
        self.assertEqual(parse_item("Intel i5,$5000 $4800"), ("Intel i5", 5000, 4800))

    def test_single_price_is_reused_as_new(self):
        self.assertEqual(parse_item("RAM 16G,$1200"), ("RAM 16G", 1200, 1200))

    def test_thousands_separator_single(self):
        # 原始版本會在千分位逗號截斷，這裡必須拿到完整的 41990。
        self.assertEqual(parse_item("RTX 4090,$41,990"), ("RTX 4090", 41990, 41990))

    def test_thousands_separator_two_prices(self):
        self.assertEqual(parse_item("VGA,$45,000 $41,990"), ("VGA", 45000, 41990))

    def test_name_is_stripped(self):
        name, _, _ = parse_item(" Foo ,$100")
        self.assertEqual(name, "Foo")

    def test_no_comma_returns_none(self):
        self.assertIsNone(parse_item("no comma here"))

    def test_comma_at_start_returns_none(self):
        self.assertIsNone(parse_item(",$100"))

    def test_no_price_returns_none(self):
        self.assertIsNone(parse_item("name,no dollar here"))


class TestFindPrice(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(_find_price("$100 abc"), (100, 4))

    def test_thousands(self):
        self.assertEqual(_find_price("$41,990"), (41990, 7))

    def test_missing_dollar(self):
        self.assertEqual(_find_price("no dollar"), (None, -1))

    def test_dollar_with_no_digits(self):
        price, _ = _find_price("$ abc")
        self.assertIsNone(price)


class TestSplitMessage(unittest.TestCase):
    def test_short_message_single_chunk(self):
        self.assertEqual(list(_split_message("hello", 10)), ["hello"])

    def test_exactly_at_limit_single_chunk(self):
        msg = "a" * 10
        self.assertEqual(list(_split_message(msg, 10)), [msg])

    def test_multiline_split_preserves_content(self):
        msg = "\n".join(f"line{i}" for i in range(50))
        chunks = list(_split_message(msg, 20))
        self.assertTrue(all(len(c) <= 20 for c in chunks))
        self.assertEqual("".join(chunks), msg)
        self.assertGreater(len(chunks), 1)

    def test_single_overlong_line_is_hard_split(self):
        msg = "x" * 25
        chunks = list(_split_message(msg, 10))
        self.assertTrue(all(len(c) <= 10 for c in chunks))
        self.assertEqual("".join(chunks), msg)


class TestBuildNotifier(unittest.TestCase):
    def test_falls_back_to_console_without_credentials(self):
        notifier = build_notifier(Settings())
        self.assertIsInstance(notifier, ConsoleNotifier)

    def test_uses_telegram_when_credentials_present(self):
        notifier = build_notifier(Settings(telegram_bot_token="t", telegram_chat_id="c"))
        self.assertIsInstance(notifier, TelegramNotifier)

    def test_telegram_requires_both_token_and_chat_id(self):
        with self.assertRaises(ValueError):
            TelegramNotifier("", "c")
        with self.assertRaises(ValueError):
            TelegramNotifier("t", "")


class TestCategoryDatabase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_get_latest_missing_returns_none(self):
        with CategoryDatabase(self.db_dir, "cpu") as db:
            self.assertIsNone(db.get_latest("nope"))

    def test_insert_then_get_latest(self):
        with CategoryDatabase(self.db_dir, "cpu") as db:
            db.insert("t1", "X", 100, 90)
            self.assertEqual(db.get_latest("X"), ("100", "90"))

    def test_update_overwrites(self):
        with CategoryDatabase(self.db_dir, "cpu") as db:
            db.insert("t1", "X", 100, 90)
            db.update("t2", "X", 90, 80)
            self.assertEqual(db.get_latest("X"), ("90", "80"))

    def test_persists_across_connections(self):
        with CategoryDatabase(self.db_dir, "cpu") as db:
            db.insert("t1", "X", 100, 90)
        with CategoryDatabase(self.db_dir, "cpu") as db2:
            self.assertEqual(db2.get_latest("X"), ("100", "90"))

    def test_context_manager_closes_connection(self):
        db = CategoryDatabase(self.db_dir, "cpu")
        with db:
            pass
        self.assertIsNone(db.conn)


class TestToInt(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(_to_int("41990"), 41990)

    def test_none(self):
        self.assertIsNone(_to_int(None))

    def test_non_numeric(self):
        self.assertIsNone(_to_int("abc"))


class TestProcessCell(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(db_dir=self._tmp.name)
        self.crawler = CoolpcCrawler(self.settings, ConsoleNotifier())

    def tearDown(self):
        self._tmp.cleanup()

    def _cell(self, db, text):
        return self.crawler._process_cell(db, "t", text)

    def test_new_item_is_inserted_and_announced(self):
        with CategoryDatabase(self.settings.db_dir, "cpu") as db:
            line = self._cell(db, "Foo,$100 $90")
            self.assertIn("新商品", line)
            self.assertEqual(db.get_latest("Foo"), ("100", "90"))

    def test_change_below_threshold_is_ignored(self):
        with CategoryDatabase(self.settings.db_dir, "cpu") as db:
            self._cell(db, "Foo,$100 $100")  # 建立基準：新價 100
            line = self._cell(db, "Foo,$100 $105")  # 價差 5 <= 門檻 10
            self.assertIsNone(line)
            self.assertEqual(db.get_latest("Foo"), ("100", "100"))  # 未更新

    def test_price_increase_over_threshold(self):
        with CategoryDatabase(self.settings.db_dir, "cpu") as db:
            self._cell(db, "Foo,$100 $100")
            line = self._cell(db, "Foo,$100 $200")
            self.assertIn("漲價", line)
            self.assertIn("100", line)
            self.assertEqual(db.get_latest("Foo"), ("100", "200"))

    def test_direction_uses_integer_comparison(self):
        # 迴歸測試：原始版本以字串比較（"100" > "9" 為 False，會誤判成漲價）。
        with CategoryDatabase(self.settings.db_dir, "cpu") as db:
            self._cell(db, "Bar,$100 $100")  # 基準新價 100
            line = self._cell(db, "Bar,$100 $9")  # 100 -> 9，應為降價
            self.assertIn("降價", line)
            self.assertNotIn("漲價", line)

    def test_ignore_items_are_skipped(self):
        self.settings.ignore_items = ["Foo"]
        with CategoryDatabase(self.settings.db_dir, "cpu") as db:
            line = self._cell(db, "Foo,$100 $90")
            self.assertIsNone(line)
            self.assertIsNone(db.get_latest("Foo"))  # 被忽略，不進 DB


if __name__ == "__main__":
    unittest.main()
