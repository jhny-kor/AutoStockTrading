# 시스템 상태

- 생성시각: 2026-03-25T14:04:03

## 프로세스 상태
```text
한국주식 자동매매 프로세스 상태
==================================================
안내: 프로세스 목록 조회 권한이 없어 PID 파일 기준 상태를 표시합니다.

[한국주식 분석 수집기]
  상태: 실행 중 1개  스크립트: scripts/stock_analysis_collector.py
  - PID 79567 | PPID 0 | 실행시간 ?

[국장 장타 시그널 러너]
  상태: 실행 중 1개  스크립트: scripts/kr_long_term_runner.py
  - PID 38367 | PPID 0 | 실행시간 ?

[국장 단타 시그널 러너]
  상태: 실행 중 1개  스크립트: scripts/kr_short_term_runner.py
  - PID 38369 | PPID 0 | 실행시간 ?

[국장 장타 주문 엔진]
  상태: 중지됨  스크립트: scripts/kr_long_term_trader.py

[국장 단타 주문 엔진]
  상태: 중지됨  스크립트: scripts/kr_short_term_trader.py

[일일 리포트 스케줄러]
  상태: 실행 중 1개  스크립트: scripts/daily_report_scheduler.py
  - PID 3929 | PPID 0 | 실행시간 ?

[중요 공시 감시기]
  상태: 실행 중 1개  스크립트: scripts/important_disclosure_watcher.py
  - PID 79576 | PPID 0 | 실행시간 ?
```

## 최근 분석 로그
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/017670/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/012450/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/267260/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/207940/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/105560/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/000660/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/005930/stocks/snapshot.jsonl
- /Users/plo/Documents/auto_stock_bot/analysis_logs/2026-03-25/kis_analysis/214450/stocks/snapshot.jsonl

## 최근 전략 로그
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/stock_strategy/017670/korean_bluechips/buy_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/stock_strategy/012450/korean_bluechips/buy_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/stock_strategy/267260/korean_bluechips/buy_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/stock_strategy/207940/korean_bluechips/buy_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/stock_strategy/105560/korean_bluechips/buy_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/kr_long_term/000660/long_term/entry_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/kr_long_term/005930/long_term/entry_candidate.jsonl
- /Users/plo/Documents/auto_stock_bot/structured_logs/2026-03-25/kr_short_term/000660/short_term/entry_candidate.jsonl

## 최근 주문 로그
- 없음