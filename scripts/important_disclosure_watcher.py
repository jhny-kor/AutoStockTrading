"""Poll OpenDART and send Telegram alerts for important disclosures."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import os
from pathlib import Path
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.config import get_default_symbols  # noqa: E402
from autostocktrading.notifications import load_telegram_notifier  # noqa: E402
from autostocktrading.services.disclosures import fetch_recent_disclosures  # noqa: E402
from autostocktrading.services.reporting import is_important_disclosure  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402
from autostocktrading.utils.state import load_json_state, save_json_state  # noqa: E402


STATE_PATH = ROOT_DIR / "logs" / "state" / "important_disclosures.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch important disclosures and alert to Telegram.")
    parser.add_argument("--once", action="store_true", help="Run one disclosure check and exit.")
    parser.add_argument(
        "--poll-sec",
        type=int,
        default=300,
        help="Polling interval in seconds. Default: 300",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Look back this many days when polling OpenDART. Default: 3",
    )
    return parser


def build_message(item) -> str:
    return (
        "[중요 공시]\n"
        f"- 종목: {item.corp_name} ({item.stock_code})\n"
        f"- 공시: {item.report_name.strip()}\n"
        f"- 접수일: {item.receipt_date}\n"
        f"- 링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.rcept_no}"
    )


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    notifier = load_telegram_notifier()
    if not notifier.enabled:
        print("[FAIL] Telegram is not enabled.")
        return 1

    api_key = os.getenv("DART_API_KEY", "").strip()
    if not api_key:
        print("[FAIL] DART_API_KEY is not set.")
        return 1

    state = load_json_state(STATE_PATH, default={"seen_receipts": []})

    while True:
        end_date = date.today()
        begin_date = end_date - timedelta(days=max(args.days - 1, 0))

        try:
            disclosures = fetch_recent_disclosures(
                api_key=api_key,
                stock_codes=get_default_symbols(),
                begin_date=begin_date,
                end_date=end_date,
                page_count=20,
            )
        except Exception as exc:
            print(f"[FAIL] Disclosure poll failed: {exc}")
            if args.once:
                return 1
            time.sleep(max(args.poll_sec, 30))
            continue

        seen = set(state.get("seen_receipts", []))
        if not seen:
            state["seen_receipts"] = sorted({item.rcept_no for item in disclosures})[-500:]
            save_json_state(STATE_PATH, state)
            print(f"[OK] Seeded disclosure watcher state with {len(state['seen_receipts'])} receipts.")
            if args.once:
                break
            time.sleep(max(args.poll_sec, 30))
            continue

        new_seen = list(seen)
        for item in disclosures:
            if item.rcept_no in seen:
                continue
            if not is_important_disclosure(item.report_name):
                continue

            sent, error = notifier.send_message_detailed(build_message(item))
            if sent:
                new_seen.append(item.rcept_no)
                print(f"[OK] Important disclosure sent: {item.stock_code} {item.report_name.strip()}")
            else:
                print(f"[FAIL] Telegram send failed for {item.rcept_no}: {error}")

        state["seen_receipts"] = sorted(set(new_seen))[-500:]
        save_json_state(STATE_PATH, state)

        if args.once:
            break
        time.sleep(max(args.poll_sec, 30))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
