"""US stock watchlists for KIS overseas trading."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsWatchlistEntry:
    symbol: str
    name: str
    exchange_quote: str
    exchange_order: str
    currency: str
    theme: str
    long_term_reason: str


US_LONG_TERM_WATCHLIST: tuple[UsWatchlistEntry, ...] = (
    UsWatchlistEntry(
        symbol="AAPL",
        name="Apple",
        exchange_quote="NAS",
        exchange_order="NASD",
        currency="USD",
        theme="소비자기기·플랫폼",
        long_term_reason="현금창출력과 생태계 잠금효과, 자사주 매입과 서비스 확장",
    ),
    UsWatchlistEntry(
        symbol="TSLA",
        name="Tesla",
        exchange_quote="NAS",
        exchange_order="NASD",
        currency="USD",
        theme="전기차·에너지·자율주행",
        long_term_reason="전기차 외 에너지 저장과 소프트웨어 옵션까지 포함한 성장성",
    ),
)

US_SHORT_TERM_WATCHLIST: tuple[UsWatchlistEntry, ...] = US_LONG_TERM_WATCHLIST


def get_us_long_term_entries() -> list[UsWatchlistEntry]:
    return list(US_LONG_TERM_WATCHLIST)


def get_us_short_term_entries() -> list[UsWatchlistEntry]:
    return list(US_SHORT_TERM_WATCHLIST)
