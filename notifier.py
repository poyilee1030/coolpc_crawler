"""通知後端。

LINE Notify 已於 2025-03-31 終止服務，這裡改用 Telegram bot 取代，
並保留一個容易擴充的 Notifier 介面（要換 Discord / Email 只要新增一個類別）。
"""
from __future__ import annotations

import abc
import logging

logger = logging.getLogger(__name__)

TELEGRAM_MAX_CHARS = 4096


class Notifier(abc.ABC):
    @abc.abstractmethod
    def send(self, message: str) -> None:
        ...


class ConsoleNotifier(Notifier):
    """把訊息印到 stdout，方便在沒設定 bot 時測試。"""

    def send(self, message: str) -> None:
        print("[notify]\n" + message)


class TelegramNotifier(Notifier):
    def __init__(self, token: str, chat_id: str, timeout: int = 15):
        if not token or not chat_id:
            raise ValueError("TelegramNotifier 需要 bot token 與 chat id")
        self.chat_id = chat_id
        self.timeout = timeout
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"

    def send(self, message: str) -> None:
        import requests  # 延遲匯入：只有真的要發 Telegram 時才需要

        for chunk in _split_message(message, TELEGRAM_MAX_CHARS):
            try:
                resp = requests.post(
                    self._url,
                    data={"chat_id": self.chat_id, "text": chunk},
                    timeout=self.timeout,
                )
                if resp.status_code != 200:
                    logger.error(
                        "Telegram 傳送失敗 (%s): %s", resp.status_code, resp.text
                    )
            except requests.RequestException as exc:
                logger.error("Telegram 連線錯誤: %s", exc)


def _split_message(message: str, limit: int):
    """依行切成不超過 limit 的段落（Telegram 單則上限 4096 字元）。"""
    if len(message) <= limit:
        yield message
        return

    buf = ""
    for line in message.splitlines(keepends=True):
        if len(buf) + len(line) > limit:
            if buf:
                yield buf
                buf = ""
            while len(line) > limit:  # 單行就超長，硬切
                yield line[:limit]
                line = line[limit:]
        buf += line
    if buf:
        yield buf


def build_notifier(settings) -> Notifier:
    """依設定挑選通知後端；沒設定 Telegram 就退回主控台輸出。"""
    if settings.telegram_bot_token and settings.telegram_chat_id:
        return TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    logger.warning("未設定 Telegram 憑證，改用主控台輸出（不會真的發通知）。")
    return ConsoleNotifier()
