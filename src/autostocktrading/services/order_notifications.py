"""Helpers for notifying order submission and fill status."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from autostocktrading.brokers.kis import KisApiClient, KisConfig
from autostocktrading.notifications import load_telegram_notifier
from autostocktrading.utils.env import load_env_file
from autostocktrading.utils.state import load_json_state, save_json_state


ROOT_DIR = Path(__file__).resolve().parents[3]


def build_submission_message(payload: dict[str, Any]) -> str:
    return (
        "[주문 전송]\n"
        f"- 전략: {payload.get('strategy_source')}\n"
        f"- 종목: {payload.get('name')} ({payload.get('symbol')})\n"
        f"- 유형: {payload.get('candidate_type')}\n"
        f"- 수량: {payload.get('quantity')}주\n"
        f"- 주문형태: {payload.get('order_style')}\n"
        f"- 가격: {payload.get('limit_price', payload.get('current_price'))}\n"
        f"- 상태: {payload.get('status')}"
    )


def build_fill_message(row: dict[str, Any]) -> str:
    total_ccld_qty = row.get("tot_ccld_qty")
    remain_qty = row.get("rmn_qty")
    avg_price = row.get("avg_prvs")
    status = "체결완료" if str(remain_qty) == "0" and str(total_ccld_qty) != "0" else "미체결/부분체결"
    return (
        "[주문 상태]\n"
        f"- 종목: {row.get('prdt_name')} ({row.get('pdno')})\n"
        f"- 주문번호: {row.get('odno')}\n"
        f"- 상태: {status}\n"
        f"- 주문수량: {row.get('ord_qty')}\n"
        f"- 체결수량: {total_ccld_qty}\n"
        f"- 미체결수량: {remain_qty}\n"
        f"- 평균체결가: {avg_price}"
    )


def notify_submission(payload: dict[str, Any]) -> tuple[bool, str | None]:
    load_env_file(ROOT_DIR / ".env")
    notifier = load_telegram_notifier()
    if not notifier.enabled:
        return False, "telegram_disabled"
    return notifier.send_message_chunks(build_submission_message(payload))


def poll_and_notify_order_statuses(state_path: Path) -> int:
    load_env_file(ROOT_DIR / ".env")
    notifier = load_telegram_notifier()
    if not notifier.enabled:
        return 1

    state = load_json_state(state_path, default={"pending_orders": []})
    pending = state.get("pending_orders", [])
    if not pending:
        return 0

    client = KisApiClient(KisConfig.from_env())
    token = client.get_access_token()
    remaining: list[dict[str, Any]] = []

    for item in pending:
        order_no = item.get("order_no", "")
        branch_no = item.get("order_branch_no", "")
        symbol = item.get("symbol", "")
        order_date = item.get("order_date", date.today().strftime("%Y%m%d"))
        inquiry = client.inquire_daily_ccld(
            start_date=order_date,
            end_date=order_date,
            symbol=symbol,
            order_branch_no=branch_no,
            order_no=order_no,
            token=token,
        )
        rows = inquiry.get("output1") or []
        matched = None
        for row in rows:
            if row.get("odno") == order_no:
                matched = row
                break

        if not matched:
            remaining.append(item)
            continue

        sent, _ = notifier.send_message_chunks(build_fill_message(matched))
        if not sent:
            remaining.append(item)
            continue

        if str(matched.get("rmn_qty")) != "0":
            remaining.append(item)

    state["pending_orders"] = remaining
    save_json_state(state_path, state)
    return 0
