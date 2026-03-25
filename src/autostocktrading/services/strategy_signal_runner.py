"""Run separate long-term and short-term signal evaluations from shared analysis logs."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Callable

from autostocktrading.config.watchlist import WatchlistEntry
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager
from autostocktrading.services.analysis_report import find_latest_analysis_date, read_latest_payload
from autostocktrading.utils.state import load_json_state, save_json_state


ROOT_DIR = Path(__file__).resolve().parents[3]


def run_signal_batch(
    *,
    strategy_source: str,
    strategy_category: str,
    entries: list[WatchlistEntry],
    evaluate_fn: Callable[[dict], dict],
    state_path: Path,
    target_date: date | None = None,
) -> int:
    latest_date = target_date or find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    if latest_date is None:
        print("[FAIL] No shared analysis logs are available yet.")
        return 1

    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "structured_logs",
            archive_root=ROOT_DIR / "archives" / "structured_logs",
        )
    )
    state = load_json_state(state_path, default={"last_seen": {}})
    last_seen = state.setdefault("last_seen", {})

    for entry in entries:
        analysis_path = (
            ROOT_DIR
            / "analysis_logs"
            / latest_date.isoformat()
            / "kis_analysis"
            / entry.symbol
            / "stocks"
            / "snapshot.jsonl"
        )
        raw_payload = read_latest_payload(analysis_path)
        if not raw_payload:
            continue

        collected_at = str(raw_payload.get("collected_at"))
        if last_seen.get(entry.symbol) == collected_at:
            continue

        decision = evaluate_fn(raw_payload)
        logger.append_event(
            source=strategy_source,
            symbol=entry.symbol,
            category=strategy_category,
            event_type="entry_candidate",
            payload=decision,
            target_date=latest_date,
        )
        last_seen[entry.symbol] = collected_at
        print(json.dumps(decision, ensure_ascii=False))

    save_json_state(state_path, state)
    return 0
