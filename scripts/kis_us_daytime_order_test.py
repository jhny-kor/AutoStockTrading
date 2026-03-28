"""Submit a small KIS overseas US daytime order."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.brokers.kis.config import KisConfig  # noqa: E402
from autostocktrading.brokers.kis.overseas import KisOverseasClient, KisOverseasOrderRequest  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Submit a small KIS overseas daytime order.")
    parser.add_argument("--exchange", default="NASD", help="Exchange code for orders. Default: NASD")
    parser.add_argument("--symbol", default="AAPL", help="US stock symbol. Default: AAPL")
    parser.add_argument("--side", default="BUY", choices=["BUY", "SELL"], help="Order side")
    parser.add_argument("--qty", type=int, default=1, help="Order quantity. Default: 1")
    parser.add_argument("--price", type=float, required=True, help="Limit price")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")
    config = KisConfig.from_env()
    client = KisOverseasClient(config)
    request = KisOverseasOrderRequest(
        side=args.side,
        exchange_code=args.exchange,
        symbol=args.symbol,
        quantity=args.qty,
        price=args.price,
        order_division="00",
    )
    response = client.place_daytime_order(request)
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
