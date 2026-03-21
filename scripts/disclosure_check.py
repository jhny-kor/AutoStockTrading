"""Fetch recent OpenDART disclosures for the stock watchlist."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import os
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.config import DEFAULT_ANALYSIS_WATCHLIST, get_default_symbols  # noqa: E402
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402
from autostocktrading.services.disclosures import (  # noqa: E402
    fetch_recent_disclosures,
    format_disclosures_text,
)
from autostocktrading.utils.env import load_env_file  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch recent OpenDART disclosures.")
    parser.add_argument(
        "--symbols",
        default=",".join(get_default_symbols()),
        help="Comma-separated stock codes. Default: watchlist symbols",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Look back this many days. Default: 7",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Also append the fetched disclosures into disclosure_logs.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    api_key = os.getenv("DART_API_KEY", "").strip()
    if not api_key:
        print("[FAIL] DART_API_KEY is not set in .env.")
        return 1

    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    end_date = date.today()
    begin_date = end_date - timedelta(days=max(args.days - 1, 0))

    try:
        disclosures = fetch_recent_disclosures(
            api_key=api_key,
            stock_codes=symbols,
            begin_date=begin_date,
            end_date=end_date,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[FAIL] Disclosure fetch failed: {exc}")
        return 1

    print("[OK] Disclosure fetch succeeded.")
    print(format_disclosures_text(disclosures))

    if args.log:
        logger = DailyJsonlLogger(
            LogDirectoryManager(
                log_root=ROOT_DIR / "disclosure_logs",
                archive_root=ROOT_DIR / "archives" / "disclosure_logs",
            )
        )
        logger.append_event(
            source="opendart",
            category="disclosures",
            event_type="recent_watchlist",
            payload={
                "watchlist": [
                    {
                        "symbol": entry.symbol,
                        "name": entry.name,
                    }
                    for entry in DEFAULT_ANALYSIS_WATCHLIST
                    if entry.symbol in symbols
                ],
                "begin_date": begin_date.isoformat(),
                "end_date": end_date.isoformat(),
                "count": len(disclosures),
                "items": [item.__dict__ for item in disclosures],
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
