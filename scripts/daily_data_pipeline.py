"""Run collection, reporting, screening, and archival in one batch."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.config import get_default_symbols  # noqa: E402
from autostocktrading.brokers.kis import KisApiClient, KisConfig  # noqa: E402
from autostocktrading.logs import LogDirectoryManager, archive_old_log_directories  # noqa: E402
from autostocktrading.services.analysis_report import build_analysis_report, find_latest_analysis_date  # noqa: E402
from autostocktrading.services.value_screener import build_screener_report  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402
from autostocktrading.strategies import evaluate_buy_candidate  # noqa: E402
from autostocktrading.services.stock_analysis import build_stock_analysis_snapshot, parse_daily_bars  # noqa: E402
from autostocktrading.logs import DailyJsonlLogger  # noqa: E402


ARCHIVE_ROOTS = (
    ("logs", "archives/logs"),
    ("analysis_logs", "archives/analysis_logs"),
    ("structured_logs", "archives/structured_logs"),
    ("news_logs", "archives/news_logs"),
    ("disclosure_logs", "archives/disclosure_logs"),
    ("reports", "archives/reports"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the stock data pipeline in one batch.")
    parser.add_argument(
        "--report-date",
        type=date.fromisoformat,
        help="Use this report date instead of the latest available one.",
    )
    parser.add_argument(
        "--keep-days",
        type=int,
        default=14,
        help="Archive data older than this many recent days. Default: 14",
    )
    parser.add_argument(
        "--skip-collect",
        action="store_true",
        help="Skip the collection step and only build reports/screens/archive.",
    )
    parser.add_argument(
        "--archive-dry-run",
        action="store_true",
        help="Only show archival targets without creating tar.gz files.",
    )
    return parser


def write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_collection() -> None:
    config = KisConfig.from_env()
    client = KisApiClient(config)
    analysis_logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "analysis_logs",
            archive_root=ROOT_DIR / "archives" / "analysis_logs",
        )
    )
    strategy_logger = DailyJsonlLogger(
        LogDirectoryManager(
            log_root=ROOT_DIR / "structured_logs",
            archive_root=ROOT_DIR / "archives" / "structured_logs",
        )
    )

    current_date = date.today()
    start_date = (current_date - timedelta(days=180)).strftime("%Y%m%d")
    end_date = current_date.strftime("%Y%m%d")
    token = client.get_access_token()

    for symbol in get_default_symbols():
        quote_response = client.inquire_price(symbol, token=token)
        try:
            daily_response = client.inquire_daily_itemchart_price(
                symbol,
                start_date=start_date,
                end_date=end_date,
                token=token,
            )
            daily_bars = parse_daily_bars(daily_response)
        except Exception:
            daily_response = client.inquire_daily_price(symbol, token=token)
            daily_bars = parse_daily_bars(daily_response)

        snapshot = build_stock_analysis_snapshot(
            symbol=symbol,
            quote_response=quote_response,
            daily_bars=daily_bars,
        )
        decision = evaluate_buy_candidate(snapshot)
        analysis_logger.append_event(
            source="kis_analysis",
            symbol=symbol,
            category="stocks",
            event_type="snapshot",
            payload=snapshot,
        )
        strategy_logger.append_event(
            source="stock_strategy",
            symbol=symbol,
            category="korean_bluechips",
            event_type="buy_candidate",
            payload=decision,
        )


def main() -> int:
    args = build_parser().parse_args()
    load_env_file(ROOT_DIR / ".env")

    if not args.skip_collect:
        run_collection()

    target_date = args.report_date or find_latest_analysis_date(ROOT_DIR / "analysis_logs")
    if target_date is None:
        print("[FAIL] No analysis logs available after collection.")
        return 1

    report_dir = ROOT_DIR / "reports" / target_date.isoformat()
    report_dir.mkdir(parents=True, exist_ok=True)

    watchlist_scopes = ["all", "large", "mid", "small"]
    for scope in watchlist_scopes:
        content = build_analysis_report(target_date, watchlists=[scope])
        write_report(report_dir / f"stock-analysis-report-{scope}.md", content)
        print(f"[OK] Wrote stock analysis report: {scope}")

        screener = build_screener_report(target_date=target_date, watchlists=[scope])
        write_report(report_dir / f"value-recovery-screener-{scope}.md", screener)
        print(f"[OK] Wrote screener report: {scope}")

    for log_root, archive_root in ARCHIVE_ROOTS:
        archived = archive_old_log_directories(
            manager=LogDirectoryManager(
                log_root=ROOT_DIR / log_root,
                archive_root=ROOT_DIR / archive_root,
            ),
            keep_days=args.keep_days,
            today=target_date,
            dry_run=args.archive_dry_run,
        )
        if archived:
            print(f"[OK] Archive targets for {log_root}: {len(archived)}")
        else:
            print(f"[OK] No archive targets for {log_root}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
