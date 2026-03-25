"""Separate Korean long-term and short-term strategy watchlists."""

from __future__ import annotations

from autostocktrading.config.watchlist import get_watchlist_entry


KR_LONG_TERM_SYMBOLS = [
    "005930",  # 삼성전자
    "105560",  # KB금융
    "017670",  # SK텔레콤
    "000810",  # 삼성화재
    "005380",  # 현대차
    "000270",  # 기아
    "207940",  # 삼성바이오로직스
    "267260",  # HD현대일렉트릭
    "012450",  # 한화에어로스페이스
    "000660",  # SK하이닉스
]

KR_SHORT_TERM_SYMBOLS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "010120",  # LS ELECTRIC
    "064350",  # 현대로템
    "272210",  # 한화시스템
    "047810",  # 한국항공우주
    "214150",  # 클래시스
    "058470",  # 리노공업
    "403870",  # HPSP
    "141080",  # 리가켐바이오
    "005290",  # 동진쎄미켐
    "036930",  # 주성엔지니어링
    "240810",  # 원익IPS
]


def get_long_term_entries():
    return [entry for symbol in KR_LONG_TERM_SYMBOLS if (entry := get_watchlist_entry(symbol))]


def get_short_term_entries():
    return [entry for symbol in KR_SHORT_TERM_SYMBOLS if (entry := get_watchlist_entry(symbol))]
