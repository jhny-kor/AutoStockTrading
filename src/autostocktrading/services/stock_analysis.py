"""Stock analysis snapshot builder for Korean equities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from statistics import mean
from typing import Any

from autostocktrading.config import get_watchlist_entry


def _to_int(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        return int(str(value).replace(",", ""))
    except ValueError:
        try:
            return int(float(str(value).replace(",", "")))
        except ValueError:
            return None


def _to_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _compact(record: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in record.items():
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        compact[key] = value
    return compact


def calc_sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return mean(values[-period:])


def calc_return_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous * 100


def calc_avg_abs_change_pct(closes: list[float], lookback: int) -> float | None:
    if len(closes) < 2:
        return None
    recent = closes[-(lookback + 1):] if len(closes) >= lookback + 1 else closes
    changes: list[float] = []
    for prev, curr in zip(recent, recent[1:]):
        if prev == 0:
            continue
        changes.append(abs((curr - prev) / prev) * 100)
    return mean(changes) if changes else None


def calc_rsi(closes: list[float], period: int) -> float | None:
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    window = closes[-(period + 1):]
    for prev, curr in zip(window, window[1:]):
        diff = curr - prev
        if diff >= 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))
    avg_gain = mean(gains)
    avg_loss = mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_volume_ratio(volumes: list[int], lookback: int) -> float | None:
    if len(volumes) < 2:
        return None
    current_volume = volumes[-1]
    previous = volumes[-(lookback + 1):-1] if len(volumes) >= lookback + 1 else volumes[:-1]
    if not previous:
        return None
    avg_volume = mean(previous)
    if avg_volume <= 0:
        return None
    return current_volume / avg_volume


def calc_range_stats(highs: list[float], lows: list[float], close: float, lookback: int) -> dict[str, float | None]:
    recent_highs = highs[-lookback:] if len(highs) >= lookback else highs
    recent_lows = lows[-lookback:] if len(lows) >= lookback else lows
    if not recent_highs or not recent_lows:
        return {
            "recent_high": None,
            "recent_low": None,
            "range_position_pct": None,
            "distance_from_recent_high_pct": None,
            "distance_from_recent_low_pct": None,
        }
    recent_high = max(recent_highs)
    recent_low = min(recent_lows)
    span = recent_high - recent_low
    range_position_pct = None if span <= 0 else (close - recent_low) / span * 100
    return {
        "recent_high": recent_high,
        "recent_low": recent_low,
        "range_position_pct": range_position_pct,
        "distance_from_recent_high_pct": calc_return_pct(close, recent_high),
        "distance_from_recent_low_pct": calc_return_pct(close, recent_low),
    }


@dataclass(frozen=True)
class DailyBar:
    trade_date: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int


def parse_daily_bars(response: dict[str, Any]) -> list[DailyBar]:
    raw_rows = response.get("output2") or response.get("output") or []
    bars: list[DailyBar] = []
    for row in raw_rows:
        trade_date = row.get("stck_bsop_date")
        open_price = _to_float(row.get("stck_oprc"))
        high_price = _to_float(row.get("stck_hgpr"))
        low_price = _to_float(row.get("stck_lwpr"))
        close_price = _to_float(row.get("stck_clpr"))
        volume = _to_int(row.get("acml_vol"))
        if not trade_date or None in (open_price, high_price, low_price, close_price, volume):
            continue
        bars.append(
            DailyBar(
                trade_date=str(trade_date),
                open_price=float(open_price),
                high_price=float(high_price),
                low_price=float(low_price),
                close_price=float(close_price),
                volume=int(volume),
            )
        )
    bars.sort(key=lambda bar: bar.trade_date)
    return bars


def build_stock_analysis_snapshot(
    *,
    symbol: str,
    quote_response: dict[str, Any],
    daily_bars: list[DailyBar],
    collected_at: datetime | None = None,
) -> dict[str, Any]:
    current_time = collected_at or datetime.now()
    quote = quote_response.get("output") or {}
    watchlist_entry = get_watchlist_entry(symbol)
    name = (
        quote.get("hts_kor_isnm")
        or quote.get("prdt_name")
        or (watchlist_entry.name if watchlist_entry else None)
        or symbol
    )

    current_price = _to_float(quote.get("stck_prpr"))
    open_price = _to_float(quote.get("stck_oprc"))
    high_price = _to_float(quote.get("stck_hgpr"))
    low_price = _to_float(quote.get("stck_lwpr"))
    accumulated_volume = _to_int(quote.get("acml_vol"))
    previous_close = _to_float(quote.get("stck_sdpr")) or (
        daily_bars[-2].close_price if len(daily_bars) >= 2 else None
    )

    closes = [bar.close_price for bar in daily_bars]
    highs = [bar.high_price for bar in daily_bars]
    lows = [bar.low_price for bar in daily_bars]
    volumes = [bar.volume for bar in daily_bars]
    last_close = closes[-1] if closes else current_price

    sma_5 = calc_sma(closes, 5)
    sma_10 = calc_sma(closes, 10)
    sma_20 = calc_sma(closes, 20)
    sma_60 = calc_sma(closes, 60)
    rsi_14 = calc_rsi(closes, 14)
    volume_ratio_5 = calc_volume_ratio(volumes, 5)
    volume_ratio_20 = calc_volume_ratio(volumes, 20)
    avg_abs_change_5 = calc_avg_abs_change_pct(closes, 5)
    avg_abs_change_20 = calc_avg_abs_change_pct(closes, 20)
    range_stats_20 = calc_range_stats(highs, lows, last_close or 0.0, 20)

    recent_close = closes[-1] if closes else None
    previous_day_close = closes[-2] if len(closes) >= 2 else None

    current_reference_price = current_price or recent_close

    return _compact(
        {
            "collected_at": current_time.isoformat(timespec="seconds"),
            "collected_at_local": current_time.astimezone().isoformat(timespec="seconds"),
            "symbol": symbol,
            "name": name,
            "theme": watchlist_entry.theme if watchlist_entry else None,
            "long_term_reason": watchlist_entry.long_term_reason if watchlist_entry else None,
            "market": "KRX",
            "source": "kis",
            "current_price": current_price,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "previous_close": previous_close,
            "accumulated_volume": accumulated_volume,
            "day_change_pct": _to_float(quote.get("prdy_ctrt")),
            "day_range_pct": calc_return_pct(high_price, low_price),
            "open_gap_pct": calc_return_pct(open_price, previous_close),
            "current_vs_open_pct": calc_return_pct(current_reference_price, open_price),
            "current_vs_previous_close_pct": calc_return_pct(current_reference_price, previous_close),
            "per": _to_float(quote.get("per")),
            "pbr": _to_float(quote.get("pbr")),
            "eps": _to_float(quote.get("eps")),
            "bps": _to_float(quote.get("bps")),
            "market_cap": _to_float(quote.get("hts_avls")),
            "w52_high": _to_float(quote.get("w52_hgpr")),
            "w52_low": _to_float(quote.get("w52_lwpr")),
            "distance_from_52w_high_pct": calc_return_pct(current_reference_price, _to_float(quote.get("w52_hgpr"))),
            "distance_from_52w_low_pct": calc_return_pct(current_reference_price, _to_float(quote.get("w52_lwpr"))),
            "daily_bar_count": len(daily_bars),
            "latest_daily_close": recent_close,
            "daily_return_1d_pct": calc_return_pct(recent_close, previous_day_close),
            "daily_return_5d_pct": calc_return_pct(recent_close, closes[-6] if len(closes) >= 6 else None),
            "daily_return_20d_pct": calc_return_pct(recent_close, closes[-21] if len(closes) >= 21 else None),
            "sma_5": sma_5,
            "sma_10": sma_10,
            "sma_20": sma_20,
            "sma_60": sma_60,
            "price_vs_sma_5_pct": calc_return_pct(current_reference_price, sma_5),
            "price_vs_sma_20_pct": calc_return_pct(current_reference_price, sma_20),
            "price_vs_sma_60_pct": calc_return_pct(current_reference_price, sma_60),
            "sma_5_vs_sma_20_pct": calc_return_pct(sma_5, sma_20),
            "sma_20_vs_sma_60_pct": calc_return_pct(sma_20, sma_60),
            "above_sma_20": (
                current_reference_price is not None and sma_20 is not None and current_reference_price > sma_20
            ),
            "above_sma_60": (
                current_reference_price is not None and sma_60 is not None and current_reference_price > sma_60
            ),
            "sma_20_above_sma_60": sma_20 is not None and sma_60 is not None and sma_20 > sma_60,
            "volume_ratio_5": volume_ratio_5,
            "volume_ratio_20": volume_ratio_20,
            "avg_abs_change_5_pct": avg_abs_change_5,
            "avg_abs_change_20_pct": avg_abs_change_20,
            "rsi_14": rsi_14,
            "recent_high_20d": range_stats_20["recent_high"],
            "recent_low_20d": range_stats_20["recent_low"],
            "range_position_20d_pct": range_stats_20["range_position_pct"],
            "distance_from_recent_high_20d_pct": range_stats_20["distance_from_recent_high_pct"],
            "distance_from_recent_low_20d_pct": range_stats_20["distance_from_recent_low_pct"],
            "near_20d_high": (
                range_stats_20["range_position_pct"] is not None
                and range_stats_20["range_position_pct"] >= 85
            ),
            "volume_active": volume_ratio_20 is not None and volume_ratio_20 >= 1.2,
            "breakout_watch": (
                current_reference_price is not None
                and sma_20 is not None
                and current_reference_price > sma_20
                and volume_ratio_20 is not None
                and volume_ratio_20 >= 1.2
                and range_stats_20["range_position_pct"] is not None
                and range_stats_20["range_position_pct"] >= 85
            ),
            "pullback_watch": (
                current_reference_price is not None
                and sma_20 is not None
                and current_reference_price >= sma_20
                and rsi_14 is not None
                and 45 <= rsi_14 <= 60
            ),
        }
    )
