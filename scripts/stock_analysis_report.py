"""Build a readable report from collected stock analysis logs."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.services.analysis_report import (  # noqa: E402
    build_analysis_report,
    find_latest_analysis_date,
)


def parse_iso_date(raw: str) -> date:
    return date.fromisoformat(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a stock analysis summary report.")
    parser.add_argument(
        "--date",
        type=parse_iso_date,
        help="Report date in YYYY-MM-DD format. Default: latest available date.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Also write the report into reports/YYYY-MM-DD/stock-analysis-report.md",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_date = args.date or find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    if target_date is None:
        print("[FAIL] No analysis logs are available yet.")
        return 1

    report = build_analysis_report(target_date)
    print(report)

    if args.write:
        report_dir = ROOT_DIR / "reports" / target_date.isoformat()
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "stock-analysis-report.md"
        report_path.write_text(report, encoding="utf-8")
        print("")
        print(f"[OK] Report written to {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
