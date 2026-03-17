# 공모주 일정 텔레그램 알림

## 결론

가능합니다.

현재 저장소에는 아래 흐름이 추가되어 있습니다.

1. `공모주 청약일정` 수집
2. 텔레그램 메시지 포맷 생성
3. 텔레그램 Bot API 전송

## 데이터 소스 판단

공식 KIND 페이지는 브라우저에서는 확인되지만, 스크립트 접근 시 오류 페이지가 내려오는 경우가 있어 자동 수집에는 다소 까다롭습니다.

반면 `38커뮤니케이션 공모주 청약일정` 페이지는 프로그램으로 HTML 테이블을 읽을 수 있음을 확인했습니다.

그래서 현재 구현은 아래 방식을 사용합니다.

- 수집: `38커뮤니케이션 공모주 청약일정`
- 검증: 필요 시 `KIND` 수동 확인

## 사용 파일

- `src/autostocktrading/services/ipo_schedule.py`
- `src/autostocktrading/notifications/telegram.py`
- `scripts/ipo_schedule_check.py`
- `scripts/send_ipo_schedule_telegram.py`

## 먼저 확인만 하기

아래 명령으로 공모주 청약일정을 콘솔에서 먼저 확인할 수 있습니다.

```bash
.venv/bin/python scripts/ipo_schedule_check.py
```

## 텔레그램 전송 설정

`.env`에 아래 값을 추가합니다.

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 텔레그램 전송

```bash
.venv/bin/python scripts/send_ipo_schedule_telegram.py
```

오늘 시작하는 청약만 보내려면 아래처럼 실행합니다.

```bash
.venv/bin/python scripts/send_ipo_schedule_telegram.py --mode today
```

해당 주간에 시작하는 청약만 보내려면 아래처럼 실행합니다.

```bash
.venv/bin/python scripts/send_ipo_schedule_telegram.py --mode this-week
```

## 참고

- 현재 구현은 `가까운 공모주 청약 일정`을 텔레그램용 텍스트로 묶어 보냅니다.
- 실제 운영에서는 아침 1회 또는 청약 시작일 당일만 보내도록 스케줄링하는 것이 좋습니다.
- `38커뮤니케이션` 데이터는 비공식 공개 페이지이므로, 중요한 일정은 청약 전 최종 확인이 필요합니다.
