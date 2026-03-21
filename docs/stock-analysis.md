# 한국주식 분석 로그

## 목표

기본 감시 종목에 대해 자동주식매매 전 단계의 분석 로그를 날짜별로 누적합니다.

현재 수집기는 아래 데이터를 바탕으로 분석 스냅샷을 저장합니다.

- 현재가, 시가, 고가, 저가, 누적거래량
- PER, PBR, EPS, BPS
- 52주 고가/저가
- 일별 종가 기반 이동평균
- RSI, 거래량 배수, 변동성
- 최근 20일 범위 위치
- 간단한 관찰 신호 (`breakout_watch`, `pullback_watch`)
- 매수 후보 여부와 차단 사유

## 저장 위치

분석 로그는 아래 구조로 쌓입니다.

```text
analysis_logs/
  YYYY-MM-DD/
    kis_analysis/
      005930/
        stocks/
          snapshot.jsonl
      000660/
        stocks/
          snapshot.jsonl
      105560/
        stocks/
          snapshot.jsonl
```

매수 후보 판단 로그는 아래 구조로 함께 쌓입니다.

```text
structured_logs/
  YYYY-MM-DD/
    stock_strategy/
      005930/
        korean_bluechips/
          buy_candidate.jsonl
      000660/
        korean_bluechips/
          buy_candidate.jsonl
```

## 실행

한 번만 수집:

```bash
.venv/bin/python scripts/stock_analysis_collector.py --once
```

5분마다 계속 수집:

```bash
.venv/bin/python scripts/stock_analysis_collector.py
```

## 커스터마이즈

특정 종목만:

```bash
.venv/bin/python scripts/stock_analysis_collector.py --symbols 005930 --once
```

기본 감시 종목:

- `005930` 삼성전자
- `000660` SK하이닉스
- `105560` KB금융
- `207940` 삼성바이오로직스
- `267260` HD현대일렉트릭
- `012450` 한화에어로스페이스
- `017670` SK텔레콤

## 로그 활용 예시

나중에 아래 항목을 기준으로 전략을 조정할 수 있습니다.

- `above_sma_20`, `above_sma_60`
- `sma_20_above_sma_60`
- `volume_ratio_20`
- `rsi_14`
- `range_position_20d_pct`
- `breakout_watch`
- `pullback_watch`
- `buy_candidate`
- `candidate_type`
- `hard_blockers`
- `breakout_blockers`
- `pullback_blockers`

## 참고

- 수집기는 한투 API 토큰을 재사용하도록 구성했습니다.
- 장기 이동평균 계산을 위해 우선 `기간별 차트 조회`를 시도하고, 실패하면 기본 일별 시세로 자동 폴백합니다.
- 현재 규칙은 `korean_bluechips_v1`이며, 기본 감시 종목 전반에 같은 형식의 추세/거래량/RSI/범위 위치를 함께 봅니다.
