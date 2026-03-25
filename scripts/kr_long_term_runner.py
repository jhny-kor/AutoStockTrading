"""Run the Korean long-term strategy on shared analysis logs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.config.kr_strategy_watchlists import get_long_term_entries  # noqa: E402
from autostocktrading.strategies import evaluate_long_term_candidate  # noqa: E402
from autostocktrading.services.strategy_signal_runner import run_signal_batch  # noqa: E402


STATE_PATH = ROOT_DIR / "logs" / "state" / "kr_long_term_runner.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Korean long-term signal runner.")
    parser.add_argument("--once", action="store_true", help="Run one evaluation pass and exit.")
    parser.add_argument("--poll-sec", type=int, default=30, help="Polling interval in seconds. Default: 30")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    while True:
        code = run_signal_batch(
            strategy_source="kr_long_term",
            strategy_category="long_term",
            entries=get_long_term_entries(),
            evaluate_fn=evaluate_long_term_candidate,
            state_path=STATE_PATH,
        )
        if code != 0:
            return code
        if args.once:
            break
        time.sleep(max(args.poll_sec, 10))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
