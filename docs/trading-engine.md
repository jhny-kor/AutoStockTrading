# 국장 주문 엔진

## 개요

국장 장타와 단타는 서로 다른 프로그램으로 주문할 수 있게 분리되어 있습니다.

- 장타 시그널 러너: `scripts/kr_long_term_runner.py`
- 단타 시그널 러너: `scripts/kr_short_term_runner.py`
- 장타 주문 엔진: `scripts/kr_long_term_trader.py`
- 단타 주문 엔진: `scripts/kr_short_term_trader.py`

## 중요한 점

현재 구현은 `실거래 가능` 상태지만, 기본값은 `dry-run`입니다.

즉:

- 기본 실행: 주문 판단만 하고 실제 주문은 보내지 않음
- 실거래 활성화 후 실행: 실제 한투 주문 API 전송

## 실거래 활성화 방법

`.env`에서 아래 두 조건이 모두 필요합니다.

```env
KIS_USE_VIRTUAL=false
KIS_ALLOW_LIVE_ORDERS=true
```

그리고 전략별 `DRY_RUN`도 꺼야 합니다.

```env
KR_LONG_DRY_RUN=false
KR_SHORT_DRY_RUN=false
```

## 전략별 주문 설정

예시:

```env
KR_LONG_ORDER_BUDGET_KRW=500000
KR_LONG_MAX_ORDERS_PER_DAY=2
KR_LONG_MAX_OPEN_CANDIDATES=2
KR_LONG_ORDER_STYLE=market

KR_SHORT_ORDER_BUDGET_KRW=300000
KR_SHORT_MAX_ORDERS_PER_DAY=3
KR_SHORT_MAX_OPEN_CANDIDATES=3
KR_SHORT_ORDER_STYLE=market
```

## 수동 실행

장타 주문 엔진:

```bash
.venv/bin/python scripts/kr_long_term_trader.py --once
```

단타 주문 엔진:

```bash
.venv/bin/python scripts/kr_short_term_trader.py --once
```

## 현재 동작

- shared analysis log를 읽음
- 장타/단타 시그널 로그를 읽음
- 후보 종목이 있으면 예산 기준 수량 계산
- dry-run이면 simulated 주문 로그만 남김
- live 조건이 모두 맞으면 한투 `order-cash`로 주문 전송

## 로그

주문 엔진 결과는 아래에 남습니다.

```text
trade_logs/YYYY-MM-DD/kr_long_term/<symbol>/orders/buy_entry.jsonl
trade_logs/YYYY-MM-DD/kr_short_term/<symbol>/orders/buy_entry.jsonl
```
