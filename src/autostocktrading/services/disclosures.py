"""OpenDART disclosure collection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import io
import json
from pathlib import Path
from typing import Any
from urllib import parse, request
import xml.etree.ElementTree as ET
import zipfile

from autostocktrading.config import get_watchlist_entry


CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
DISCLOSURE_LIST_URL = "https://opendart.fss.or.kr/api/list.json"


@dataclass(frozen=True)
class DartDisclosure:
    stock_code: str
    corp_code: str
    corp_name: str
    report_name: str
    rcept_no: str
    receipt_date: str
    market: str | None
    disclosure_type: str | None
    detail_type: str | None


def fetch_corp_code_map(api_key: str) -> dict[str, dict[str, str]]:
    query = parse.urlencode({"crtfc_key": api_key})
    with request.urlopen(f"{CORP_CODE_URL}?{query}", timeout=20) as response:
        payload = response.read()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        if not names:
            raise ValueError("OpenDART corp code response was empty.")
        xml_bytes = archive.read(names[0])

    root = ET.fromstring(xml_bytes)
    corp_map: dict[str, dict[str, str]] = {}
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        corp_name = (item.findtext("corp_name") or "").strip()
        if not stock_code or not corp_code:
            continue
        corp_map[stock_code] = {
            "corp_code": corp_code,
            "corp_name": corp_name,
        }
    return corp_map


def fetch_recent_disclosures(
    *,
    api_key: str,
    stock_codes: list[str],
    begin_date: date,
    end_date: date,
    page_count: int = 20,
) -> list[DartDisclosure]:
    corp_map = fetch_corp_code_map(api_key)
    disclosures: list[DartDisclosure] = []

    for stock_code in stock_codes:
        corp_info = corp_map.get(stock_code)
        if not corp_info:
            continue

        params = {
            "crtfc_key": api_key,
            "corp_code": corp_info["corp_code"],
            "bgn_de": begin_date.strftime("%Y%m%d"),
            "end_de": end_date.strftime("%Y%m%d"),
            "page_no": "1",
            "page_count": str(page_count),
        }
        query = parse.urlencode(params)
        with request.urlopen(f"{DISCLOSURE_LIST_URL}?{query}", timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if payload.get("status") not in (None, "000", "013"):
            raise ValueError(f"OpenDART disclosure fetch failed for {stock_code}: {payload}")

        for row in payload.get("list", []) or []:
            disclosures.append(
                DartDisclosure(
                    stock_code=stock_code,
                    corp_code=corp_info["corp_code"],
                    corp_name=row.get("corp_name") or corp_info["corp_name"],
                    report_name=row.get("report_nm", ""),
                    rcept_no=row.get("rcept_no", ""),
                    receipt_date=row.get("rcept_dt", ""),
                    market=row.get("corp_cls"),
                    disclosure_type=row.get("pblntf_ty"),
                    detail_type=row.get("pblntf_detail_ty"),
                )
            )

    disclosures.sort(key=lambda item: (item.receipt_date, item.stock_code, item.rcept_no), reverse=True)
    return disclosures


def format_disclosures_text(disclosures: list[DartDisclosure]) -> str:
    if not disclosures:
        return "최근 공시가 없습니다."

    lines: list[str] = []
    for item in disclosures:
        entry = get_watchlist_entry(item.stock_code)
        name = entry.name if entry else item.corp_name
        lines.append(
            f"- {item.receipt_date} {name}({item.stock_code}) | {item.report_name} | "
            f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.rcept_no}"
        )
    return "\n".join(lines)
