"""Write a sample dated JSONL log entry."""

from __future__ import annotations

import argparse
from datetime import date
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402


def parse_iso_date(raw: str) -> date:
    return date.fromisoformat(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a sample JSONL log event.")
    parser.add_argument("--source", default="kis", help="Log source. Default: kis")
    parser.add_argument("--symbol", default="005930", help="Symbol bucket. Default: 005930")
    parser.add_argument("--event-type", default="quote", help="Event file name. Default: quote")
    parser.add_argument("--category", default="market", help="Optional category directory.")
    parser.add_argument(
        "--date",
        type=parse_iso_date,
        help="Override target log date in YYYY-MM-DD format.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "logs",
            archive_root=ROOT_DIR / "archives",
        )
    )

    log_path = logger.append_event(
        source=args.source,
        symbol=args.symbol,
        category=args.category,
        event_type=args.event_type,
        target_date=args.date,
        payload={
            "message": "demo log event",
            "source": args.source,
            "symbol": args.symbol,
        },
    )

    print("[OK] Demo log event written.")
    print(log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
