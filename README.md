# AutoStockTrading

`AutoStockTrading`은 한국주식과 미국주식을 모두 자동매매할 수 있는 시스템을 목표로 하는 저장소입니다.

현재 기준 추천 조합은 아래와 같습니다.

- 한국주식: `한국투자증권 Open API`
- 미국주식: `Interactive Brokers (IBKR)`

개발 속도를 우선하면 아래 조합도 유효합니다.

- 한국주식: `한국투자증권 Open API`
- 미국주식: `Alpaca`

## 문서

- [플랫폼 선택 가이드](./docs/platform-selection.md)
- [구현 로드맵](./docs/implementation-roadmap.md)
- [한국투자증권 연결 가이드](./docs/kis-setup.md)
- [공모주 일정 텔레그램 알림](./docs/ipo-telegram.md)

## 추천 방향

이 저장소는 아래 방향으로 시작하는 것을 권장합니다.

1. 한국과 미국 브로커를 각각 어댑터로 분리합니다.
2. 전략 로직은 브로커 구현과 독립적으로 유지합니다.
3. 실전 계좌 연결 전에는 모의투자 또는 페이퍼 트레이딩으로 충분히 검증합니다.
4. 주문, 체결, 잔고, 에러 로그를 반드시 별도 저장합니다.

## 빠른 시작

한국주식은 현재 `한국투자증권 Open API`부터 연결할 수 있는 최소 코드가 준비되어 있습니다.

1. `.env.example`을 참고해 `.env`를 만듭니다.
2. `KIS_APP_KEY`, `KIS_APP_SECRET`를 채웁니다.
3. `.venv`를 만들고 활성화합니다.
4. `.venv/bin/python scripts/kis_check_connection.py`로 토큰 발급이 되는지 확인합니다.
5. `.venv/bin/python scripts/kis_quote_check.py`로 현재가 조회를 확인합니다.
6. `.venv/bin/python scripts/ipo_schedule_check.py`로 공모주 청약일정을 확인합니다.

## 초기 폴더 제안

아직 코드는 비어 있으므로 아래 구조로 시작하면 관리가 쉽습니다.

```text
AutoStockTrading/
  docs/
  src/
    brokers/
    strategies/
    services/
    backtest/
    config/
  tests/
  scripts/
```

## 공식 참고 링크

- 한국투자증권 개발자센터: [KIS Developers](https://apiportal.koreainvestment.com/intro)
- 키움 OpenAPI: [Kiwoom OpenAPI](https://openapi.kiwoom.com/)
- IBKR API: [IBKR Campus API](https://ibkrcampus.com/campus/ibkr-api-page/)
- Alpaca Trading API: [Alpaca Docs](https://docs.alpaca.markets/docs/trading-api)
