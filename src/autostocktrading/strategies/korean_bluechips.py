"""Buy-candidate rules for Samsung Electronics and SK hynix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateRuleSet:
    pullback_min_volume_ratio: float = 0.55
    breakout_min_volume_ratio: float = 1.20
    pullback_min_rsi: float = 42.0
    pullback_max_rsi: float = 60.0
    breakout_min_rsi: float = 50.0
    breakout_max_rsi: float = 75.0
    pullback_min_range_position: float = 35.0
    pullback_max_range_position: float = 80.0
    breakout_min_range_position: float = 80.0
    pullback_max_price_vs_sma20: float = 4.0
    hard_max_negative_day_change: float = -4.0
    hard_max_day_range_pct: float = 10.0


SYMBOL_RULES = {
    "005930": CandidateRuleSet(),
    "000660": CandidateRuleSet(
        pullback_min_volume_ratio=0.60,
        breakout_min_volume_ratio=1.30,
        hard_max_day_range_pct=12.0,
    ),
}


def _metric(snapshot: dict[str, Any], key: str) -> float | None:
    value = snapshot.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_buy_candidate(snapshot: dict[str, Any]) -> dict[str, Any]:
    symbol = str(snapshot.get("symbol", ""))
    rules = SYMBOL_RULES.get(symbol, CandidateRuleSet())

    hard_blockers: list[str] = []
    if not snapshot.get("above_sma_20"):
        hard_blockers.append("below_sma_20")
    if not snapshot.get("above_sma_60"):
        hard_blockers.append("below_sma_60")
    if not snapshot.get("sma_20_above_sma_60"):
        hard_blockers.append("sma20_not_above_sma60")

    day_change_pct = _metric(snapshot, "day_change_pct")
    if day_change_pct is not None and day_change_pct <= rules.hard_max_negative_day_change:
        hard_blockers.append("day_change_too_negative")

    day_range_pct = _metric(snapshot, "day_range_pct")
    if day_range_pct is not None and day_range_pct >= rules.hard_max_day_range_pct:
        hard_blockers.append("intraday_range_too_large")

    rsi_14 = _metric(snapshot, "rsi_14")
    volume_ratio_20 = _metric(snapshot, "volume_ratio_20")
    range_position_20d_pct = _metric(snapshot, "range_position_20d_pct")
    price_vs_sma_20_pct = _metric(snapshot, "price_vs_sma_20_pct")
    current_vs_previous_close_pct = _metric(snapshot, "current_vs_previous_close_pct")

    breakout_blockers: list[str] = []
    if volume_ratio_20 is None or volume_ratio_20 < rules.breakout_min_volume_ratio:
        breakout_blockers.append("breakout_volume_too_low")
    if range_position_20d_pct is None or range_position_20d_pct < rules.breakout_min_range_position:
        breakout_blockers.append("not_near_20d_high")
    if rsi_14 is None or not (rules.breakout_min_rsi <= rsi_14 <= rules.breakout_max_rsi):
        breakout_blockers.append("breakout_rsi_not_in_range")
    if price_vs_sma_20_pct is None or price_vs_sma_20_pct < 0:
        breakout_blockers.append("price_below_sma20")
    if current_vs_previous_close_pct is None or current_vs_previous_close_pct < 0:
        breakout_blockers.append("daily_momentum_not_positive")

    pullback_blockers: list[str] = []
    if volume_ratio_20 is None or volume_ratio_20 < rules.pullback_min_volume_ratio:
        pullback_blockers.append("pullback_volume_too_low")
    if rsi_14 is None or not (rules.pullback_min_rsi <= rsi_14 <= rules.pullback_max_rsi):
        pullback_blockers.append("pullback_rsi_not_in_range")
    if range_position_20d_pct is None or not (
        rules.pullback_min_range_position <= range_position_20d_pct <= rules.pullback_max_range_position
    ):
        pullback_blockers.append("pullback_range_position_not_in_range")
    if price_vs_sma_20_pct is None or not (0 <= price_vs_sma_20_pct <= rules.pullback_max_price_vs_sma20):
        pullback_blockers.append("pullback_price_vs_sma20_not_in_range")
    if current_vs_previous_close_pct is not None and current_vs_previous_close_pct <= -2.5:
        pullback_blockers.append("pullback_daily_drop_too_large")

    breakout_ready = not hard_blockers and not breakout_blockers
    pullback_ready = not hard_blockers and not pullback_blockers

    candidate_type: str | None = None
    if breakout_ready:
        candidate_type = "breakout"
    elif pullback_ready:
        candidate_type = "pullback"

    score_components = [
        snapshot.get("above_sma_20") is True,
        snapshot.get("above_sma_60") is True,
        snapshot.get("sma_20_above_sma_60") is True,
        volume_ratio_20 is not None and volume_ratio_20 >= rules.pullback_min_volume_ratio,
        rsi_14 is not None and rules.pullback_min_rsi <= rsi_14 <= rules.breakout_max_rsi,
        range_position_20d_pct is not None and range_position_20d_pct >= rules.pullback_min_range_position,
    ]
    score = round(sum(1 for item in score_components if item) / len(score_components) * 100, 2)

    return {
        "strategy_name": "korean_bluechips_v1",
        "symbol": symbol,
        "name": snapshot.get("name"),
        "buy_candidate": candidate_type is not None,
        "candidate_type": candidate_type,
        "decision_score": score,
        "hard_blockers": hard_blockers,
        "breakout_ready": breakout_ready,
        "breakout_blockers": breakout_blockers,
        "pullback_ready": pullback_ready,
        "pullback_blockers": pullback_blockers,
        "day_change_pct": day_change_pct,
        "day_range_pct": day_range_pct,
        "rsi_14": rsi_14,
        "volume_ratio_20": volume_ratio_20,
        "range_position_20d_pct": range_position_20d_pct,
        "price_vs_sma_20_pct": price_vs_sma_20_pct,
        "above_sma_20": snapshot.get("above_sma_20"),
        "above_sma_60": snapshot.get("above_sma_60"),
        "sma_20_above_sma_60": snapshot.get("sma_20_above_sma_60"),
        "breakout_watch": snapshot.get("breakout_watch"),
        "pullback_watch": snapshot.get("pullback_watch"),
    }
