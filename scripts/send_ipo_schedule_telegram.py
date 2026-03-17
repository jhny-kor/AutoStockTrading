"""Fetch Korean IPO subscription schedules and send them to Telegram."""

from __future__ import annotations

import argparse
from datetime import date
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.notifications import load_telegram_notifier  # noqa: E402
from autostocktrading.services.ipo_schedule import (  # noqa: E402
    fetch_ipo_schedule,
    filter_entries_starting_in_week,
    filter_entries_starting_on_date,
    filter_upcoming_entries,
    format_ipo_schedule_message,
)
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


def parse_iso_date(raw: str) -> date:
    return date.fromisoformat(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send Korean IPO subscription schedules to Telegram."
    )
    parser.add_argument(
        "--mode",
        choices=["upcoming", "today", "this-week"],
        default="upcoming",
        help="Select which IPO schedules to send. Default: upcoming",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many upcoming entries to include. Default: 5",
    )
    parser.add_argument(
        "--include-recent-days",
        type=int,
        default=0,
        help="Also include schedules that ended this many days ago. Default: 0",
    )
    parser.add_argument(
        "--reference-date",
        type=parse_iso_date,
        help="Override the reference date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Also append the send result to the dated JSONL log store.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    notifier = load_telegram_notifier()
    if not notifier.enabled:
        print("[FAIL] Telegram is not enabled. Set TELEGRAM_ENABLED=true in .env.")
        return 1

    try:
        entries = fetch_ipo_schedule()
        if args.mode == "today":
            selected = filter_entries_starting_on_date(
                entries,
                target_date=args.reference_date,
            )
        elif args.mode == "this-week":
            selected = filter_entries_starting_in_week(
                entries,
                reference_date=args.reference_date,
            )
        else:
            selected = filter_upcoming_entries(
                entries,
                today=args.reference_date,
                include_recent_days=args.include_recent_days,
            )
        message = format_ipo_schedule_message(
            selected[: args.limit],
            title=_resolve_title(args.mode, args.reference_date),
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[FAIL] IPO schedule fetch failed: {exc}")
        return 1

    sent, error = notifier.send_message_detailed(message)
    if not sent:
        print(f"[FAIL] Telegram send failed: {error or '알 수 없는 오류'}")
        return 1

    if args.log:
        logger = DailyJsonlLogger(
            LogDirectoryManager(
                log_root=ROOT_DIR / "logs",
                archive_root=ROOT_DIR / "archives",
            )
        )
        log_path = logger.append_event(
            source="telegram",
            category="notifications",
            event_type="ipo_schedule",
            payload={
                "mode": args.mode,
                "reference_date": (
                    args.reference_date.isoformat() if args.reference_date else None
                ),
                "sent": True,
                "entry_count": len(selected[: args.limit]),
            },
        )
        print(f"Logged to: {log_path}")

    print("[OK] IPO schedule sent to Telegram.")
    return 0


def _resolve_title(mode: str, reference_date: date | None) -> str:
    if mode == "today":
        label = reference_date.isoformat() if reference_date else "오늘"
        return f"[오늘 시작하는 공모주 청약 - {label}]"
    if mode == "this-week":
        label = reference_date.isoformat() if reference_date else "이번 주"
        return f"[이번 주 시작하는 공모주 청약 - {label} 기준]"
    return "[공모주 청약일정]"


if __name__ == "__main__":
    raise SystemExit(main())
