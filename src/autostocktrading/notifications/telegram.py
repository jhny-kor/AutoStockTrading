"""Minimal Telegram Bot API sender."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib import error, request


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _extract_api_error_detail(body: bytes) -> str | None:
    if not body:
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    description = payload.get("description")
    return description.strip() if isinstance(description, str) and description.strip() else None


def format_telegram_request_error(exc: Exception) -> str:
    if isinstance(exc, error.HTTPError):
        detail = _extract_api_error_detail(exc.read())
        status = f"HTTP {exc.code}"
        if exc.reason:
            status = f"{status} {exc.reason}"
        return f"{status}: {detail}" if detail else status
    if isinstance(exc, error.URLError):
        return f"네트워크 오류: {exc.reason}"
    if isinstance(exc, TimeoutError):
        return "요청 시간이 초과되었습니다."
    return repr(exc)


@dataclass(frozen=True)
class TelegramNotifier:
    enabled: bool
    bot_token: str
    chat_id: str

    def send_message_detailed(self, text: str) -> tuple[bool, str | None]:
        if not self.enabled:
            return False, "텔레그램 알림이 비활성화되어 있습니다."
        if not self.bot_token or not self.chat_id:
            return False, "텔레그램 봇 토큰 또는 chat id 가 비어 있습니다."

        payload = json.dumps({"chat_id": self.chat_id, "text": text}).encode("utf-8")
        http_request = request.Request(
            url=f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=10) as response:
                raw_body = response.read().decode("utf-8")
        except (error.HTTPError, error.URLError, TimeoutError, ValueError) as exc:
            return False, format_telegram_request_error(exc)

        try:
            parsed: Any = json.loads(raw_body)
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            return False, format_telegram_request_error(exc)

        if isinstance(parsed, dict) and parsed.get("ok") is False:
            description = parsed.get("description")
            if isinstance(description, str) and description.strip():
                return False, description.strip()
            return False, "텔레그램 API 가 요청을 거부했습니다."

        return True, None

    def send_message_chunks(self, text: str, limit: int = 3900) -> tuple[bool, str | None]:
        chunks = split_telegram_text(text, limit=limit)
        for chunk in chunks:
            sent, error = self.send_message_detailed(chunk)
            if not sent:
                return False, error
        return True, None


def split_telegram_text(text: str, limit: int = 3900) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return [""]
    if len(normalized) <= limit:
        return [normalized]

    chunks: list[str] = []
    remaining = normalized
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def load_telegram_notifier() -> TelegramNotifier:
    return TelegramNotifier(
        enabled=_parse_bool(os.getenv("TELEGRAM_ENABLED"), default=False),
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
