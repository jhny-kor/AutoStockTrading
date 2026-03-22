"""Helpers for Telegram-ready daily reports and disclosure alert messages."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from autostocktrading.config import DEFAULT_ANALYSIS_WATCHLIST, get_default_symbols
from .analysis_report import build_analysis_report
from .disclosures import format_disclosures_text, fetch_recent_disclosures
from .news import fetch_stock_news, format_news_text


ROOT_DIR = Path(__file__).resolve().parents[3]


def _read_report_file(target_date: date) -> str:
    report_path = ROOT_DIR / "reports" / target_date.isoformat() / "stock-analysis-report.md"
    if report_path.exists():
        return report_path.read_text(encoding="utf-8")
    return build_analysis_report(target_date)


def build_daily_report_message(
    *,
    target_date: date,
    slot_label: str,
    dart_api_key: str | None = None,
    news_symbols: list[str] | None = None,
) -> str:
    sections: list[str] = [f"[주식 일일 리포트] {target_date.isoformat()} {slot_label}", ""]
    sections.append(_read_report_file(target_date).strip())

    chosen_symbols = news_symbols or ["005930", "000660", "105560"]
    news_blocks: list[str] = []
    for symbol in chosen_symbols:
        try:
            items = fetch_stock_news(symbol, days=3)
        except Exception:
            continue
        if not items:
            continue
        name = next((entry.name for entry in DEFAULT_ANALYSIS_WATCHLIST if entry.symbol == symbol), symbol)
        news_blocks.append(f"[{name} 뉴스]\n{format_news_text(items, limit=2)}")

    if news_blocks:
        sections.extend(["", "## 주요 뉴스", *news_blocks])

    if dart_api_key:
        try:
            disclosures = fetch_recent_disclosures(
                api_key=dart_api_key,
                stock_codes=get_default_symbols(),
                begin_date=target_date - timedelta(days=2),
                end_date=target_date,
                page_count=10,
            )
        except Exception:
            disclosures = []

        if disclosures:
            sections.extend(["", "## 최근 공시", format_disclosures_text(disclosures[:8])])

    return "\n".join(sections).strip()


IMPORTANT_DISCLOSURE_KEYWORDS = (
    "유상증자",
    "무상증자",
    "자기주식취득결정",
    "자기주식처분결정",
    "기업가치제고계획",
    "단일판매ㆍ공급계약체결",
    "타법인주식및출자증권취득결정",
    "영업정지",
    "중대재해발생",
    "감자결정",
    "합병결정",
    "분할결정",
    "최대주주변경",
)


def is_important_disclosure(report_name: str) -> bool:
    return any(keyword in report_name for keyword in IMPORTANT_DISCLOSURE_KEYWORDS)
