# 국장 전략 정리

## 구조

국장은 공통 수집기 위에 `장타`와 `단타` 전략을 따로 올리는 구조입니다.

- 공통 수집기: `scripts/stock_analysis_collector.py`
- 장타 시그널 러너: `scripts/kr_long_term_runner.py`
- 단타 시그널 러너: `scripts/kr_short_term_runner.py`
- 장타 주문 엔진: `scripts/kr_long_term_trader.py`
- 단타 주문 엔진: `scripts/kr_short_term_trader.py`

## 장타 전략

전략 이름:

- `kr_long_term_v1`

핵심 목적:

- 가치와 배당을 같이 보면서 추세가 완전히 꺾이지 않은 종목의 `회복 구간` 진입

주요 판단 기준:

- `20일선` 위
- `20일선 > 60일선`
- `RSI`가 과열이 아닌 구간
- `20일선`에서 너무 멀지 않은 가격
- `PER/PBR`이 과도하지 않은지 확인
- 급락일은 피함

장점:

- 추격 매수보다 눌림/회복 구간을 노림
- 밸류와 추세를 함께 보므로 장기 보유 논리가 비교적 명확함

주의점:

- 성장주에서는 `PER/PBR` 조건 때문에 후보가 줄 수 있음
- 강한 주도주 초입은 놓칠 수 있음

## 단타 전략

전략 이름:

- `kr_short_term_v1`

핵심 목적:

- 장중 혹은 단기 스윙 관점에서 `돌파` 또는 `짧은 눌림` 구간 진입

주요 판단 기준:

- `20일선` 위 여부
- `거래량 배수`
- `RSI`
- `20일 범위 위치`
- 당일 모멘텀과 최근 5일 흐름

세부 유형:

- `short_breakout`
- `short_pullback`

장점:

- 거래량과 단기 모멘텀을 더 중시해서 빠른 진입 판단에 적합

주의점:

- 뉴스 한 건에도 신호가 크게 흔들릴 수 있음
- 중소형주는 슬리피지와 변동성이 큼

## watchlist 분리

전략과 종목군은 분리되어 있습니다.

- 대형주 watchlist
- 중형주 watchlist
- 소형주 watchlist
- 장타용 심볼 세트
- 단타용 심볼 세트

즉:

- 새로운 종목 추가 가능
- 장타용만 추가 가능
- 단타용만 추가 가능
- 전략 교체 가능

## 지금 확인할 파일

- 전략 구현: `src/autostocktrading/strategies/`
- 전략 심볼 구성: `src/autostocktrading/config/kr_strategy_watchlists.py`
- 공통 감시 리스트: `src/autostocktrading/config/watchlist.py`
