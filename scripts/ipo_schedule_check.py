"""Fetch Korean IPO subscription schedules and print a Telegram-ready summary."""

from __future__ import annotations

import argparse
from datetime import date
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.services.ipo_schedule import (  # noqa: E402
    fetch_ipo_schedule,
    filter_entries_starting_in_week,
    filter_entries_starting_on_date,
    filter_upcoming_entries,
    format_ipo_schedule_message,
)
from autostocktrading.utils.env import load_env_file  # noqa: E402


def parse_iso_date(raw: str) -> date:
    return date.fromisoformat(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Korean IPO subscription schedules.")
    parser.add_argument(
        "--mode",
        choices=["upcoming", "today", "this-week"],
        default="upcoming",
        help="Select which IPO schedules to show. Default: upcoming",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many upcoming entries to show. Default: 5",
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

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
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[FAIL] IPO schedule fetch failed: {exc}")
        return 1

    print("[OK] IPO schedule fetch succeeded.")
    print(
        format_ipo_schedule_message(
            selected[: args.limit],
            title=_resolve_title(args.mode, args.reference_date),
        )
    )
    return 0


def _resolve_title(mode: str, reference_date: date | None) -> str:
    if mode == "today":
        label = reference_date.isoformat() if reference_date else "오늘"
        return f"[공모주 청약 시작 일정 - {label}]"
    if mode == "this-week":
        label = reference_date.isoformat() if reference_date else "이번 주"
        return f"[공모주 청약 시작 일정 - {label} 기준 주간]"
    return "[공모주 청약일정]"


if __name__ == "__main__":
    raise SystemExit(main())
