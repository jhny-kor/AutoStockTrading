"""Collect US stock analysis snapshots for KIS overseas trading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.brokers.kis import KisConfig, KisOverseasClient  # noqa: E402
from autostocktrading.config.us_strategy_watchlists import get_us_long_term_entries  # noqa: E402
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402
from autostocktrading.services.us_stock_analysis import build_us_stock_snapshot  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect US stock snapshots via KIS overseas API.")
    parser.add_argument("--once", action="store_true", help="Collect one pass and exit.")
    parser.add_argument("--poll-sec", type=int, default=300, help="Polling interval seconds. Default: 300")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")
    client = KisOverseasClient(KisConfig.from_env())
    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "us_analysis_logs",
            archive_root=ROOT_DIR / "archives" / "us_analysis_logs",
        )
    )

    entries = get_us_long_term_entries()
    while True:
        token = client.get_access_token()
        for entry in entries:
            quote = client.inquire_price(exchange_code=entry.exchange_quote, symbol=entry.symbol, token=token)
            detail = client.inquire_price_detail(exchange_code=entry.exchange_quote, symbol=entry.symbol, token=token)
            snapshot = build_us_stock_snapshot(entry=entry, quote_response=quote, detail_response=detail)
            path = logger.append_event(
                source="kis_us_analysis",
                symbol=entry.symbol,
                category="stocks",
                event_type="snapshot",
                payload=snapshot,
            )
            print(json.dumps({"symbol": entry.symbol, "name": entry.name, "path": str(path), "current_price": snapshot.get("current_price")}, ensure_ascii=False))
        if args.once:
            break
        time.sleep(max(args.poll_sec, 30))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
