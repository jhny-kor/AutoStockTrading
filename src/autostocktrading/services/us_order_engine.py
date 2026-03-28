"""Shared US order-engine helpers using KIS overseas daytime orders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
from typing import Any

from autostocktrading.brokers.kis import KisConfig, KisOverseasClient, KisOverseasOrderRequest
from autostocktrading.config.us_strategy_watchlists import UsWatchlistEntry
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager
from autostocktrading.utils.state import load_json_state, save_json_state
from .us_strategy_signal_runner import find_latest_us_analysis_date, read_latest_payload


ROOT_DIR = Path(__file__).resolve().parents[3]


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class UsOrderEngineConfig:
    dry_run: bool
    allow_live_orders: bool
    order_budget_usd: float
    max_orders_per_day: int
    max_open_candidates: int
    order_style: str


def build_us_order_engine_config(prefix: str) -> UsOrderEngineConfig:
    import os

    return UsOrderEngineConfig(
        dry_run=_parse_bool(os.getenv(f"{prefix}_DRY_RUN"), default=True),
        allow_live_orders=_parse_bool(os.getenv("KIS_ALLOW_LIVE_ORDERS"), default=False),
        order_budget_usd=float(os.getenv(f"{prefix}_ORDER_BUDGET_USD", "500")),
        max_orders_per_day=int(os.getenv(f"{prefix}_MAX_ORDERS_PER_DAY", "1")),
        max_open_candidates=int(os.getenv(f"{prefix}_MAX_OPEN_CANDIDATES", "1")),
        order_style=os.getenv(f"{prefix}_ORDER_STYLE", "limit").strip().lower(),
    )


def run_us_order_batch(
    *,
    strategy_source: str,
    strategy_category: str,
    entries: list[UsWatchlistEntry],
    state_path: Path,
    config_prefix: str,
    target_date: date | None = None,
) -> int:
    latest_date = target_date or find_latest_us_analysis_date(ROOT_DIR / "us_analysis_logs")
    if latest_date is None:
        print("[FAIL] No US analysis logs are available yet.")
        return 1

    config = build_us_order_engine_config(config_prefix)
    kis_config = KisConfig.from_env()
    client = KisOverseasClient(kis_config)

    state = load_json_state(
        state_path,
        default={"ordered_receipts": {}, "today_count": {}, "last_seen": {}},
    )
    ordered_receipts = state.setdefault("ordered_receipts", {})
    today_count = state.setdefault("today_count", {})
    last_seen = state.setdefault("last_seen", {})
    today_key = latest_date.isoformat()
    today_count.setdefault(today_key, 0)

    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "us_trade_logs",
            archive_root=ROOT_DIR / "archives" / "us_trade_logs",
        )
    )
    token = client.get_access_token()
    ordered_this_run = 0

    for entry in entries:
        strategy_path = (
            ROOT_DIR
            / "us_structured_logs"
            / today_key
            / strategy_source
            / entry.symbol
            / strategy_category
            / "entry_candidate.jsonl"
        )
        payload = read_latest_payload(strategy_path)
        if not payload or not payload.get("entry_candidate"):
            continue

        signal_key = f"{today_key}:{strategy_source}:{entry.symbol}:{payload.get('candidate_type')}"
        if ordered_receipts.get(signal_key):
            continue
        if today_count[today_key] >= config.max_orders_per_day:
            break
        if ordered_this_run >= config.max_open_candidates:
            break

        analysis_path = (
            ROOT_DIR
            / "us_analysis_logs"
            / today_key
            / "kis_us_analysis"
            / entry.symbol
            / "stocks"
            / "snapshot.jsonl"
        )
        analysis_payload = read_latest_payload(analysis_path)
        if not analysis_payload:
            continue

        current_price = analysis_payload.get("current_price")
        if current_price is None:
            continue

        quantity = math.floor(config.order_budget_usd / float(current_price))
        if quantity <= 0:
            continue

        order_payload = {
            "strategy_source": strategy_source,
            "symbol": entry.symbol,
            "name": entry.name,
            "candidate_type": payload.get("candidate_type"),
            "dry_run": config.dry_run,
            "use_virtual": kis_config.use_virtual,
            "current_price": current_price,
            "quantity": quantity,
            "order_budget_usd": config.order_budget_usd,
            "order_style": config.order_style,
        }

        if config.dry_run:
            order_payload["status"] = "simulated"
            ordered_receipts[signal_key] = True
            today_count[today_key] += 1
            last_seen[entry.symbol] = today_key
            ordered_this_run += 1
            print(json.dumps(order_payload, ensure_ascii=False))
        else:
            if not config.allow_live_orders or kis_config.use_virtual:
                raise RuntimeError(
                    "US live order execution requires KIS_USE_VIRTUAL=false and KIS_ALLOW_LIVE_ORDERS=true."
                )
            request = KisOverseasOrderRequest(
                side="BUY",
                exchange_code=entry.exchange_order,
                symbol=entry.symbol,
                quantity=quantity,
                price=float(current_price),
                order_division="00" if config.order_style == "limit" else "01",
            )
            response = client.place_daytime_order(request, token=token)
            order_payload["status"] = "submitted" if str(response.get("rt_cd")) == "0" else "failed"
            order_payload["response"] = response
            print(json.dumps(order_payload, ensure_ascii=False))
            if str(response.get("rt_cd")) == "0":
                ordered_receipts[signal_key] = True
                today_count[today_key] += 1
                last_seen[entry.symbol] = today_key
                ordered_this_run += 1

        logger.append_event(
            source=strategy_source,
            symbol=entry.symbol,
            category="orders",
            event_type="buy_entry",
            payload=order_payload,
            target_date=latest_date,
        )

    save_json_state(state_path, state)
    return 0
