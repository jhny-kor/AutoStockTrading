"""Send scheduled stock daily reports to Telegram with duplicate suppression."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.notifications import load_telegram_notifier  # noqa: E402
from autostocktrading.services.reporting import build_daily_report_message  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402
from autostocktrading.utils.state import load_json_state, save_json_state  # noqa: E402


STATE_PATH = ROOT_DIR / "logs" / "state" / "daily_report_scheduler.json"
DEFAULT_SLOTS = ("08:30", "12:10", "15:40")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send scheduled stock daily reports.")
    parser.add_argument("--once", action="store_true", help="Run a single scheduler check and exit.")
    parser.add_argument(
        "--slots",
        default=",".join(DEFAULT_SLOTS),
        help="Comma-separated HH:MM report slots. Default: 08:30,12:10,15:40",
    )
    parser.add_argument(
        "--poll-sec",
        type=int,
        default=30,
        help="Polling interval in seconds. Default: 30",
    )
    return parser


def parse_slots(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def current_slot_label(now: datetime, slots: list[str]) -> str | None:
    current = now.strftime("%H:%M")
    return current if current in slots else None


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    notifier = load_telegram_notifier()
    if not notifier.enabled:
        print("[FAIL] Telegram is not enabled.")
        return 1

    dart_api_key = os.getenv("DART_API_KEY", "").strip() or None
    slots = parse_slots(args.slots)
    state = load_json_state(
        STATE_PATH,
        default={"sent_slots": {}, "last_report_hash": "", "last_report_date": ""},
    )

    while True:
        now = datetime.now()
        slot_label = current_slot_label(now, slots)
        today = now.date().isoformat()

        if slot_label:
            sent_slots = state.setdefault("sent_slots", {})
            sent_for_today = sent_slots.setdefault(today, [])
            if slot_label not in sent_for_today:
                message = build_daily_report_message(
                    target_date=now.date(),
                    slot_label=slot_label,
                    dart_api_key=dart_api_key,
                )
                digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
                if state.get("last_report_hash") != digest or state.get("last_report_date") != today:
                    sent, error = notifier.send_message_detailed(message)
                    if sent:
                        sent_for_today.append(slot_label)
                        state["last_report_hash"] = digest
                        state["last_report_date"] = today
                        save_json_state(STATE_PATH, state)
                        print(f"[OK] Report sent for {today} {slot_label}")
                    else:
                        print(f"[FAIL] Report send failed for {today} {slot_label}: {error}")
                else:
                    sent_for_today.append(slot_label)
                    save_json_state(STATE_PATH, state)
                    print(f"[SKIP] Duplicate report suppressed for {today} {slot_label}")

        if args.once:
            break
        time.sleep(max(args.poll_sec, 10))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
