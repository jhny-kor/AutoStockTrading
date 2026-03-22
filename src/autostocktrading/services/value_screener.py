"""Value + dividend + trend-recovery screener helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Iterable

from autostocktrading.config import WatchlistEntry, get_watchlist_entries_by_market, resolve_watchlist_entries


ROOT_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ScreenResult:
    symbol: str
    name: str
    market: str
    size_tier: str
    total_score: float
    value_score: float
    dividend_score: float
    trend_score: float
    per: float | None
    pbr: float | None
    price_vs_sma_20_pct: float | None
    rsi_14: float | None
    volume_ratio_20: float | None
    notes: str


def _read_latest_payload(path: Path) -> dict | None:
    if not path.exists():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return json.loads(lines[-1]).get("payload")


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _dividend_profile_score(profile: str) -> float:
    mapping = {
        "high": 1.0,
        "moderate": 0.7,
        "low": 0.3,
        "none": 0.0,
    }
    return mapping.get(profile, 0.3)


def _value_score(per: float | None, pbr: float | None) -> float:
    score = 0.0
    weight = 0.0
    if per is not None and per > 0:
        score += _clamp_score((18.0 - per) / 18.0) * 0.5
        weight += 0.5
    if pbr is not None and pbr > 0:
        score += _clamp_score((2.5 - pbr) / 2.5) * 0.5
        weight += 0.5
    return round((score / weight) * 100, 2) if weight else 0.0


def _trend_score(snapshot: dict) -> float:
    score = 0.0
    count = 0

    for key in ("above_sma_20", "above_sma_60", "sma_20_above_sma_60"):
        count += 1
        if snapshot.get(key) is True:
            score += 1.0

    rsi = snapshot.get("rsi_14")
    count += 1
    if rsi is not None and 35 <= float(rsi) <= 55:
        score += 1.0

    price_vs_sma20 = snapshot.get("price_vs_sma_20_pct")
    count += 1
    if price_vs_sma20 is not None and -1.0 <= float(price_vs_sma20) <= 5.0:
        score += 1.0

    volume_ratio = snapshot.get("volume_ratio_20")
    count += 1
    if volume_ratio is not None and float(volume_ratio) >= 0.7:
        score += 1.0

    return round((score / count) * 100, 2) if count else 0.0


def screen_watchlist(
    *,
    target_date: date,
    watchlists: list[str] | None = None,
    markets: list[str] | None = None,
) -> list[ScreenResult]:
    entries = resolve_watchlist_entries(watchlists)
    if markets:
        market_set = {item.upper() for item in markets}
        entries = [entry for entry in entries if entry.market.upper() in market_set]

    results: list[ScreenResult] = []
    date_str = target_date.isoformat()

    for entry in entries:
        analysis_path = ROOT_DIR / "analysis_logs" / date_str / "kis_analysis" / entry.symbol / "stocks" / "snapshot.jsonl"
        snapshot = _read_latest_payload(analysis_path)
        if not snapshot:
            continue

        per = snapshot.get("per")
        pbr = snapshot.get("pbr")
        value_score = _value_score(float(per) if per is not None else None, float(pbr) if pbr is not None else None)
        dividend_score = round(_dividend_profile_score(entry.dividend_profile) * 100, 2)
        trend_score = _trend_score(snapshot)
        total_score = round(value_score * 0.40 + dividend_score * 0.20 + trend_score * 0.40, 2)

        notes = []
        if value_score >= 60:
            notes.append("value_ok")
        if dividend_score >= 70:
            notes.append("dividend_ok")
        if trend_score >= 70:
            notes.append("trend_ok")

        results.append(
            ScreenResult(
                symbol=entry.symbol,
                name=entry.name,
                market=entry.market,
                size_tier=entry.size_tier,
                total_score=total_score,
                value_score=value_score,
                dividend_score=dividend_score,
                trend_score=trend_score,
                per=float(per) if per is not None else None,
                pbr=float(pbr) if pbr is not None else None,
                price_vs_sma_20_pct=float(snapshot["price_vs_sma_20_pct"]) if snapshot.get("price_vs_sma_20_pct") is not None else None,
                rsi_14=float(snapshot["rsi_14"]) if snapshot.get("rsi_14") is not None else None,
                volume_ratio_20=float(snapshot["volume_ratio_20"]) if snapshot.get("volume_ratio_20") is not None else None,
                notes=",".join(notes) if notes else "watch",
            )
        )

    results.sort(key=lambda item: (item.market, -item.total_score, item.name))
    return results


def build_screener_report(
    *,
    target_date: date,
    watchlists: list[str] | None = None,
) -> str:
    results = screen_watchlist(target_date=target_date, watchlists=watchlists)
    lines = [f"# 저PBR/저PER + 배당 + 추세회복 스크리너", "", f"- 기준일: {target_date.isoformat()}", ""]

    for market in ("KOSPI", "KOSDAQ"):
        market_results = [item for item in results if item.market == market][:3]
        lines.append(f"## {market} 상위 3")
        if not market_results:
            lines.append("- 결과 없음")
            lines.append("")
            continue
        for item in market_results:
            lines.append(
                f"- {item.name} ({item.symbol}) [{item.size_tier}] | total {item.total_score:.2f} | "
                f"value {item.value_score:.2f} | dividend {item.dividend_score:.2f} | trend {item.trend_score:.2f}"
            )
            lines.append(
                f"  PER {item.per}, PBR {item.pbr}, RSI {item.rsi_14}, "
                f"20일선 대비 {item.price_vs_sma_20_pct}%, 거래량배수 {item.volume_ratio_20}, notes={item.notes}"
            )
        lines.append("")

    return "\n".join(lines).strip()
