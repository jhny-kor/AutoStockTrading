"""
한국주식 분석 수집기 프로세스 관리 도구

- 분석 수집기 상태 확인
- 백그라운드 시작
- 정상 종료 및 강제 종료
- launchd 자동 시작과 함께 사용할 수 있는 진입점 제공

가능한 명령
- .venv/bin/python bot_manager.py status
- .venv/bin/python bot_manager.py start all
- .venv/bin/python bot_manager.py start collector
- .venv/bin/python bot_manager.py stop
- .venv/bin/python bot_manager.py stop all
- .venv/bin/python bot_manager.py stop collector
- .venv/bin/python bot_manager.py stop --force
- .venv/bin/python bot_manager.py stop collector --force
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
}

SECTION_TITLES = {
    "collector": "한국주식 분석 수집기",
}

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CYAN = "\033[36m"


@dataclass
class ManagedProcess:
    name: str
    script: str
    pid: int
    ppid: int
    elapsed: str
    command: str


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
    result = subprocess.run(
        ["ps", "-Ao", "pid=,ppid=,etime=,command="],
        capture_output=True,
        text=True,
        check=True,
    )
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

    return processes


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

    print(f"{name} 시작 요청 완료 (PID {process.pid})")
    print(f"- stdout: {stdout_path}")
    print(f"- stderr: {stderr_path}")
    return 0


def handle_start(target: str) -> int:
    if target == "all":
        return start_program("collector")
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
        choices=["all", "collector"],
        help="시작할 대상",
    )

    stop_parser = subparsers.add_parser("stop", help="실행 중인 프로세스를 종료합니다.")
    stop_parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", "collector"],
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
