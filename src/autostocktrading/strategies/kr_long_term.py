"""Long-term entry strategy for Korean stocks."""

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


def evaluate_long_term_candidate(snapshot: dict[str, Any]) -> dict[str, Any]:
    per = _metric(snapshot, "per")
    pbr = _metric(snapshot, "pbr")
    rsi = _metric(snapshot, "rsi_14")
    volume_ratio = _metric(snapshot, "volume_ratio_20")
    price_vs_sma20 = _metric(snapshot, "price_vs_sma_20_pct")
    price_vs_sma60 = _metric(snapshot, "price_vs_sma_60_pct")
    day_change = _metric(snapshot, "day_change_pct")

    blockers: list[str] = []
    if not snapshot.get("above_sma_20"):
        blockers.append("below_sma_20")
    if not snapshot.get("sma_20_above_sma_60"):
        blockers.append("sma20_not_above_sma60")
    if rsi is None or not (40 <= rsi <= 60):
        blockers.append("rsi_not_in_long_term_range")
    if price_vs_sma20 is None or not (-1.0 <= price_vs_sma20 <= 4.0):
        blockers.append("price_vs_sma20_not_in_range")
    if day_change is not None and day_change <= -4.0:
        blockers.append("day_change_too_negative")

    valuation_notes: list[str] = []
    value_friendly = False
    if per is not None and per <= 20:
        valuation_notes.append("per_ok")
        value_friendly = True
    if pbr is not None and pbr <= 2.5:
        valuation_notes.append("pbr_ok")
        value_friendly = True
    if not value_friendly:
        blockers.append("value_not_cheap_enough")

    candidate = not blockers
    return {
        "strategy_name": "kr_long_term_v1",
        "symbol": snapshot.get("symbol"),
        "name": snapshot.get("name"),
        "entry_candidate": candidate,
        "candidate_type": "long_term_recovery" if candidate else None,
        "blockers": blockers,
        "valuation_notes": valuation_notes,
        "per": per,
        "pbr": pbr,
        "rsi_14": rsi,
        "volume_ratio_20": volume_ratio,
        "price_vs_sma_20_pct": price_vs_sma20,
        "price_vs_sma_60_pct": price_vs_sma60,
        "day_change_pct": day_change,
    }
