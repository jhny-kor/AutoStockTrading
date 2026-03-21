"""Build a readable report from collected stock analysis logs."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime
import json
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.config import DEFAULT_ANALYSIS_WATCHLIST, get_watchlist_entry  # noqa: E402


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


def find_latest_date(base_dir: Path) -> date | None:
    if not base_dir.exists():
        return None
    dates = []
    for child in base_dir.iterdir():
        if child.is_dir():
            try:
                dates.append(date.fromisoformat(child.name))
            except ValueError:
                continue
    return max(dates) if dates else None


def read_latest_payload(path: Path) -> dict | None:
    if not path.exists():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return json.loads(lines[-1]).get("payload")


def build_report(target_date: date) -> str:
    date_str = target_date.isoformat()
    lines: list[str] = [f"# 주식 분석 리포트", "", f"- 기준일: {date_str}", ""]

    candidate_lines: list[str] = []
    summaries: list[str] = []
    type_buckets: dict[str, list[str]] = defaultdict(list)

    for entry in DEFAULT_ANALYSIS_WATCHLIST:
        analysis_path = ROOT_DIR / "analysis_logs" / date_str / "kis_analysis" / entry.symbol / "stocks" / "snapshot.jsonl"
        strategy_path = ROOT_DIR / "structured_logs" / date_str / "stock_strategy" / entry.symbol / "korean_bluechips" / "buy_candidate.jsonl"

        analysis = read_latest_payload(analysis_path)
        decision = read_latest_payload(strategy_path)
        if not analysis or not decision:
            summaries.append(f"## {entry.name} ({entry.symbol})\n- 로그가 아직 없습니다.")
            continue

        if decision.get("buy_candidate"):
            label = decision.get("candidate_type") or "candidate"
            type_buckets[label].append(entry.name)
            candidate_lines.append(
                f"- {entry.name} ({entry.symbol}): {label}, RSI {analysis.get('rsi_14'):.2f}, "
                f"20일선 대비 {analysis.get('price_vs_sma_20_pct'):.2f}%, 거래량배수 {analysis.get('volume_ratio_20'):.2f}"
            )

        blockers = (
            decision.get("hard_blockers")
            or decision.get("pullback_blockers")
            or decision.get("breakout_blockers")
            or []
        )
        blocker_text = ", ".join(blockers) if blockers else "없음"

        summaries.append(
            "\n".join(
                [
                    f"## {entry.name} ({entry.symbol})",
                    f"- 테마: {entry.theme}",
                    f"- 장기 포인트: {entry.long_term_reason}",
                    f"- 현재가: {analysis.get('current_price')}",
                    f"- 일간 등락률: {analysis.get('day_change_pct')}%",
                    f"- 5일/20일 수익률: {analysis.get('daily_return_5d_pct'):.2f}% / {analysis.get('daily_return_20d_pct'):.2f}%",
                    f"- RSI 14: {analysis.get('rsi_14'):.2f}",
                    f"- 거래량 배수(20일): {analysis.get('volume_ratio_20'):.2f}",
                    f"- 20일선/60일선 대비: {analysis.get('price_vs_sma_20_pct'):.2f}% / {analysis.get('price_vs_sma_60_pct'):.2f}%",
                    f"- 20일 범위 위치: {analysis.get('range_position_20d_pct'):.2f}%",
                    f"- 매수 후보: {decision.get('buy_candidate')} ({decision.get('candidate_type')})",
                    f"- 차단 사유: {blocker_text}",
                ]
            )
        )

    lines.append("## 후보 요약")
    if candidate_lines:
        lines.extend(candidate_lines)
    else:
        lines.append("- 현재 기준 매수 후보가 없습니다.")

    lines.append("")
    lines.append("## 유형별 요약")
    if type_buckets:
        for candidate_type, names in sorted(type_buckets.items()):
            lines.append(f"- {candidate_type}: {', '.join(names)}")
    else:
        lines.append("- 해당 없음")

    lines.append("")
    lines.extend(summaries)
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    target_date = args.date or find_latest_date(ROOT_DIR / "analysis_logs")
    if target_date is None:
        print("[FAIL] No analysis logs are available yet.")
        return 1

    report = build_report(target_date)
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
