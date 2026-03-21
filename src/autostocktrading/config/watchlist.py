"""Shared stock watchlist definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WatchlistEntry:
    symbol: str
    name: str
    theme: str
    long_term_reason: str


DEFAULT_ANALYSIS_WATCHLIST: tuple[WatchlistEntry, ...] = (
    WatchlistEntry(
        symbol="005930",
        name="삼성전자",
        theme="메모리·파운드리·소비자전자",
        long_term_reason="메모리 사이클 회복과 대규모 현금창출력, 반도체 밸류체인 핵심 지위",
    ),
    WatchlistEntry(
        symbol="000660",
        name="SK하이닉스",
        theme="HBM·DRAM",
        long_term_reason="HBM 중심 고부가 메모리 수혜와 AI 서버 투자 확장의 직접 수혜",
    ),
    WatchlistEntry(
        symbol="105560",
        name="KB금융",
        theme="은행·주주환원",
        long_term_reason="안정적 현금흐름, 자본정책과 주주환원, 금리 사이클 완충력",
    ),
    WatchlistEntry(
        symbol="207940",
        name="삼성바이오로직스",
        theme="바이오 CDMO",
        long_term_reason="대형 생산능력과 장기 계약 기반 성장, 바이오 위탁생산 구조적 확대",
    ),
    WatchlistEntry(
        symbol="267260",
        name="HD현대일렉트릭",
        theme="전력기기·전력인프라",
        long_term_reason="전력망 투자와 AI 전력 수요 증가에 따른 고수익 수주 구조",
    ),
    WatchlistEntry(
        symbol="012450",
        name="한화에어로스페이스",
        theme="방산·항공엔진",
        long_term_reason="글로벌 방산 수요와 수주잔고 확대, 우주·엔진 사업 옵션",
    ),
    WatchlistEntry(
        symbol="017670",
        name="SK텔레콤",
        theme="통신·배당·AI 인프라",
        long_term_reason="안정적 현금흐름과 배당, AI 인프라 및 데이터센터 확장 옵션",
    ),
)


def get_default_symbols() -> list[str]:
    return [entry.symbol for entry in DEFAULT_ANALYSIS_WATCHLIST]


def get_watchlist_entry(symbol: str) -> WatchlistEntry | None:
    for entry in DEFAULT_ANALYSIS_WATCHLIST:
        if entry.symbol == symbol:
            return entry
    return None
