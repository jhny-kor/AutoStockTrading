"""US stock analysis snapshot builder using KIS overseas quote/detail responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from autostocktrading.config.us_strategy_watchlists import UsWatchlistEntry


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
        compact[key] = value
    return compact


def build_us_stock_snapshot(
    *,
    entry: UsWatchlistEntry,
    quote_response: dict[str, Any],
    detail_response: dict[str, Any],
    collected_at: datetime | None = None,
) -> dict[str, Any]:
    current_time = collected_at or datetime.now()
    quote = quote_response.get("output") or {}
    detail = detail_response.get("output") or {}

    current_price = _to_float(quote.get("last")) or _to_float(detail.get("last"))
    previous_close = _to_float(quote.get("base")) or _to_float(detail.get("base"))
    open_price = _to_float(detail.get("open"))
    high_price = _to_float(detail.get("high"))
    low_price = _to_float(detail.get("low"))
    week52_high = _to_float(detail.get("h52p"))
    week52_low = _to_float(detail.get("l52p"))

    def pct(current: float | None, base: float | None) -> float | None:
        if current is None or base in (None, 0):
            return None
        return (current - base) / base * 100

    return _compact(
        {
            "collected_at": current_time.isoformat(timespec="seconds"),
            "symbol": entry.symbol,
            "name": entry.name,
            "market": "US",
            "source": "kis_overseas",
            "exchange_quote": entry.exchange_quote,
            "exchange_order": entry.exchange_order,
            "currency": entry.currency,
            "theme": entry.theme,
            "long_term_reason": entry.long_term_reason,
            "current_price": current_price,
            "previous_close": previous_close,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "day_change_pct": _to_float(quote.get("rate")) or _to_float(detail.get("t_xrat")),
            "current_vs_previous_close_pct": pct(current_price, previous_close),
            "current_vs_open_pct": pct(current_price, open_price),
            "per": _to_float(detail.get("perx")),
            "pbr": _to_float(detail.get("pbrx")),
            "eps": _to_float(detail.get("epsx")),
            "bps": _to_float(detail.get("bpsx")),
            "volume": _to_float(quote.get("tvol")) or _to_float(detail.get("tvol")),
            "trade_amount": _to_float(quote.get("tamt")) or _to_float(detail.get("tamt")),
            "week52_high": week52_high,
            "week52_low": week52_low,
            "distance_from_52w_high_pct": pct(current_price, week52_high),
            "distance_from_52w_low_pct": pct(current_price, week52_low),
            "orderable": detail.get("e_ordyn") or quote.get("ordy"),
            "tick_size": _to_float(detail.get("e_hogau")),
        }
    )
