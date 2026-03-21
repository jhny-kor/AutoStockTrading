"""Fetch recent news for the stock watchlist."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.config import DEFAULT_ANALYSIS_WATCHLIST, get_default_symbols  # noqa: E402
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402
from autostocktrading.services.news import (  # noqa: E402
    fetch_stock_news,
    format_news_text,
    news_items_to_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch recent watchlist news.")
    parser.add_argument(
        "--symbols",
        default=",".join(get_default_symbols()),
        help="Comma-separated stock codes. Default: watchlist symbols",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Look back this many days in Google News RSS. Default: 7",
    )
    parser.add_argument(
        "--per-symbol-limit",
        type=int,
        default=3,
        help="How many items per symbol to print. Default: 3",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Also append the fetched news into news_logs.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]

    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "news_logs",
            archive_root=ROOT_DIR / "archives" / "news_logs",
        )
    )

    for symbol in symbols:
        try:
            items = fetch_stock_news(symbol, days=args.days)
        except Exception as exc:  # pragma: no cover - CLI error path
            print(f"[FAIL] {symbol} news fetch failed: {exc}")
            continue

        watch = next((entry for entry in DEFAULT_ANALYSIS_WATCHLIST if entry.symbol == symbol), None)
        name = watch.name if watch else symbol
        print(f"[{name} {symbol}]")
        print(format_news_text(items, limit=args.per_symbol_limit))
        print("")

        if args.log:
            logger.append_event(
                source="google_news",
                symbol=symbol,
                category="watchlist",
                event_type="recent_news",
                payload={
                    "days": args.days,
                    "count": len(items),
                    "items": news_items_to_payload(items),
                },
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
