"""Small JSON state helpers for long-running processes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_state(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {} if default is None else dict(default)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {} if default is None else dict(default)
    if not isinstance(payload, dict):
        return {} if default is None else dict(default)
    if default is None:
        return payload
    merged = dict(default)
    merged.update(payload)
    return merged


def save_json_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
