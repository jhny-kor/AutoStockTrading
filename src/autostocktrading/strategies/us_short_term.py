"""Short-term strategy for US stocks under KIS overseas trading."""

from __future__ import annotations

from typing import Any


def _metric(snapshot: dict[str, Any], key: str) -> float | None:
    value = snapshot.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_us_short_term_candidate(snapshot: dict[str, Any]) -> dict[str, Any]:
    day_change = _metric(snapshot, "day_change_pct")
    current_vs_open = _metric(snapshot, "current_vs_open_pct")
    distance_52h = _metric(snapshot, "distance_from_52w_high_pct")
    volume = _metric(snapshot, "volume")

    breakout_blockers: list[str] = []
    if snapshot.get("orderable") == "매매 불가":
        breakout_blockers.append("not_orderable")
    if day_change is None or day_change < 0.5:
        breakout_blockers.append("day_change_too_low")
    if current_vs_open is None or current_vs_open < 0:
        breakout_blockers.append("below_open")
    if distance_52h is not None and distance_52h > -1:
        breakout_blockers.append("too_close_to_52w_high")
    if volume is None or volume <= 0:
        breakout_blockers.append("volume_missing")

    candidate = not breakout_blockers
    return {
        "strategy_name": "us_short_term_v1",
        "symbol": snapshot.get("symbol"),
        "name": snapshot.get("name"),
        "entry_candidate": candidate,
        "candidate_type": "us_intraday_momentum" if candidate else None,
        "breakout_blockers": breakout_blockers,
        "day_change_pct": day_change,
        "current_vs_open_pct": current_vs_open,
        "distance_from_52w_high_pct": distance_52h,
        "volume": volume,
    }
