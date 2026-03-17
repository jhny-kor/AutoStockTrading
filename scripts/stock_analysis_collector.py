"""Collect dated analysis snapshots for selected Korean stocks."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.brokers.kis import KisApiClient, KisConfig  # noqa: E402
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager  # noqa: E402
from autostocktrading.services.stock_analysis import (  # noqa: E402
    build_stock_analysis_snapshot,
    parse_daily_bars,
)
from autostocktrading.strategies import evaluate_buy_candidate  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


DEFAULT_SYMBOLS = ["005930", "000660"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect stock analysis snapshots for Samsung Electronics and SK hynix."
    )
    parser.add_argument(
        "--symbols",
        default=",".join(DEFAULT_SYMBOLS),
        help="Comma-separated stock codes. Default: 005930,000660",
    )
    parser.add_argument(
        "--interval-sec",
        type=int,
        default=300,
        help="Polling interval in seconds for loop mode. Default: 300",
    )
    parser.add_argument(
        "--history-days",
        type=int,
        default=180,
        help="How many calendar days of history to request for daily analysis. Default: 180",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Collect a single snapshot batch and exit.",
    )
    return parser


def sanitize_symbol(symbol: str) -> str:
    return symbol.strip()


def collect_symbol_snapshot(
    client: KisApiClient,
    analysis_logger: DailyJsonlLogger,
    strategy_logger: DailyJsonlLogger,
    *,
    symbol: str,
    history_days: int,
) -> tuple[Path, Path, dict[str, object], dict[str, object]]:
    token = client.get_access_token()
    quote_response = client.inquire_price(symbol, token=token)

    today = datetime.now().date()
    start_date = (today - timedelta(days=history_days)).strftime("%Y%m%d")
    end_date = today.strftime("%Y%m%d")

    try:
        daily_response = client.inquire_daily_itemchart_price(
            symbol,
            start_date=start_date,
            end_date=end_date,
            token=token,
        )
        daily_bars = parse_daily_bars(daily_response)
    except Exception:
        daily_response = client.inquire_daily_price(symbol, token=token)
        daily_bars = parse_daily_bars(daily_response)

    snapshot = build_stock_analysis_snapshot(
        symbol=symbol,
        quote_response=quote_response,
        daily_bars=daily_bars,
    )
    decision = evaluate_buy_candidate(snapshot)

    analysis_log_path = analysis_logger.append_event(
        source="kis_analysis",
        symbol=symbol,
        category="stocks",
        event_type="snapshot",
        payload=snapshot,
    )
    strategy_log_path = strategy_logger.append_event(
        source="stock_strategy",
        symbol=symbol,
        category="korean_bluechips",
        event_type="buy_candidate",
        payload=decision,
    )
    print(
        json.dumps(
            {
                "symbol": symbol,
                "name": snapshot.get("name"),
                "current_price": snapshot.get("current_price"),
                "rsi_14": snapshot.get("rsi_14"),
                "volume_ratio_20": snapshot.get("volume_ratio_20"),
                "breakout_watch": snapshot.get("breakout_watch"),
                "pullback_watch": snapshot.get("pullback_watch"),
                "buy_candidate": decision.get("buy_candidate"),
                "candidate_type": decision.get("candidate_type"),
                "decision_score": decision.get("decision_score"),
                "analysis_log_path": str(analysis_log_path),
                "strategy_log_path": str(strategy_log_path),
            },
            ensure_ascii=False,
        )
    )
    return analysis_log_path, strategy_log_path, snapshot, decision


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    symbols = [sanitize_symbol(item) for item in args.symbols.split(",") if item.strip()]
    if not symbols:
        print("[FAIL] No symbols were provided.")
        return 1

    config = KisConfig.from_env()
    client = KisApiClient(config)
    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "analysis_logs",
            archive_root=ROOT_DIR / "archives" / "analysis_logs",
        )
    )
    strategy_logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "structured_logs",
            archive_root=ROOT_DIR / "archives" / "structured_logs",
        )
    )

    while True:
        for symbol in symbols:
            try:
                collect_symbol_snapshot(
                    client,
                    logger,
                    strategy_logger,
                    symbol=symbol,
                    history_days=args.history_days,
                )
            except Exception as exc:  # pragma: no cover - CLI error path
                print(f"[FAIL] {symbol} analysis collection failed: {exc}")

        if args.once:
            break
        time.sleep(max(args.interval_sec, 1))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
