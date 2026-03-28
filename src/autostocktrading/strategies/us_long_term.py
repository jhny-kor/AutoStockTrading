"""Long-term strategy for US stocks under KIS overseas trading."""

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


def evaluate_us_long_term_candidate(snapshot: dict[str, Any]) -> dict[str, Any]:
    per = _metric(snapshot, "per")
    pbr = _metric(snapshot, "pbr")
    day_change = _metric(snapshot, "day_change_pct")
    distance_52h = _metric(snapshot, "distance_from_52w_high_pct")
    distance_52l = _metric(snapshot, "distance_from_52w_low_pct")

    blockers: list[str] = []
    if snapshot.get("orderable") == "매매 불가":
        blockers.append("not_orderable")
    if per is not None and per > 45:
        blockers.append("per_too_high")
    if pbr is not None and pbr > 15:
        blockers.append("pbr_too_high")
    if day_change is not None and day_change <= -6:
        blockers.append("day_change_too_negative")
    if distance_52h is not None and distance_52h > -3:
        blockers.append("too_close_to_52w_high")
    if distance_52l is not None and distance_52l < 10:
        blockers.append("too_close_to_52w_low")

    candidate = not blockers
    return {
        "strategy_name": "us_long_term_v1",
        "symbol": snapshot.get("symbol"),
        "name": snapshot.get("name"),
        "entry_candidate": candidate,
        "candidate_type": "us_long_term_value_growth" if candidate else None,
        "blockers": blockers,
        "per": per,
        "pbr": pbr,
        "day_change_pct": day_change,
        "distance_from_52w_high_pct": distance_52h,
        "distance_from_52w_low_pct": distance_52l,
    }
