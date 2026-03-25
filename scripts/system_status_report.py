"""Write a Markdown system status snapshot for the stock bot."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import bot_manager  # noqa: E402


def latest_files(pattern: str, limit: int = 8) -> list[Path]:
    return sorted(ROOT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def build_status_markdown() -> str:
    lines: list[str] = [
        "# 시스템 상태",
        "",
        f"- 생성시각: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 프로세스 상태",
        "```text",
        "\n".join(bot_manager.build_status_lines(use_color=False)),
        "```",
        "",
        "## 최근 분석 로그",
    ]

    analysis_files = latest_files("analysis_logs/*/kis_analysis/*/stocks/snapshot.jsonl")
    if analysis_files:
        lines.extend([f"- {path}" for path in analysis_files[:8]])
    else:
        lines.append("- 없음")

    lines.extend(["", "## 최근 전략 로그"])
    strategy_files = latest_files("structured_logs/*/*/*/*/*.jsonl")
    if strategy_files:
        lines.extend([f"- {path}" for path in strategy_files[:8]])
    else:
        lines.append("- 없음")

    lines.extend(["", "## 최근 주문 로그"])
    trade_files = latest_files("trade_logs/*/*/*/*.jsonl")
    if trade_files:
        lines.extend([f"- {path}" for path in trade_files[:8]])
    else:
        lines.append("- 없음")

    return "\n".join(lines)


def main() -> int:
    report = build_status_markdown()
    report_dir = ROOT_DIR / "reports" / datetime.now().date().isoformat()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "system-status.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print("")
    print(f"[OK] Report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
