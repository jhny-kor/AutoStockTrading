"""Run long/short US strategy evaluations from shared overseas analysis logs."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Callable

from autostocktrading.config.us_strategy_watchlists import UsWatchlistEntry
from autostocktrading.logs import DailyJsonlLogger, LogDirectoryManager
from autostocktrading.utils.state import load_json_state, save_json_state


ROOT_DIR = Path(__file__).resolve().parents[3]


def find_latest_us_analysis_date(base_dir: Path | None = None) -> date | None:
    target = base_dir or (ROOT_DIR / "us_analysis_logs")
    if not target.exists():
        return None
    dates: list[date] = []
    for child in target.iterdir():
        if not child.is_dir():
            continue
        try:
            dates.append(date.fromisoformat(child.name))
        except ValueError:
            continue
    return max(dates) if dates else None


def read_latest_payload(path: Path) -> dict | None:
    if not path.exists():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    import json

    return json.loads(lines[-1]).get("payload")


def run_us_signal_batch(
    *,
    strategy_source: str,
    strategy_category: str,
    entries: list[UsWatchlistEntry],
    evaluate_fn: Callable[[dict], dict],
    state_path: Path,
    target_date: date | None = None,
) -> int:
    latest_date = target_date or find_latest_us_analysis_date(ROOT_DIR / "us_analysis_logs")
    if latest_date is None:
        print("[FAIL] No shared US analysis logs are available yet.")
        return 1

    logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "us_structured_logs",
            archive_root=ROOT_DIR / "archives" / "us_structured_logs",
        )
    )
    state = load_json_state(state_path, default={"last_seen": {}})
    last_seen = state.setdefault("last_seen", {})

    for entry in entries:
        analysis_path = (
            ROOT_DIR
            / "us_analysis_logs"
            / latest_date.isoformat()
            / "kis_us_analysis"
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
