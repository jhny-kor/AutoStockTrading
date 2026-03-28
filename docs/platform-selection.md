# 플랫폼 선택 가이드

## 결론

실전 운영까지 고려한 기본 추천 조합은 아래와 같습니다.

- 한국주식: `한국투자증권 Open API`
- 미국주식: `한국투자증권 해외주식 Open API`

빠른 프로토타이핑이 우선이면 아래 조합도 좋습니다.

- 한국주식: `한국투자증권 Open API`
- 미국주식: `한국투자증권 해외주식 Open API`

## 비교 요약

| 구분 | 플랫폼 | 추천도 | 강점 | 주의점 |
| --- | --- | --- | --- | --- |
| 한국주식 | 한국투자증권 Open API | 높음 | 국내/해외주식 모두 공식 지원, REST/WebSocket 제공, 개인 개발자 접근성 우수 | 인증과 호출 규격을 정확히 맞춰야 함 |
| 한국주식 | 키움 REST API | 중상 | 국내 사용자 자료가 많고 조건검색 친화적 | 실전/모의 키 분리, 허용 IP 등록 필요, 모의투자 제약 확인 필요 |
| 미국주식 | 한국투자증권 해외주식 Open API | 높음 | 같은 계좌 체계로 국장/미장 운영 가능, 공식 주문/계좌 API 제공 | 해외주식 권한과 환전/주문 세션을 함께 확인해야 함 |

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

### 1. 한국투자증권 해외주식 Open API

현재 저장소 기준으로는 가장 일관성이 좋습니다.

- 국장과 같은 증권사/계좌 체계로 운영 가능
- `해외주식 주문/계좌`, `기본시세`, `실시간시세`가 공식 서비스 목록에 포함됨
- 국장 로직과 공통 구조를 재사용하기 좋음

적합한 경우:

- 국장과 미장을 같은 저장소에서 같이 관리하고 싶을 때
- 브로커 수를 늘리지 않고 한 계열 API로 통합하고 싶을 때
- 실거래 운영 복잡도를 줄이고 싶을 때

공식 링크:

- [KIS Developers](https://apiportal.koreainvestment.com/intro)
- [API 서비스 개요](https://apiportal.koreainvestment.com/apiservice-summary)

## 이 저장소 기준 최종 추천

### 기본안

- 한국주식: `한국투자증권 Open API`
- 미국주식: `한국투자증권 해외주식 Open API`

이 조합은 국장/미장을 같은 계좌 체계와 코드 구조로 가져가기 좋습니다.

### 빠른 MVP안

- 한국주식: `한국투자증권 Open API`
- 미국주식: `한국투자증권 해외주식 Open API`

이 조합은 브로커를 분리하지 않아 구현 복잡도가 낮습니다.

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
