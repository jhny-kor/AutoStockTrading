"""Korean stock news collection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from email.utils import parsedate_to_datetime
import json
from typing import Iterable
from urllib import parse, request
import xml.etree.ElementTree as ET

from autostocktrading.config import get_watchlist_entry


GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


@dataclass(frozen=True)
class NewsItem:
    symbol: str
    keyword: str
    title: str
    link: str
    published_at: str | None
    source_name: str | None


def fetch_google_news_rss(
    *,
    keyword: str,
    days: int = 7,
    hl: str = "ko",
    gl: str = "KR",
    ceid: str = "KR:ko",
) -> str:
    query = f"{keyword} when:{days}d"
    params = parse.urlencode(
        {
            "q": query,
            "hl": hl,
            "gl": gl,
            "ceid": ceid,
        }
    )
    url = f"{GOOGLE_NEWS_RSS_URL}?{params}"
    http_request = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with request.urlopen(http_request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_google_news_rss(xml_text: str, *, symbol: str, keyword: str) -> list[NewsItem]:
    root = ET.fromstring(xml_text)
    items: list[NewsItem] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_element = item.find("source")
        source_name = source_element.text.strip() if source_element is not None and source_element.text else None
        published_at = None
        if pub_date:
            try:
                published_at = parsedate_to_datetime(pub_date).isoformat()
            except (TypeError, ValueError, IndexError):
                published_at = pub_date
        items.append(
            NewsItem(
                symbol=symbol,
                keyword=keyword,
                title=title,
                link=link,
                published_at=published_at,
                source_name=source_name,
            )
        )
    return items


def fetch_stock_news(symbol: str, *, days: int = 7) -> list[NewsItem]:
    entry = get_watchlist_entry(symbol)
    keyword = entry.name if entry else symbol
    xml_text = fetch_google_news_rss(keyword=keyword, days=days)
    return parse_google_news_rss(xml_text, symbol=symbol, keyword=keyword)


def format_news_text(items: Iterable[NewsItem], *, limit: int = 5) -> str:
    lines: list[str] = []
    for index, item in enumerate(items):
        if index >= limit:
            break
        source = f" | {item.source_name}" if item.source_name else ""
        published = f"{item.published_at} | " if item.published_at else ""
        lines.append(f"- {published}{item.title}{source}\n  {item.link}")
    return "\n".join(lines) if lines else "최근 뉴스가 없습니다."


def news_items_to_payload(items: Iterable[NewsItem]) -> list[dict[str, str | None]]:
    return [
        {
            "symbol": item.symbol,
            "keyword": item.keyword,
            "title": item.title,
            "link": item.link,
            "published_at": item.published_at,
            "source_name": item.source_name,
        }
        for item in items
    ]
