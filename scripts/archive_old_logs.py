"""Archive dated log directories into tar.gz files."""

from __future__ import annotations

import argparse
from datetime import date
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.logs import LogDirectoryManager, archive_old_log_directories  # noqa: E402


def parse_iso_date(raw: str) -> date:
    return date.fromisoformat(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Archive old dated logs into tar.gz files.")
    parser.add_argument(
        "--keep-days",
        type=int,
        default=14,
        help="Keep this many recent days unarchived. Default: 14",
    )
    parser.add_argument(
        "--today",
        type=parse_iso_date,
        help="Override the current date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which archives would be created without writing them.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing archives if they already exist.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manager = LogDirectoryManager(
        log_root=ROOT_DIR / "logs",
        archive_root=ROOT_DIR / "archives",
    )

    try:
        archived = archive_old_log_directories(
            manager=manager,
            keep_days=args.keep_days,
            today=args.today,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[FAIL] Log archival failed: {exc}")
        return 1

    if not archived:
        print("[OK] No log directories needed archival.")
        return 0

    if args.dry_run:
        print("[OK] Dry run only. These archives would be created:")
    else:
        print("[OK] Archived log directories:")

    for archive_path in archived:
        print(f"- {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
