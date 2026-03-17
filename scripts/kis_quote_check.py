"""Fetch a simple domestic stock quote from KIS Open API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.brokers.kis import KisApiClient, KisConfig  # noqa: E402
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch a domestic stock quote from KIS.")
    parser.add_argument(
        "--symbol",
        default="005930",
        help="Domestic stock code to query. Default: 005930 (Samsung Electronics)",
    )
    parser.add_argument(
        "--market-code",
        default="J",
        help="KIS market division code. Default: J",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Also append the quote response to the dated JSONL log store.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        load_env_file(ROOT_DIR / ".env")
        config = KisConfig.from_env()
        client = KisApiClient(config)
        response = client.inquire_price(
            symbol=args.symbol,
            market_code=args.market_code,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[FAIL] KIS quote lookup failed: {exc}")
        return 1

    output = response.get("output") or {}
    message = response.get("msg1", "")
    current_price = output.get("stck_prpr")
    change_sign = output.get("prdy_vrss_sign")
    change_amount = output.get("prdy_vrss")
    symbol_name = output.get("hts_kor_isnm")

    print("[OK] KIS quote lookup succeeded.")
    print(f"Environment: {'virtual' if config.use_virtual else 'production'}")
    print(f"Symbol: {args.symbol}")
    print(f"Name: {symbol_name}")
    print(f"Current price: {current_price}")
    print(f"Change sign: {change_sign}")
    print(f"Change amount: {change_amount}")
    if message:
        print(f"Message: {message}")

    if args.log:
        logger = DailyJsonlLogger(
            LogDirectoryManager(
                log_root=ROOT_DIR / "logs",
                archive_root=ROOT_DIR / "archives",
            )
        )
        log_path = logger.append_event(
            source="kis",
            symbol=args.symbol,
            category="market",
            event_type="quote",
            payload=response,
        )
        print(f"Logged to: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
