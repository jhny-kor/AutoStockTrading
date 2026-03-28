"""Check a KIS overseas stock quote."""

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
from autostocktrading.brokers.kis.overseas import KisOverseasClient  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a KIS overseas stock quote.")
    parser.add_argument("--exchange", default="NAS", help="Exchange code. Example: NAS, NYS, AMS")
    parser.add_argument("--symbol", default="AAPL", help="US stock symbol. Default: AAPL")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")
    client = KisOverseasClient(KisConfig.from_env())
    quote = client.inquire_price(exchange_code=args.exchange, symbol=args.symbol)
    detail = client.inquire_price_detail(exchange_code=args.exchange, symbol=args.symbol)
    print("Quote:")
    print(json.dumps(quote, ensure_ascii=False))
    print("Detail:")
    print(json.dumps(detail, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
