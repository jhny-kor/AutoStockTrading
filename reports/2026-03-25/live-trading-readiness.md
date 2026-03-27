# 2026-03-25 실거래 준비 상태

## 현재 설정

- `KIS_USE_VIRTUAL=false`
- `KIS_ALLOW_LIVE_ORDERS=true`
- `KR_LONG_DRY_RUN=true`
- `KR_SHORT_DRY_RUN=false`
- `KR_SHORT_ORDER_BUDGET_KRW=100000`
- `KR_SHORT_MAX_ORDERS_PER_DAY=1`
- `KR_SHORT_MAX_OPEN_CANDIDATES=1`
- `KR_SHORT_ORDER_STYLE=market`

## 해석

- 국장 시세/주문 기준 서버는 `실전 서버`
- 국장 단타 주문 엔진은 `실거래 가능`
- 국장 장타 주문 엔진은 아직 `dry-run 유지`
- 아직 주문 엔진 프로세스는 수동 시작 전이므로 자동으로 주문이 나가지는 않음

## 권장 확인 항목

1. 장중에 `국장 단타 시그널 러너` 후보가 실제로 존재하는지 확인
2. `국장 단타 주문 엔진`을 켜기 전 예산과 횟수 제한이 의도와 맞는지 재확인
3. 텔레그램 알림이 정상인지 확인
4. 첫 실거래는 주문 수량을 작게 유지

## 시작 명령

단타 주문 엔진 수동 1회 실행:

```bash
.venv/bin/python scripts/kr_short_term_trader.py --once
```

단타 주문 엔진 계속 실행:

```bash
.venv/bin/python scripts/kr_short_term_trader.py
```

## 주의

- 이 설정은 `실제 주문`이 가능한 상태입니다.
- 현재는 프로세스를 시작하지 않았기 때문에 즉시 주문은 나가지 않습니다.
