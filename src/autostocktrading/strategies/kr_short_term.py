"""Short-term entry strategy for Korean stocks."""

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


def evaluate_short_term_candidate(snapshot: dict[str, Any]) -> dict[str, Any]:
    rsi = _metric(snapshot, "rsi_14")
    volume_ratio = _metric(snapshot, "volume_ratio_20")
    price_vs_sma20 = _metric(snapshot, "price_vs_sma_20_pct")
    range_position = _metric(snapshot, "range_position_20d_pct")
    day_change = _metric(snapshot, "day_change_pct")
    five_day = _metric(snapshot, "daily_return_5d_pct")

    breakout_blockers: list[str] = []
    if not snapshot.get("above_sma_20"):
        breakout_blockers.append("below_sma_20")
    if volume_ratio is None or volume_ratio < 1.1:
        breakout_blockers.append("volume_too_low")
    if rsi is None or not (48 <= rsi <= 68):
        breakout_blockers.append("rsi_not_in_short_term_range")
    if range_position is None or range_position < 55:
        breakout_blockers.append("range_position_too_low")
    if day_change is None or day_change < 0:
        breakout_blockers.append("daily_momentum_negative")

    pullback_blockers: list[str] = []
    if not snapshot.get("above_sma_20"):
        pullback_blockers.append("below_sma_20")
    if price_vs_sma20 is None or not (0 <= price_vs_sma20 <= 3.0):
        pullback_blockers.append("price_vs_sma20_not_in_range")
    if rsi is None or not (42 <= rsi <= 60):
        pullback_blockers.append("rsi_not_in_pullback_range")
    if five_day is None or five_day <= 0:
        pullback_blockers.append("five_day_momentum_not_positive")

    candidate_type = None
    if not breakout_blockers:
        candidate_type = "short_breakout"
    elif not pullback_blockers:
        candidate_type = "short_pullback"

    return {
        "strategy_name": "kr_short_term_v1",
        "symbol": snapshot.get("symbol"),
        "name": snapshot.get("name"),
        "entry_candidate": candidate_type is not None,
        "candidate_type": candidate_type,
        "breakout_blockers": breakout_blockers,
        "pullback_blockers": pullback_blockers,
        "rsi_14": rsi,
        "volume_ratio_20": volume_ratio,
        "price_vs_sma_20_pct": price_vs_sma20,
        "range_position_20d_pct": range_position,
        "day_change_pct": day_change,
        "daily_return_5d_pct": five_day,
    }
