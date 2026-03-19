# 프로세스 관리

## 목표

`auto_coin_bot`처럼 한국주식 분석 수집기를 백그라운드 프로세스로 관리합니다.

현재는 아래 구성을 사용합니다.

- `bot_manager.py`
- `scripts/autostart_all.sh`
- `launchd/com.plo.autostockbot.startall.plist`

## 가능한 명령

상태 확인:

```bash
.venv/bin/python bot_manager.py status
```

분석 수집기 시작:

```bash
.venv/bin/python bot_manager.py start collector
```

전체 시작:

```bash
.venv/bin/python bot_manager.py start all
```

중지:

```bash
.venv/bin/python bot_manager.py stop
```

강제 중지:

```bash
.venv/bin/python bot_manager.py stop --force
```

## 로그

프로세스 표준 출력과 표준 에러는 날짜별로 아래 경로에 저장됩니다.

```text
logs/YYYY-MM-DD/stock_analysis_collector.stdout.log
logs/YYYY-MM-DD/stock_analysis_collector.stderr.log
logs/YYYY-MM-DD/stock_analysis_collector.launcher.log
```

분석 결과는 기존과 동일하게 아래에 쌓입니다.

```text
analysis_logs/YYYY-MM-DD/...
structured_logs/YYYY-MM-DD/...
```

## launchd

부팅 시 자동 시작까지 원하면 아래 plist를 사용할 수 있습니다.

- `launchd/com.plo.autostockbot.startall.plist`

일반적인 설치 예시:

```bash
cp launchd/com.plo.autostockbot.startall.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.plo.autostockbot.startall.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.plo.autostockbot.startall.plist
```
