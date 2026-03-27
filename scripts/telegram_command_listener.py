"""Telegram command listener for the stock bot."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import sys
import time
import urllib.parse
import urllib.request


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import bot_manager  # noqa: E402
from autostocktrading.brokers.kis import KisApiClient, KisConfig  # noqa: E402
from autostocktrading.config import LARGE_CAP_WATCHLIST, MID_CAP_WATCHLIST, SMALL_CAP_WATCHLIST  # noqa: E402
from autostocktrading.notifications import load_telegram_notifier  # noqa: E402
from autostocktrading.notifications.telegram import format_telegram_request_error  # noqa: E402
from autostocktrading.services.analysis_report import find_latest_analysis_date, read_latest_payload  # noqa: E402
from autostocktrading.services.disclosures import fetch_recent_disclosures, format_disclosures_text  # noqa: E402
from autostocktrading.services.news import fetch_stock_news, format_news_text  # noqa: E402
from autostocktrading.services.value_screener import build_screener_report  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402
from autostocktrading.utils.state import load_json_state, save_json_state  # noqa: E402


OFFSET_PATH = ROOT_DIR / "logs" / "state" / "telegram_listener_offset.json"


def telegram_api_request(bot_token: str, method: str, payload: dict | None = None, timeout: int = 30):
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    http_request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except Exception as exc:
        return None, format_telegram_request_error(exc)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, repr(exc)
    if isinstance(parsed, dict) and parsed.get("ok") is False:
        return None, str(parsed.get("description") or "Telegram API rejected request")
    return parsed, None


def get_updates(bot_token: str, offset: int, timeout: int = 20):
    query = urllib.parse.urlencode({"offset": offset, "timeout": timeout})
    return telegram_api_request(bot_token, f"getUpdates?{query}", payload=None, timeout=timeout + 5)


def extract_message(update: dict) -> tuple[str | None, str | None]:
    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict):
        return None, None
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text")
    return (str(chat_id) if chat_id is not None else None), (str(text).strip() if text else None)


def recent_trade_lines(limit: int = 10) -> list[str]:
    base = ROOT_DIR / "trade_logs"
    if not base.exists():
        return []
    lines: list[str] = []
    for path in sorted(base.rglob("buy_entry.jsonl"), reverse=True):
        for raw in reversed(path.read_text(encoding="utf-8").splitlines()):
            payload = json.loads(raw).get("payload", {})
            lines.append(
                f"- {payload.get('strategy_source')} | {payload.get('name')}({payload.get('symbol')}) | "
                f"{payload.get('status')} | qty {payload.get('quantity')} | price {payload.get('current_price')}"
            )
            if len(lines) >= limit:
                return lines
    return lines


def recent_order_lines(limit: int = 12) -> list[str]:
    base = ROOT_DIR / "trade_logs"
    if not base.exists():
        return []
    lines: list[str] = []
    for path in sorted(base.rglob("*.jsonl"), reverse=True):
        for raw in reversed(path.read_text(encoding="utf-8").splitlines()):
            payload = json.loads(raw).get("payload", {})
            lines.append(
                f"- {payload.get('strategy_source')} | {payload.get('name')}({payload.get('symbol')}) | "
                f"{payload.get('status')} | qty {payload.get('quantity')} | "
                f"budget {payload.get('order_budget_krw')} | style {payload.get('order_style')}"
            )
            if len(lines) >= limit:
                return lines
    return lines


def current_strategy_candidates(strategy_source: str, category: str, target_date: str) -> list[str]:
    base = ROOT_DIR / "structured_logs" / target_date / strategy_source
    if not base.exists():
        return []
    lines: list[str] = []
    for path in sorted(base.rglob("entry_candidate.jsonl")):
        payload = read_latest_payload(path)
        if not payload or not payload.get("entry_candidate"):
            continue
        lines.append(
            f"- {payload.get('name')}({payload.get('symbol')}) | {payload.get('candidate_type')}"
        )
    return lines


def build_balance_text() -> str:
    load_env_file(ROOT_DIR / ".env")
    try:
        client = KisApiClient(KisConfig.from_env())
        token = client.get_access_token()
        balance = client.inquire_balance(token=token)
        cash = client.inquire_possible_order_cash(token=token)
    except Exception as exc:
        return f"잔고 조회 실패\n- {exc}"
    holdings = balance.get("output1") or []
    summary = (balance.get("output2") or [{}])[0]

    lines = ["계좌 요약"]
    ord_psbl_cash = (cash.get("output") or {}).get("ord_psbl_cash")
    if ord_psbl_cash is not None:
        lines.append(f"- 주문가능현금: {ord_psbl_cash}")
    if summary:
        for key, label in [
            ("tot_evlu_amt", "총평가금액"),
            ("scts_evlu_amt", "주식평가금액"),
            ("evlu_pfls_smtl_amt", "평가손익합계"),
            ("dnca_tot_amt", "예수금"),
        ]:
            value = summary.get(key)
            if value not in (None, ""):
                lines.append(f"- {label}: {value}")

    lines.append("")
    lines.append("보유 종목")
    found = False
    for item in holdings:
        qty = item.get("hldg_qty")
        if qty in (None, "", "0"):
            continue
        found = True
        lines.append(
            f"- {item.get('prdt_name')}({item.get('pdno')}) | "
            f"{qty}주 | 평균단가 {item.get('pchs_avg_pric')} | 현재가 {item.get('prpr')} | "
            f"손익 {item.get('evlu_pfls_amt')}"
        )
    if not found:
        lines.append("- 보유 종목 없음")
    return "\n".join(lines)


def latest_report_text() -> str:
    latest_date = find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    if latest_date is None:
        return "최신 리포트가 없습니다."
    report_path = ROOT_DIR / "reports" / latest_date.isoformat() / "system-status.md"
    if report_path.exists():
        return report_path.read_text(encoding="utf-8")
    report_path = ROOT_DIR / "reports" / latest_date.isoformat() / "stock-analysis-report-all.md"
    if report_path.exists():
        return report_path.read_text(encoding="utf-8")
    return "최신 리포트가 없습니다."


def latest_named_report(filename: str) -> str:
    direct_candidates = sorted(ROOT_DIR.glob(f"reports/*/{filename}"), key=lambda p: p.stat().st_mtime, reverse=True)
    if direct_candidates:
        return direct_candidates[0].read_text(encoding="utf-8")
    latest_date = find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    if latest_date is None:
        return "최신 리포트가 없습니다."
    report_path = ROOT_DIR / "reports" / latest_date.isoformat() / filename
    return report_path.read_text(encoding="utf-8") if report_path.exists() else "최신 리포트가 없습니다."


def watchlists_text() -> str:
    def section(title: str, entries) -> list[str]:
        lines = [title]
        lines.extend([f"- {entry.name}({entry.symbol})" for entry in entries])
        return lines

    parts: list[str] = []
    parts.extend(section("대형주 watchlist", LARGE_CAP_WATCHLIST))
    parts.append("")
    parts.extend(section("중형주 watchlist", MID_CAP_WATCHLIST))
    parts.append("")
    parts.extend(section("소형주 watchlist", SMALL_CAP_WATCHLIST))
    return "\n".join(parts)


def disclosures_text(days: int = 3) -> str:
    api_key = os.getenv("DART_API_KEY", "").strip()
    if not api_key:
        return "DART_API_KEY 가 설정되지 않았습니다."
    end_date = date.today()
    begin_date = end_date - timedelta(days=max(days - 1, 0))
    disclosures = fetch_recent_disclosures(
        api_key=api_key,
        stock_codes=[entry.symbol for entry in LARGE_CAP_WATCHLIST + MID_CAP_WATCHLIST + SMALL_CAP_WATCHLIST],
        begin_date=begin_date,
        end_date=end_date,
        page_count=12,
    )
    return "최근 공시\n" + format_disclosures_text(disclosures[:12])


def news_text() -> str:
    symbols = ["005930", "000660", "105560"]
    blocks: list[str] = []
    for symbol in symbols:
        items = fetch_stock_news(symbol, days=3)
        if not items:
            continue
        name = items[0].keyword if items else symbol
        blocks.append(f"[{name}]\n{format_news_text(items, limit=2)}")
    return "최근 뉴스\n" + ("\n\n".join(blocks) if blocks else "- 뉴스 없음")


def readiness_text() -> str:
    latest_date = find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    report_date = latest_date.isoformat() if latest_date else date.today().isoformat()
    report_path = ROOT_DIR / "reports" / report_date / "live-trading-readiness.md"
    return report_path.read_text(encoding="utf-8") if report_path.exists() else "실거래 준비 상태 리포트가 없습니다."


def handle_command(command: str) -> str:
    latest_date = find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    date_str = latest_date.isoformat() if latest_date else ""

    if command in {"/start", "/help"}:
        return (
            "AutoStockBot 명령\n"
            "- /status : 프로세스 상태\n"
            "- /balance, /positions : 잔고/현금\n"
            "- /trades : 최근 거래내역\n"
            "- /orders : 최근 주문 상태\n"
            "- /long : 장타 후보\n"
            "- /short : 단타 후보\n"
            "- /report, /analysis : 최신 리포트\n"
            "- /last : 최신 상태 리포트\n"
            "- /screen : 최신 스크리너\n"
            "- /screen_large : 대형주 스크리너\n"
            "- /screen_mid : 중형주 스크리너\n"
            "- /screen_small : 소형주 스크리너\n"
            "- /watchlists : 전체 watchlist\n"
            "- /news : 최근 뉴스\n"
            "- /disclosures : 최근 공시\n"
            "- /readiness : 실거래 준비 상태\n"
        )
    if command == "/status":
        return "\n".join(bot_manager.build_status_lines(use_color=False))
    if command in {"/balance", "/positions"}:
        return build_balance_text()
    if command == "/trades":
        lines = recent_trade_lines(limit=12)
        return "최근 거래내역\n" + ("\n".join(lines) if lines else "- 거래 로그 없음")
    if command == "/orders":
        lines = recent_order_lines(limit=12)
        return "최근 주문 상태\n" + ("\n".join(lines) if lines else "- 주문 로그 없음")
    if command == "/long":
        lines = current_strategy_candidates("kr_long_term", "long_term", date_str)
        return "장타 후보\n" + ("\n".join(lines) if lines else "- 현재 기준 후보 없음")
    if command == "/short":
        lines = current_strategy_candidates("kr_short_term", "short_term", date_str)
        return "단타 후보\n" + ("\n".join(lines) if lines else "- 현재 기준 후보 없음")
    if command in {"/report", "/analysis"}:
        return latest_report_text()
    if command == "/last":
        latest_date = find_latest_analysis_date(ROOT_DIR / "analysis_logs")
        if latest_date is None:
            return "최신 상태 리포트가 없습니다."
        report_path = ROOT_DIR / "reports" / latest_date.isoformat() / "system-status.md"
        return report_path.read_text(encoding="utf-8") if report_path.exists() else "최신 상태 리포트가 없습니다."
    if command == "/screen":
        return latest_named_report("value-recovery-screener.md")
    if command == "/screen_large":
        return latest_named_report("value-recovery-screener-large.md")
    if command == "/screen_mid":
        return latest_named_report("value-recovery-screener-mid.md")
    if command == "/screen_small":
        return latest_named_report("value-recovery-screener-small.md")
    if command == "/watchlists":
        return watchlists_text()
    if command == "/news":
        return news_text()
    if command == "/disclosures":
        return disclosures_text()
    if command == "/readiness":
        return readiness_text()
    return "알 수 없는 명령입니다. /help 를 입력하세요."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Telegram stock command listener.")
    parser.add_argument("--poll-sec", type=int, default=5, help="Polling interval in seconds. Default: 5")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")
    notifier = load_telegram_notifier()
    if not notifier.enabled or not notifier.bot_token or not notifier.chat_id:
        print("[FAIL] Telegram is not fully configured.")
        return 1

    state = load_json_state(OFFSET_PATH, default={"offset": 0})
    offset = int(state.get("offset", 0))

    while True:
        result, error = get_updates(notifier.bot_token, offset=offset, timeout=max(args.poll_sec, 5))
        if error:
            print(f"[FAIL] Telegram getUpdates failed: {error}")
            time.sleep(max(args.poll_sec, 5))
            continue

        updates = result.get("result", []) if isinstance(result, dict) else []
        for update in updates:
            offset = max(offset, int(update.get("update_id", 0)) + 1)
            state["offset"] = offset
            save_json_state(OFFSET_PATH, state)
            chat_id, text = extract_message(update)
            if not chat_id or not text:
                continue
            if chat_id != notifier.chat_id:
                continue

            try:
                response_text = handle_command(text)
            except Exception as exc:
                response_text = f"명령 처리 실패\n- {exc}"
            notifier.send_message_chunks(response_text)

        state["offset"] = offset
        save_json_state(OFFSET_PATH, state)
        time.sleep(max(args.poll_sec, 5))


if __name__ == "__main__":
    raise SystemExit(main())
