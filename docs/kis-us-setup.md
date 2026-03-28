# 한투 해외주식(미장) 가이드

## 목표

미장은 `한국투자증권 해외주식 Open API`로 국장과 분리해서 운영합니다.

현재 시작 종목:

- `AAPL`
- `TSLA`

## 포함된 파일

- `src/autostocktrading/brokers/kis/overseas.py`
- `scripts/kis_us_quote_check.py`
- `scripts/kis_us_balance_check.py`
- `scripts/kis_us_daytime_order_test.py`
- `scripts/us_stock_analysis_collector.py`
- `scripts/us_long_term_runner.py`
- `scripts/us_short_term_runner.py`
- `scripts/us_long_term_trader.py`
- `scripts/us_short_term_trader.py`

## 연결 확인

현재가 확인:

```bash
.venv/bin/python scripts/kis_us_quote_check.py --exchange NAS --symbol AAPL
```

잔고 확인:

```bash
.venv/bin/python scripts/kis_us_balance_check.py --exchange NASD --currency USD
```

## 수집/시그널/주문

분석 수집:

```bash
.venv/bin/python scripts/us_stock_analysis_collector.py --once
```

장타 시그널:

```bash
.venv/bin/python scripts/us_long_term_runner.py --once
```

단타 시그널:

```bash
.venv/bin/python scripts/us_short_term_runner.py --once
```

장타 주문 엔진:

```bash
.venv/bin/python scripts/us_long_term_trader.py --once
```

단타 주문 엔진:

```bash
.venv/bin/python scripts/us_short_term_trader.py --once
```

## 해외주식 주문 테스트

지정가 1주 테스트:

```bash
.venv/bin/python scripts/kis_us_daytime_order_test.py --exchange NASD --symbol AAPL --side BUY --qty 1 --price 150
```

## 주의

- 현재 미장 모듈은 한투 해외주식 API를 사용합니다.
- 실거래 전에는 국장과 마찬가지로 소액 주문부터 확인하는 것이 맞습니다.
