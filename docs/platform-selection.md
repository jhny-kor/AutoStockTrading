# 플랫폼 선택 가이드

## 결론

실전 운영까지 고려한 기본 추천 조합은 아래와 같습니다.

- 한국주식: `한국투자증권 Open API`
- 미국주식: `Interactive Brokers (IBKR)`

빠른 프로토타이핑이 우선이면 아래 조합도 좋습니다.

- 한국주식: `한국투자증권 Open API`
- 미국주식: `Alpaca`

국내 조건검색과 국내 자동매매 커뮤니티 자료를 중시하면 아래 조합도 고려할 수 있습니다.

- 한국주식: `키움 REST API`
- 미국주식: `IBKR`

## 비교 요약

| 구분 | 플랫폼 | 추천도 | 강점 | 주의점 |
| --- | --- | --- | --- | --- |
| 한국주식 | 한국투자증권 Open API | 높음 | 국내/해외주식 모두 공식 지원, REST/WebSocket 제공, 개인 개발자 접근성 우수 | 인증과 호출 규격을 정확히 맞춰야 함 |
| 한국주식 | 키움 REST API | 중상 | 국내 사용자 자료가 많고 조건검색 친화적 | 실전/모의 키 분리, 허용 IP 등록 필요, 모의투자 제약 확인 필요 |
| 미국주식 | IBKR | 높음 | API 성숙도 높음, 실전 안정성 우수, 자산 확장성 좋음 | 초기 설정과 개념이 비교적 복잡함 |
| 미국주식 | Alpaca | 중상 | 페이퍼 트레이딩 진입이 빠름, 개발 경험이 단순함 | 실계좌 사용 가능 국가와 운영 조건 확인 필요 |

## 한국주식 추천

### 1. 한국투자증권 Open API

가장 먼저 붙이기 좋은 한국 브로커입니다.

- `국내주식`과 `해외주식` 주문/계좌 API를 공식 제공
- `REST`와 `WebSocket`을 함께 사용할 수 있어 시세 수신과 주문 처리 분리가 쉬움
- 개인 고객도 개발자센터에서 신청할 수 있어 진입 장벽이 비교적 낮음
- 저장소를 장기적으로 운영할 때 구조화하기 편함

적합한 경우:

- 한국주식과 미국주식을 한 저장소에서 함께 운영하고 싶을 때
- API 문서 기반으로 차분히 시스템화하고 싶을 때
- 추후 운영 자동화와 모니터링을 붙일 계획이 있을 때

공식 링크:

- [KIS Developers](https://apiportal.koreainvestment.com/intro)
- [API 서비스 개요](https://apiportal.koreainvestment.com/apiservice-summary)
- [제휴/개인고객 안내](https://apiportal.koreainvestment.com/provider)

### 2. 키움 REST API

한국 시장 중심으로 깊게 파고들 때 유력한 대안입니다.

- 국내 자동매매 경험담과 예제가 많은 편
- 조건검색 기반 자동매매를 고려할 때 매력적
- 국내 개인 투자자에게 익숙한 플랫폼

주의할 점:

- 실전/모의 App Key를 별도 관리
- 허용 IP 등록 필요
- 모의투자 지원 범위는 공식 문서 기준으로 다시 확인하며 구현해야 함

공식 링크:

- [키움 OpenAPI](https://openapi.kiwoom.com/)
- [서비스 이용안내](https://openapi.kiwoom.com/intro/serviceInfo)
- [API 가이드](https://openapi.kiwoom.com/guide/apiguide)

## 미국주식 추천

### 1. Interactive Brokers (IBKR)

실전 지향이라면 가장 균형이 좋습니다.

- API 성숙도가 높고 운영 사례가 많음
- `Web API`와 `TWS API` 선택지가 있어 전략과 인프라 성격에 맞게 설계 가능
- `paper trading`으로 실전 전 검증 가능
- 미국주식 외 다른 시장과 자산군으로 확장하기 좋음

적합한 경우:

- 실전 안정성과 장기 확장성을 우선할 때
- 포트폴리오가 미국주식에만 머물지 않을 가능성이 있을 때
- 운영 중 장애 대응과 모니터링을 체계적으로 가져가고 싶을 때

공식 링크:

- [IBKR Web API](https://ibkrcampus.com/campus/ibkr-api-page/web-api-trading/)
- [IBKR TWS API](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR Paper Trading](https://ibkrcampus.com/campus/glossary-terms/paper-trading-account/)

### 2. Alpaca

개발 속도를 우선하면 좋은 선택입니다.

- 페이퍼 트레이딩 진입이 빠름
- API 사용 흐름이 비교적 단순함
- 초기 프로토타입과 전략 검증용으로 편함

주의할 점:

- 실계좌 제공 국가와 계좌 개설 가능 여부를 운영 전 확인
- 장기 운영에서는 브로커 안정성, 주문 유형, 운영 정책을 재검토하는 것이 좋음

공식 링크:

- [Alpaca Trading API](https://docs.alpaca.markets/docs/trading-api)
- [Supported Countries](https://alpaca.markets/support/countries-alpaca-is-available)

## 이 저장소 기준 최종 추천

### 기본안

- 한국주식: `한국투자증권 Open API`
- 미국주식: `IBKR`

이 조합은 실전성, 문서 신뢰도, 장기 유지보수성의 균형이 좋습니다.

### 빠른 MVP안

- 한국주식: `한국투자증권 Open API`
- 미국주식: `Alpaca`

이 조합은 초기 개발 속도와 테스트 편의성이 좋습니다.

## Python 기준 추천 기술 스택

권장 구성은 아래와 같습니다.

- API 호출: `httpx` 또는 `requests`
- 실시간 수신: `websockets` 또는 `websocket-client`
- 데이터 처리: `pandas`
- 환경변수 관리: `pydantic-settings` 또는 `python-dotenv`
- 스케줄링: `APScheduler`
- 로그: 표준 `logging` + JSON 로그 포맷
- 저장소: 초기에는 `SQLite`, 운영 단계에서는 `PostgreSQL`

## 설계 원칙

- 브로커별 코드는 `broker adapter`로 분리
- 전략 로직은 브로커 구현과 독립
- 주문 전 리스크 체크를 공통 모듈로 분리
- 모의투자와 실전투자 설정을 완전히 분리
- 비밀키와 계좌정보는 `.env`나 시크릿 스토어로 관리
