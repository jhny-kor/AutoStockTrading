"""Minimal Telegram Bot API sender."""

from __future__ import annotations

from dataclasses import dataclass
import json
import mimetypes
import os
from pathlib import Path
from typing import Any
from uuid import uuid4
from urllib import error, request

from autostocktrading.utils.env import load_env_file


ROOT_DIR = Path(__file__).resolve().parents[3]


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


def _normalize_env_prefix(prefix: str | None) -> str | None:
    if prefix is None:
        prefix = os.getenv("TELEGRAM_ENV_PREFIX")
    if prefix is None:
        return None
    normalized = prefix.strip().upper().strip("_")
    return normalized or None


def _resolve_telegram_env(name: str, prefix: str | None) -> str | None:
    normalized_prefix = _normalize_env_prefix(prefix)
    candidate_keys: list[str] = []
    if normalized_prefix:
        candidate_keys.append(f"{normalized_prefix}_{name}")
    candidate_keys.append(name)
    for key in candidate_keys:
        value = os.getenv(key)
        if value is not None:
            return value
    return None


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

    def send_document(self, file_path: str, caption: str | None = None) -> tuple[bool, str | None]:
        if not self.enabled:
            return False, "텔레그램 알림이 비활성화되어 있습니다."
        if not self.bot_token or not self.chat_id:
            return False, "텔레그램 봇 토큰 또는 chat id 가 비어 있습니다."

        boundary = f"----CodexTelegram{uuid4().hex}"
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as handle:
            file_bytes = handle.read()

        parts: list[bytes] = []
        for name, value in (
            ("chat_id", self.chat_id),
            ("caption", caption or ""),
        ):
            if not value:
                continue
            parts.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                    f"{value}\r\n".encode("utf-8"),
                ]
            )

        parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                file_bytes,
                b"\r\n",
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )

        http_request = request.Request(
            url=f"https://api.telegram.org/bot{self.bot_token}/sendDocument",
            data=b"".join(parts),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=20) as response:
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
            return False, "텔레그램 API 가 문서 전송을 거부했습니다."

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


def load_telegram_notifier(prefix: str | None = None) -> TelegramNotifier:
    # Keep process-level env overrides intact so another bot can inject its own
    # Telegram credentials without being overwritten by this repo's .env file.
    load_env_file(ROOT_DIR / ".env", override=False)
    return TelegramNotifier(
        enabled=_parse_bool(_resolve_telegram_env("TELEGRAM_ENABLED", prefix), default=False),
        bot_token=_resolve_telegram_env("TELEGRAM_BOT_TOKEN", prefix) or "",
        chat_id=_resolve_telegram_env("TELEGRAM_CHAT_ID", prefix) or "",
    )
