"""IPO subscription schedule fetcher for Korean public offerings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
from typing import Iterable
from urllib import request


IPO_SCHEDULE_URL = "http://www.38.co.kr/html/fund/index.htm?o=k"
TABLE_RE = re.compile(
    r'<table[^>]*summary="공모주 청약일정"[^>]*>.*?<tbody>(?P<tbody>.*?)</tbody>',
    re.DOTALL,
)
ROW_RE = re.compile(r"<tr[^>]*>(?P<row>.*?)</tr>", re.DOTALL)
CELL_RE = re.compile(r"<td[^>]*>(?P<cell>.*?)</td>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
PERIOD_RE = re.compile(
    r"(?P<start_year>\d{4})\.(?P<start_month>\d{2})\.(?P<start_day>\d{2})~"
    r"(?:(?P<end_year>\d{4})\.)?(?P<end_month>\d{2})\.(?P<end_day>\d{2})"
)


@dataclass(frozen=True)
class IpoScheduleEntry:
    name: str
    subscription_period: str
    fixed_offer_price: str
    target_offer_price: str
    competition_rate: str
    lead_underwriters: str
    source_path: str | None = None

    def parsed_period(self) -> tuple[date, date] | None:
        match = PERIOD_RE.search(self.subscription_period)
        if not match:
            return None

        start = date(
            int(match.group("start_year")),
            int(match.group("start_month")),
            int(match.group("start_day")),
        )
        end = date(
            int(match.group("end_year") or match.group("start_year")),
            int(match.group("end_month")),
            int(match.group("end_day")),
        )
        return start, end


def fetch_ipo_schedule() -> list[IpoScheduleEntry]:
    req = request.Request(IPO_SCHEDULE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with request.urlopen(req, timeout=10) as response:
        raw = response.read()

    html = raw.decode("euc-kr", errors="replace")
    return parse_ipo_schedule_html(html)


def parse_ipo_schedule_html(html: str) -> list[IpoScheduleEntry]:
    table_match = TABLE_RE.search(html)
    if not table_match:
        raise ValueError("공모주 청약일정 테이블을 찾지 못했습니다.")

    entries: list[IpoScheduleEntry] = []
    tbody = table_match.group("tbody")

    for row_match in ROW_RE.finditer(tbody):
        cells = [
            _clean_cell(cell_match.group("cell"))
            for cell_match in CELL_RE.finditer(row_match.group("row"))
        ]
        if len(cells) < 6:
            continue

        source_path = _extract_first_href(row_match.group("row"))
        entries.append(
            IpoScheduleEntry(
                name=cells[0],
                subscription_period=cells[1],
                fixed_offer_price=cells[2],
                target_offer_price=cells[3],
                competition_rate=cells[4],
                lead_underwriters=cells[5],
                source_path=source_path,
            )
        )

    return entries


def filter_upcoming_entries(
    entries: Iterable[IpoScheduleEntry],
    *,
    today: date | None = None,
    include_recent_days: int = 0,
) -> list[IpoScheduleEntry]:
    current_day = today or datetime.now().date()
    filtered: list[IpoScheduleEntry] = []

    for entry in entries:
        parsed = entry.parsed_period()
        if not parsed:
            continue
        start, end = parsed
        if end.toordinal() >= current_day.toordinal() - include_recent_days:
            filtered.append(entry)

    return _sort_entries_by_start_date(filtered)


def filter_entries_starting_on_date(
    entries: Iterable[IpoScheduleEntry],
    *,
    target_date: date | None = None,
) -> list[IpoScheduleEntry]:
    current_day = target_date or datetime.now().date()
    filtered: list[IpoScheduleEntry] = []

    for entry in entries:
        parsed = entry.parsed_period()
        if not parsed:
            continue
        start, _ = parsed
        if start == current_day:
            filtered.append(entry)

    return _sort_entries_by_start_date(filtered)


def filter_entries_starting_in_week(
    entries: Iterable[IpoScheduleEntry],
    *,
    reference_date: date | None = None,
) -> list[IpoScheduleEntry]:
    current_day = reference_date or datetime.now().date()
    week_start = current_day - timedelta(days=current_day.weekday())
    week_end = week_start + timedelta(days=6)
    filtered: list[IpoScheduleEntry] = []

    for entry in entries:
        parsed = entry.parsed_period()
        if not parsed:
            continue
        start, _ = parsed
        if week_start <= start <= week_end:
            filtered.append(entry)

    return _sort_entries_by_start_date(filtered)


def format_ipo_schedule_message(
    entries: Iterable[IpoScheduleEntry],
    *,
    title: str = "[공모주 청약일정]",
) -> str:
    lines = [title]
    count = 0

    for entry in entries:
        count += 1
        lines.append(f"- {entry.name} | {entry.subscription_period}")
        lines.append(f"  희망공모가: {entry.target_offer_price}")
        if entry.fixed_offer_price and entry.fixed_offer_price != "-":
            lines.append(f"  확정공모가: {entry.fixed_offer_price}")
        if entry.lead_underwriters:
            lines.append(f"  주간사: {entry.lead_underwriters}")
        if entry.source_path:
            lines.append(f"  출처: https://www.38.co.kr{entry.source_path}")

    if count == 0:
        lines.append("- 예정된 공모주 청약 일정이 보이지 않습니다.")

    return "\n".join(lines)


def _clean_cell(raw: str) -> str:
    without_tags = TAG_RE.sub(" ", raw)
    normalized = SPACE_RE.sub(" ", without_tags)
    return normalized.replace("&nbsp;", " ").replace("\xa0", " ").strip()


def _extract_first_href(raw_row_html: str) -> str | None:
    match = re.search(r'href="(?P<href>/html/fund/\?o=v[^"]+)"', raw_row_html)
    if not match:
        return None
    return match.group("href").replace("&amp;", "&")


def _sort_entries_by_start_date(entries: list[IpoScheduleEntry]) -> list[IpoScheduleEntry]:
    return sorted(
        entries,
        key=lambda entry: (
            entry.parsed_period()[0] if entry.parsed_period() else date.max,
            entry.name,
        ),
    )
