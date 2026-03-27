"""Poll order status and send Telegram updates for fills/unfilled orders."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.services.order_notifications import poll_and_notify_order_statuses  # noqa: E402


LONG_STATE = ROOT_DIR / "logs" / "state" / "kr_long_term_trader.json"
SHORT_STATE = ROOT_DIR / "logs" / "state" / "kr_short_term_trader.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch order fills and send Telegram updates.")
    parser.add_argument("--once", action="store_true", help="Run one polling pass and exit.")
    parser.add_argument("--poll-sec", type=int, default=20, help="Polling interval in seconds. Default: 20")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    while True:
        poll_and_notify_order_statuses(LONG_STATE)
        poll_and_notify_order_statuses(SHORT_STATE)
        if args.once:
            break
        time.sleep(max(args.poll_sec, 10))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
