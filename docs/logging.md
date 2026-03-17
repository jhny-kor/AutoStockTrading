# 로그 저장과 압축

## 목표

자동매매 운영에서 로그는 날짜별로 수집하고, 일정 기간이 지난 뒤 `tar.gz`로 압축 보관합니다.

현재 저장소에는 아래 흐름이 추가되어 있습니다.

- 날짜별 로그 디렉터리 생성
- JSONL 형식 이벤트 기록
- 오래된 날짜 폴더 `tar.gz` 압축

## 디렉터리 구조

기본 구조는 아래와 같습니다.

```text
logs/
  2026-03-17/
    kis/
      005930/
        market/
          quote.jsonl
    ipo/
      schedule/
        subscription.jsonl
archives/
  logs-2026-03-01.tar.gz
```

## 저장 형식

각 줄은 JSON 한 건인 `JSONL` 형식입니다.

예시:

```json
{"logged_at":"2026-03-17T09:01:00","source":"kis","symbol":"005930","category":"market","event_type":"quote","payload":{"price":"193900"}}
```

## 포함된 파일

- `src/autostocktrading/logs/storage.py`
- `scripts/log_demo_event.py`
- `scripts/archive_old_logs.py`

## 수동 기록 예시

아래 명령으로 샘플 로그를 만들 수 있습니다.

```bash
.venv/bin/python scripts/log_demo_event.py
```

실제 조회 스크립트에서도 바로 로그를 남길 수 있습니다.

```bash
.venv/bin/python scripts/kis_quote_check.py --log
.venv/bin/python scripts/ipo_schedule_check.py --mode today --log
.venv/bin/python scripts/send_ipo_schedule_telegram.py --mode today --log
```

## 오래된 로그 압축

기본적으로 최근 `14일`은 그대로 두고, 그보다 오래된 날짜 폴더만 압축합니다.

```bash
.venv/bin/python scripts/archive_old_logs.py
```

무엇이 압축될지 먼저 보려면:

```bash
.venv/bin/python scripts/archive_old_logs.py --dry-run
```

## 운영 권장안

- `quote`, `strategy`, `order`, `trade`, `error`를 JSONL 또는 텍스트로 분리
- 당일 로그는 압축하지 않음
- 최근 `7~14일`은 바로 열어볼 수 있게 유지
- 그 이전 날짜는 `tar.gz` 압축

## 다음 연결 포인트

- `주문/체결` 응답을 종목별로 저장하기
- 전략 판단 로그를 `strategy.jsonl`로 구조화하기
- 일별 요약 리포트를 별도 JSON 파일로 함께 남기기
