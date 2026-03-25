"""Order engine for Korean short-term strategy signals."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.utils.env import load_env_file  # noqa: E402
from autostocktrading.services.order_engine import run_order_batch  # noqa: E402


STATE_PATH = ROOT_DIR / "logs" / "state" / "kr_short_term_trader.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Korean short-term order engine.")
    parser.add_argument("--once", action="store_true", help="Run one order pass and exit.")
    parser.add_argument("--poll-sec", type=int, default=60, help="Polling interval in seconds. Default: 60")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    while True:
        code = run_order_batch(
            strategy_source="kr_short_term",
            strategy_category="short_term",
            state_path=STATE_PATH,
            config_prefix="KR_SHORT",
        )
        if code != 0:
            return code
        if args.once:
            break
        time.sleep(max(args.poll_sec, 10))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
