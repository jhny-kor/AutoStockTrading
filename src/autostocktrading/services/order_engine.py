"""Shared order-engine helpers for Korean long-term and short-term traders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
from typing import Any, Callable

from autostocktrading.brokers.kis import KisApiClient, KisConfig
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager
from autostocktrading.services.analysis_report import find_latest_analysis_date, read_latest_payload
from autostocktrading.utils.state import load_json_state, save_json_state


ROOT_DIR = Path(__file__).resolve().parents[3]


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class OrderEngineConfig:
    dry_run: bool
    allow_live_orders: bool
    order_budget_krw: int
    max_orders_per_day: int
    max_open_candidates: int
    order_style: str


def build_order_engine_config(prefix: str) -> OrderEngineConfig:
    import os

    return OrderEngineConfig(
        dry_run=_parse_bool(os.getenv(f"{prefix}_DRY_RUN"), default=True),
        allow_live_orders=_parse_bool(os.getenv("KIS_ALLOW_LIVE_ORDERS"), default=False),
        order_budget_krw=int(os.getenv(f"{prefix}_ORDER_BUDGET_KRW", "300000")),
        max_orders_per_day=int(os.getenv(f"{prefix}_MAX_ORDERS_PER_DAY", "2")),
        max_open_candidates=int(os.getenv(f"{prefix}_MAX_OPEN_CANDIDATES", "3")),
        order_style=os.getenv(f"{prefix}_ORDER_STYLE", "market").strip().lower(),
    )


def run_order_batch(
    *,
    strategy_source: str,
    strategy_category: str,
    state_path: Path,
    config_prefix: str,
    target_date: date | None = None,
) -> int:
    latest_date = target_date or find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    if latest_date is None:
        print("[FAIL] No analysis logs are available yet.")
        return 1

    engine_config = build_order_engine_config(config_prefix)
    kis_config = KisConfig.from_env()
    client = KisApiClient(kis_config)

    state = load_json_state(
        state_path,
        default={"ordered_receipts": {}, "today_count": {}, "last_seen": {}},
    )
    ordered_receipts = state.setdefault("ordered_receipts", {})
    today_count = state.setdefault("today_count", {})
    last_seen = state.setdefault("last_seen", {})
    today_key = latest_date.isoformat()
    today_count.setdefault(today_key, 0)

    trade_logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "trade_logs",
            archive_root=ROOT_DIR / "archives" / "trade_logs",
        )
    )

    strategy_dir = ROOT_DIR / "structured_logs" / today_key / strategy_source
    if not strategy_dir.exists():
        print(f"[FAIL] No strategy directory for {strategy_source} on {today_key}.")
        return 1

    ordered_this_run = 0
    for signal_path in sorted(strategy_dir.rglob("entry_candidate.jsonl")):
        symbol = signal_path.parts[-3]
        payload = read_latest_payload(signal_path)
        if not payload or not payload.get("entry_candidate"):
            continue

        signal_key = f"{today_key}:{strategy_source}:{symbol}:{payload.get('candidate_type')}"
        if ordered_receipts.get(signal_key):
            continue
        if today_count[today_key] >= engine_config.max_orders_per_day:
            break
        if ordered_this_run >= engine_config.max_open_candidates:
            break

        analysis_path = (
            ROOT_DIR
            / "analysis_logs"
            / today_key
            / "kis_analysis"
            / symbol
            / "stocks"
            / "snapshot.jsonl"
        )
        analysis_payload = read_latest_payload(analysis_path)
        if not analysis_payload:
            continue

        current_price = analysis_payload.get("current_price")
        if current_price is None:
            continue

        quantity = math.floor(engine_config.order_budget_krw / float(current_price))
        if quantity <= 0:
            continue

        order_payload = {
            "strategy_source": strategy_source,
            "symbol": symbol,
            "name": payload.get("name"),
            "candidate_type": payload.get("candidate_type"),
            "dry_run": engine_config.dry_run,
            "use_virtual": kis_config.use_virtual,
            "current_price": current_price,
            "quantity": quantity,
            "order_budget_krw": engine_config.order_budget_krw,
            "order_style": engine_config.order_style,
        }

        if engine_config.dry_run:
            order_payload["status"] = "simulated"
            print(json.dumps(order_payload, ensure_ascii=False))
        else:
            if not kis_config.allow_live_orders or kis_config.use_virtual:
                raise RuntimeError(
                    "Live order execution requires KIS_USE_VIRTUAL=false and KIS_ALLOW_LIVE_ORDERS=true."
                )
            order_division = "01" if engine_config.order_style == "market" else "00"
            response = client.place_cash_order(
                side="BUY",
                symbol=symbol,
                quantity=quantity,
                price=0 if order_division == "01" else int(current_price),
                order_division=order_division,
            )
            order_payload["status"] = "submitted"
            order_payload["response"] = response
            print(json.dumps(order_payload, ensure_ascii=False))

        trade_logger.append_event(
            source=strategy_source,
            symbol=symbol,
            category="orders",
            event_type="buy_entry",
            payload=order_payload,
            target_date=latest_date,
        )
        ordered_receipts[signal_key] = True
        today_count[today_key] += 1
        last_seen[symbol] = today_key
        ordered_this_run += 1

    save_json_state(state_path, state)
    return 0
