# 한국투자증권 연결 가이드

## 현재 상태

이 저장소에는 한국투자증권 Open API 연결을 위한 최소 코드가 이미 추가되어 있습니다.

- 환경변수 로더
- 토큰 발급 클라이언트
- 연결 확인 스크립트

## 준비물

아래 정보가 필요합니다.

- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- 모의투자 여부

실전 주문까지 붙일 때는 계좌번호도 함께 넣게 됩니다.

## 환경변수 설정

프로젝트 루트에 `.env`를 만들고 아래 값을 채워주세요.

```env
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_USE_VIRTUAL=true
KIS_ACCOUNT_NO=
KIS_ACCOUNT_PRODUCT_CODE=01
```

기본값은 `모의투자` 기준입니다.

- `true`: 모의투자 서버
- `false`: 실전 서버

## 연결 확인

아래 명령으로 토큰 발급이 되는지 확인합니다.

```bash
.venv/bin/python scripts/kis_check_connection.py
```

성공하면 아래와 비슷한 출력이 나옵니다.

```text
[OK] KIS access token issued successfully.
Environment: virtual
Base URL: https://openapivts.koreainvestment.com:29443
```

## 현재 포함된 파일

- `src/autostocktrading/brokers/kis/config.py`
- `src/autostocktrading/brokers/kis/client.py`
- `scripts/kis_check_connection.py`
- `scripts/kis_quote_check.py`

## 현재가 조회 확인

한투 인증이 된 뒤에는 삼성전자 현재가로 조회 테스트를 할 수 있습니다.

```bash
.venv/bin/python scripts/kis_quote_check.py
```

다른 종목을 조회하려면 아래처럼 종목코드를 넘기면 됩니다.

```bash
.venv/bin/python scripts/kis_quote_check.py --symbol 000660
```

## 다음 단계

연결 확인이 끝나면 아래 순서로 확장하는 것이 좋습니다.

1. 국내주식 현재가 조회
2. 계좌 잔고 조회
3. 모의주문
4. 주문 상태 조회
5. 실시간 시세 구독

## 공식 참고 링크

- [KIS Developers](https://apiportal.koreainvestment.com/intro)
- [API 서비스 개요](https://apiportal.koreainvestment.com/apiservice-summary)
- [제휴/개인고객 안내](https://apiportal.koreainvestment.com/provider)
