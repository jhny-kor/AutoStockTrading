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

## 추천 방향

이 저장소는 아래 방향으로 시작하는 것을 권장합니다.

1. 한국과 미국 브로커를 각각 어댑터로 분리합니다.
2. 전략 로직은 브로커 구현과 독립적으로 유지합니다.
3. 실전 계좌 연결 전에는 모의투자 또는 페이퍼 트레이딩으로 충분히 검증합니다.
4. 주문, 체결, 잔고, 에러 로그를 반드시 별도 저장합니다.

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
