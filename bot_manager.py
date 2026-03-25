"""
한국주식 자동매매 보조 프로세스 관리 도구

- 분석 수집기, 리포트 스케줄러, 공시 감시기 상태 확인
- 백그라운드 시작
- 정상 종료 및 강제 종료
- launchd 자동 시작과 함께 사용할 수 있는 진입점 제공

가능한 명령
- .venv/bin/python bot_manager.py status
- .venv/bin/python bot_manager.py start all
- .venv/bin/python bot_manager.py start collector
- .venv/bin/python bot_manager.py start kr_long
- .venv/bin/python bot_manager.py start kr_short
- .venv/bin/python bot_manager.py start kr_long_trade
- .venv/bin/python bot_manager.py start kr_short_trade
- .venv/bin/python bot_manager.py start reporter
- .venv/bin/python bot_manager.py start disclosure
- .venv/bin/python bot_manager.py stop
- .venv/bin/python bot_manager.py stop all
- .venv/bin/python bot_manager.py stop collector
- .venv/bin/python bot_manager.py stop kr_long
- .venv/bin/python bot_manager.py stop kr_short
- .venv/bin/python bot_manager.py stop kr_long_trade
- .venv/bin/python bot_manager.py stop kr_short_trade
- .venv/bin/python bot_manager.py stop reporter
- .venv/bin/python bot_manager.py stop disclosure
- .venv/bin/python bot_manager.py stop --force
- .venv/bin/python bot_manager.py stop collector --force
- .venv/bin/python bot_manager.py stop kr_long --force
- .venv/bin/python bot_manager.py stop kr_short --force
- .venv/bin/python bot_manager.py stop kr_long_trade --force
- .venv/bin/python bot_manager.py stop kr_short_trade --force
- .venv/bin/python bot_manager.py stop reporter --force
- .venv/bin/python bot_manager.py stop disclosure --force
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime


PROGRAMS = {
    "collector": "scripts/stock_analysis_collector.py",
    "kr_long": "scripts/kr_long_term_runner.py",
    "kr_short": "scripts/kr_short_term_runner.py",
    "kr_long_trade": "scripts/kr_long_term_trader.py",
    "kr_short_trade": "scripts/kr_short_term_trader.py",
    "reporter": "scripts/daily_report_scheduler.py",
    "disclosure": "scripts/important_disclosure_watcher.py",
}

SECTION_TITLES = {
    "collector": "한국주식 분석 수집기",
    "kr_long": "국장 장타 시그널 러너",
    "kr_short": "국장 단타 시그널 러너",
    "kr_long_trade": "국장 장타 주문 엔진",
    "kr_short_trade": "국장 단타 주문 엔진",
    "reporter": "일일 리포트 스케줄러",
    "disclosure": "중요 공시 감시기",
}

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
PROCESS_LIST_WARNING: str | None = None
PID_DIR = Path("logs") / "pids"


@dataclass
class ManagedProcess:
    name: str
    script: str
    pid: int
    ppid: int
    elapsed: str
    command: str


def pid_file_path(name: str) -> Path:
    return PID_DIR / f"{name}.pid"


def is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_pid_file(name: str) -> int | None:
    path = pid_file_path(name)
    if not path.exists():
        return None

    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def write_pid_file(name: str, pid: int) -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    pid_file_path(name).write_text(str(pid), encoding="utf-8")


def remove_pid_file(name: str) -> None:
    path = pid_file_path(name)
    try:
        path.unlink()
    except FileNotFoundError:
        return


def build_pidfile_fallback_processes(exclude_current: bool = True) -> list[ManagedProcess]:
    current_pid = os.getpid()
    processes: list[ManagedProcess] = []

    for name, script in PROGRAMS.items():
        pid = read_pid_file(name)
        if pid is None:
            continue
        if exclude_current and pid == current_pid:
            continue
        if not is_pid_alive(pid):
            remove_pid_file(name)
            continue

        processes.append(
            ManagedProcess(
                name=name,
                script=script,
                pid=pid,
                ppid=0,
                elapsed="?",
                command=f"{script} (pidfile)",
            )
        )

    return processes


def merge_with_pidfile_processes(
    processes: list[ManagedProcess],
    exclude_current: bool = True,
) -> list[ManagedProcess]:
    by_name = {proc.name: proc for proc in processes}
    for proc in build_pidfile_fallback_processes(exclude_current=exclude_current):
        by_name.setdefault(proc.name, proc)
    return list(by_name.values())


def command_matches_script(command: str, script: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    script_name = Path(script).name
    for token in tokens:
        if Path(token).name == script_name:
            return True
    return False


def color_text(text: str, color: str, bold: bool = False) -> str:
    prefix = color
    if bold:
        prefix = BOLD + color
    return f"{prefix}{text}{RESET}"


def dated_log_path(filename: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    path = Path("logs") / today / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def list_managed_processes(exclude_current: bool = True) -> list[ManagedProcess]:
    global PROCESS_LIST_WARNING
    PROCESS_LIST_WARNING = None

    try:
        result = subprocess.run(
            ["ps", "-Ao", "pid=,ppid=,etime=,command="],
            capture_output=True,
            text=True,
            check=True,
        )
    except PermissionError:
        PROCESS_LIST_WARNING = (
            "프로세스 목록 조회 권한이 없어 PID 파일 기준 상태를 표시합니다."
        )
        return build_pidfile_fallback_processes(exclude_current=exclude_current)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        PROCESS_LIST_WARNING = (
            "프로세스 목록 조회에 실패해 PID 파일 기준 상태를 표시합니다."
            if not stderr
            else f"프로세스 목록 조회에 실패해 PID 파일 기준 상태를 표시합니다: {stderr}"
        )
        return build_pidfile_fallback_processes(exclude_current=exclude_current)

    current_pid = os.getpid()
    processes: list[ManagedProcess] = []

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split(None, 3)
        if len(parts) != 4:
            continue

        pid_text, ppid_text, elapsed, command = parts
        pid = int(pid_text)
        if exclude_current and pid == current_pid:
            continue

        for name, script in PROGRAMS.items():
            if command_matches_script(command, script):
                processes.append(
                    ManagedProcess(
                        name=name,
                        script=script,
                        pid=pid,
                        ppid=int(ppid_text),
                        elapsed=elapsed,
                        command=command,
                    )
                )
                break

    active_names = {proc.name for proc in processes}
    for proc in processes:
        write_pid_file(proc.name, proc.pid)
    for name in PROGRAMS:
        if name not in active_names:
            remove_pid_file(name)

    return merge_with_pidfile_processes(processes, exclude_current=exclude_current)


def get_processes_by_name(name: str) -> list[ManagedProcess]:
    return [proc for proc in list_managed_processes() if proc.name == name]


def build_status_lines(use_color: bool = True) -> list[str]:
    processes = list_managed_processes()
    lines: list[str] = []
    header = "한국주식 자동매매 프로세스 상태"
    separator = "=" * 50

    if use_color:
        lines.append(color_text(header, CYAN, bold=True))
        lines.append(color_text(separator, CYAN))
    else:
        lines.append(header)
        lines.append(separator)

    if PROCESS_LIST_WARNING:
        warning_text = (
            color_text(f"안내: {PROCESS_LIST_WARNING}", YELLOW, bold=True)
            if use_color
            else f"안내: {PROCESS_LIST_WARNING}"
        )
        lines.append(warning_text)

    for name, script in PROGRAMS.items():
        matched = [proc for proc in processes if proc.name == name]
        section_title = SECTION_TITLES.get(name, name)

        lines.append("")
        if use_color:
            lines.append(color_text(f"[{section_title}]", BLUE, bold=True))
        else:
            lines.append(f"[{section_title}]")

        if not matched:
            status_text = color_text("중지됨", RED, bold=True) if use_color else "중지됨"
            lines.append(f"  상태: {status_text}  스크립트: {script}")
            continue

        status_text = (
            color_text(f"실행 중 {len(matched)}개", GREEN, bold=True)
            if use_color
            else f"실행 중 {len(matched)}개"
        )
        lines.append(f"  상태: {status_text}  스크립트: {script}")
        for proc in matched:
            lines.append(f"  - PID {proc.pid} | PPID {proc.ppid} | 실행시간 {proc.elapsed}")

    return lines


def print_status() -> None:
    print("\n".join(build_status_lines(use_color=True)))


def start_program(name: str) -> int:
    if name not in PROGRAMS:
        print(f"알 수 없는 프로그램 이름입니다: {name}")
        return 1

    existing = get_processes_by_name(name)
    if existing:
        print(f"{name} 는 이미 실행 중입니다.")
        for proc in existing:
            print(f"- PID {proc.pid} / {proc.command}")
        return 0

    script = PROGRAMS[name]
    stdout_path = dated_log_path(f"{Path(script).stem}.stdout.log")
    stderr_path = dated_log_path(f"{Path(script).stem}.stderr.log")
    launcher_log = dated_log_path(f"{Path(script).stem}.launcher.log")

    with (
        stdout_path.open("a", encoding="utf-8") as stdout_handle,
        stderr_path.open("a", encoding="utf-8") as stderr_handle,
        launcher_log.open("a", encoding="utf-8") as launcher_handle,
    ):
        launcher_handle.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] start requested\n"
        )
        launcher_handle.flush()
        process = subprocess.Popen(
            [sys.executable, script],
            cwd=os.getcwd(),
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )

    write_pid_file(name, process.pid)
    print(f"{name} 시작 요청 완료 (PID {process.pid})")
    print(f"- stdout: {stdout_path}")
    print(f"- stderr: {stderr_path}")
    return 0


def handle_start(target: str) -> int:
    if target == "all":
        codes = [
            start_program(name)
            for name in (
                "collector",
                "kr_long",
                "kr_short",
                "kr_long_trade",
                "kr_short_trade",
                "reporter",
                "disclosure",
            )
        ]
        return 0 if all(code == 0 for code in codes) else 1
    return start_program(target)


def stop_processes(processes: list[ManagedProcess], force: bool = False) -> int:
    if not processes:
        print("중지할 프로세스가 없습니다.")
        return 0

    signal_type = signal.SIGKILL if force else signal.SIGTERM
    signal_name = "SIGKILL" if force else "SIGTERM"
    print(f"{len(processes)}개 프로세스에 {signal_name} 신호를 보냅니다.")

    for proc in processes:
        try:
            os.kill(proc.pid, signal_type)
            print(f"- {proc.name} PID {proc.pid} 종료 신호 전송 완료")
        except ProcessLookupError:
            print(f"- {proc.name} PID {proc.pid} 는 이미 종료되어 있습니다.")
        except PermissionError:
            print(f"- {proc.name} PID {proc.pid} 종료 권한이 없습니다.")

    return 0


def wait_for_exit(timeout_sec: float = 3.0) -> list[ManagedProcess]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        remaining = list_managed_processes()
        if not remaining:
            return []
        time.sleep(0.3)
    return list_managed_processes()


def handle_stop(target: str = "all", force: bool = False) -> int:
    processes = list_managed_processes() if target == "all" else get_processes_by_name(target)
    print_status()
    stop_processes(processes, force=force)

    if not force and processes:
        remaining = wait_for_exit()
        if target != "all":
            remaining = [proc for proc in remaining if proc.name == target]
        if remaining:
            print()
            print("일부 프로세스가 아직 남아 있습니다. 필요하면 --force 옵션을 사용하세요.")
            print_status()
            return 1

    remaining = list_managed_processes()
    if target != "all":
        remaining = [proc for proc in remaining if proc.name == target]

    print()
    if remaining:
        print("아직 실행 중인 관리 대상 프로세스가 남아 있습니다.")
        print_status()
        return 1

    if target == "all":
        for name in PROGRAMS:
            remove_pid_file(name)
    else:
        remove_pid_file(target)

    if target == "all":
        print("모든 관리 대상 프로세스가 중지되었습니다.")
    else:
        print(f"{target} 관리 대상 프로세스가 중지되었습니다.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="한국주식 자동매매 프로세스 관리 도구")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="현재 실행 상태를 확인합니다.")

    start_parser = subparsers.add_parser("start", help="프로세스를 시작합니다.")
    start_parser.add_argument(
        "target",
        choices=["all", "collector", "kr_long", "kr_short", "kr_long_trade", "kr_short_trade", "reporter", "disclosure"],
        help="시작할 대상",
    )

    stop_parser = subparsers.add_parser("stop", help="실행 중인 프로세스를 종료합니다.")
    stop_parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", "collector", "kr_long", "kr_short", "kr_long_trade", "kr_short_trade", "reporter", "disclosure"],
        help="중지할 대상 (기본값: all)",
    )
    stop_parser.add_argument(
        "--force",
        action="store_true",
        help="일반 종료가 안 되면 강제 종료합니다.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        print_status()
        return 0
    if args.command == "start":
        return handle_start(args.target)
    if args.command == "stop":
        return handle_stop(target=args.target, force=args.force)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
