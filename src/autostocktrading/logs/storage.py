"""Date-based JSONL log storage and archival helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import tarfile
from typing import Any


DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _normalize_segment(value: str) -> str:
    normalized = SAFE_SEGMENT_RE.sub("_", value.strip())
    return normalized.strip("._") or "unknown"


def _coerce_json_value(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, ensure_ascii=False, default=str))


@dataclass(frozen=True)
class LogDirectoryManager:
    log_root: Path = Path("logs")
    archive_root: Path = Path("archives")

    def dated_log_dir(self, target_date: date) -> Path:
        return self.log_root / target_date.isoformat()

    def ensure_log_dir(self, target_date: date) -> Path:
        target = self.dated_log_dir(target_date)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def ensure_archive_dir(self) -> Path:
        self.archive_root.mkdir(parents=True, exist_ok=True)
        return self.archive_root


class DailyJsonlLogger:
    def __init__(self, manager: LogDirectoryManager | None = None) -> None:
        self.manager = manager or LogDirectoryManager()

    def append_event(
        self,
        *,
        source: str,
        event_type: str,
        payload: dict[str, Any],
        symbol: str | None = None,
        category: str | None = None,
        target_date: date | None = None,
        occurred_at: datetime | None = None,
    ) -> Path:
        event_time = occurred_at or datetime.now()
        day = target_date or event_time.date()
        date_dir = self.manager.ensure_log_dir(day)

        path = date_dir / _normalize_segment(source)
        if symbol:
            path = path / _normalize_segment(symbol)
        if category:
            path = path / _normalize_segment(category)
        path.mkdir(parents=True, exist_ok=True)

        file_path = path / f"{_normalize_segment(event_type)}.jsonl"
        record = {
            "logged_at": event_time.isoformat(timespec="seconds"),
            "source": source,
            "symbol": symbol,
            "category": category,
            "event_type": event_type,
            "payload": _coerce_json_value(payload),
        }

        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")

        return file_path


def archive_old_log_directories(
    *,
    manager: LogDirectoryManager | None = None,
    keep_days: int = 14,
    today: date | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[Path]:
    if keep_days < 0:
        raise ValueError("keep_days must be zero or greater.")

    directories = manager or LogDirectoryManager()
    current_day = today or datetime.now().date()
    retained_days = max(keep_days, 1)
    earliest_keep_date = current_day - timedelta(days=retained_days - 1)
    archive_root = directories.ensure_archive_dir()

    archived_paths: list[Path] = []

    if not directories.log_root.exists():
        return archived_paths

    for child in sorted(directories.log_root.iterdir()):
        if not child.is_dir() or not DATE_DIR_RE.match(child.name):
            continue

        target_day = date.fromisoformat(child.name)
        if target_day >= earliest_keep_date:
            continue

        archive_path = archive_root / f"logs-{child.name}.tar.gz"
        if archive_path.exists() and not overwrite:
            archived_paths.append(archive_path)
            continue

        if dry_run:
            archived_paths.append(archive_path)
            continue

        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(child, arcname=f"logs/{child.name}")

        _remove_tree(child)
        archived_paths.append(archive_path)

    return archived_paths


def _remove_tree(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _remove_tree(child)
        else:
            child.unlink()
    path.rmdir()
