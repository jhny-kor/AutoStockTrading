"""Shared stock watchlist definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WatchlistEntry:
    symbol: str
    name: str
    market: str
    size_tier: str
    theme: str
    long_term_reason: str
    dividend_profile: str = "low"


LARGE_CAP_WATCHLIST: tuple[WatchlistEntry, ...] = (
    WatchlistEntry("005930", "삼성전자", "KOSPI", "large", "메모리·파운드리·소비자전자", "메모리 사이클 회복과 대규모 현금창출력, 반도체 밸류체인 핵심 지위", "moderate"),
    WatchlistEntry("000660", "SK하이닉스", "KOSPI", "large", "HBM·DRAM", "HBM 중심 고부가 메모리 수혜와 AI 서버 투자 확장의 직접 수혜", "low"),
    WatchlistEntry("105560", "KB금융", "KOSPI", "large", "은행·주주환원", "안정적 현금흐름, 자본정책과 주주환원, 금리 사이클 완충력", "high"),
    WatchlistEntry("207940", "삼성바이오로직스", "KOSPI", "large", "바이오 CDMO", "대형 생산능력과 장기 계약 기반 성장, 바이오 위탁생산 구조적 확대", "low"),
    WatchlistEntry("267260", "HD현대일렉트릭", "KOSPI", "large", "전력기기·전력인프라", "전력망 투자와 AI 전력 수요 증가에 따른 고수익 수주 구조", "low"),
    WatchlistEntry("012450", "한화에어로스페이스", "KOSPI", "large", "방산·항공엔진", "글로벌 방산 수요와 수주잔고 확대, 우주·엔진 사업 옵션", "low"),
    WatchlistEntry("017670", "SK텔레콤", "KOSPI", "large", "통신·배당·AI 인프라", "안정적 현금흐름과 배당, AI 인프라 및 데이터센터 확장 옵션", "high"),
    WatchlistEntry("005380", "현대차", "KOSPI", "large", "자동차·전동화", "전동화와 하이브리드 라인업 강화, 미국 생산거점 확대, 주주환원 강화", "high"),
    WatchlistEntry("000270", "기아", "KOSPI", "large", "자동차·수익성", "높은 수익성, EV와 하이브리드 밸런스, 안정적 현금흐름과 자사주 정책", "high"),
    WatchlistEntry("035420", "NAVER", "KOSPI", "large", "플랫폼·AI·커머스", "검색·커머스·콘텐츠·AI 서비스 결합과 국내 플랫폼 지배력", "low"),
    WatchlistEntry("000810", "삼성화재", "KOSPI", "large", "보험·주주환원", "안정적 이익 체력, 자본 여력, 주주환원 확대와 방어적 포트폴리오 역할", "high"),
)

MID_CAP_WATCHLIST: tuple[WatchlistEntry, ...] = (
    WatchlistEntry("010120", "LS ELECTRIC", "KOSPI", "mid", "전력·스마트그리드", "전력설비, 자동화, 송배전 인프라 확대 수혜", "moderate"),
    WatchlistEntry("064350", "현대로템", "KOSPI", "mid", "방산·철도", "K2 수출 확대와 철도·플랜트 사업 다변화", "low"),
    WatchlistEntry("272210", "한화시스템", "KOSPI", "mid", "방산전자·우주", "방산 전자장비와 위성·우주 투자 옵션", "low"),
    WatchlistEntry("047810", "한국항공우주", "KOSPI", "mid", "항공·방산", "국내 항공기 체계사업과 수출 확대 가능성", "low"),
    WatchlistEntry("196170", "알테오젠", "KOSDAQ", "mid", "바이오 플랫폼", "기술수출 및 플랫폼 가치가 큰 성장형 바이오", "low"),
    WatchlistEntry("214150", "클래시스", "KOSDAQ", "mid", "미용의료기기", "높은 마진과 해외 미용기기 성장성", "moderate"),
    WatchlistEntry("058470", "리노공업", "KOSDAQ", "mid", "반도체 테스트", "고수익 테스트 소켓 사업과 안정적 현금흐름", "moderate"),
    WatchlistEntry("403870", "HPSP", "KOSDAQ", "mid", "반도체 장비", "반도체 전공정 장비 성장성과 높은 수익성", "low"),
)

SMALL_CAP_WATCHLIST: tuple[WatchlistEntry, ...] = (
    WatchlistEntry("141080", "리가켐바이오", "KOSDAQ", "small", "ADC 바이오", "ADC 파이프라인과 기술 이전 가능성", "low"),
    WatchlistEntry("277810", "레인보우로보틱스", "KOSDAQ", "small", "로봇", "국내 로봇 대표 성장주로 장기 산업 성장성 보유", "low"),
    WatchlistEntry("005290", "동진쎄미켐", "KOSDAQ", "small", "반도체 소재", "포토레지스트 등 반도체 소재 국산화 수혜", "low"),
    WatchlistEntry("036930", "주성엔지니어링", "KOSDAQ", "small", "반도체·디스플레이 장비", "증착장비 사이클 회복 시 수혜", "low"),
    WatchlistEntry("240810", "원익IPS", "KOSDAQ", "small", "반도체 장비", "메모리·파운드리 설비투자 회복 수혜", "low"),
    WatchlistEntry("214450", "파마리서치", "KOSDAQ", "small", "미용·재생의학", "리쥬란 중심의 고성장과 해외 확장", "moderate"),
)

DEFAULT_ANALYSIS_WATCHLIST: tuple[WatchlistEntry, ...] = (
    LARGE_CAP_WATCHLIST + MID_CAP_WATCHLIST + SMALL_CAP_WATCHLIST
)


def get_default_symbols() -> list[str]:
    return [entry.symbol for entry in DEFAULT_ANALYSIS_WATCHLIST]


def get_watchlist_entry(symbol: str) -> WatchlistEntry | None:
    for entry in DEFAULT_ANALYSIS_WATCHLIST:
        if entry.symbol == symbol:
            return entry
    return None


def get_watchlist_entries_by_tier(size_tier: str) -> list[WatchlistEntry]:
    return [entry for entry in DEFAULT_ANALYSIS_WATCHLIST if entry.size_tier == size_tier]


def get_watchlist_entries_by_market(market: str) -> list[WatchlistEntry]:
    return [entry for entry in DEFAULT_ANALYSIS_WATCHLIST if entry.market == market]


def resolve_watchlist_entries(watchlists: list[str] | None = None) -> list[WatchlistEntry]:
    if not watchlists:
        return list(DEFAULT_ANALYSIS_WATCHLIST)

    resolved: list[WatchlistEntry] = []
    seen_symbols: set[str] = set()

    for item in watchlists:
        scope = item.strip().lower()
        if scope == "large":
            entries = LARGE_CAP_WATCHLIST
        elif scope == "mid":
            entries = MID_CAP_WATCHLIST
        elif scope == "small":
            entries = SMALL_CAP_WATCHLIST
        elif scope == "all":
            entries = DEFAULT_ANALYSIS_WATCHLIST
        else:
            entries = ()

        for entry in entries:
            if entry.symbol in seen_symbols:
                continue
            seen_symbols.add(entry.symbol)
            resolved.append(entry)

    return resolved
