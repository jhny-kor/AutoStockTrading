# 뉴스와 공시 수집

## 가능 여부

가능합니다.

다만 안정성과 신뢰도 기준으로는 `공시`를 먼저 공식 소스로 붙이는 것이 좋습니다.

- 공시: `OpenDART` 공식 API 사용 가능
- 뉴스: 포털 기사 수집 또는 기업 IR 뉴스 페이지 수집 가능

## 현재 포함된 것

이 저장소에는 `OpenDART` 기반 공시 수집 스크립트가 추가되어 있습니다.

- `src/autostocktrading/services/disclosures.py`
- `scripts/disclosure_check.py`

추가 키 없이 사용할 수 있는 뉴스 수집 스크립트도 포함되어 있습니다.

- `src/autostocktrading/services/news.py`
- `scripts/news_check.py`

## OpenDART 준비

`.env`에 아래 값을 추가합니다.

```env
DART_API_KEY=your_opendart_api_key
```

OpenDART 공식 안내:

- [OpenDART 소개](https://opendart.fss.or.kr/intro/main.do)
- [공시검색 API 가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)
- [고유번호 API 가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019018)

## 공시 수집 실행

최근 7일 공시 확인:

```bash
.venv/bin/python scripts/disclosure_check.py
```

로그까지 함께 저장:

```bash
.venv/bin/python scripts/disclosure_check.py --log
```

## 뉴스 수집 실행

최근 7일 뉴스 확인:

```bash
.venv/bin/python scripts/news_check.py
```

뉴스 로그까지 저장:

```bash
.venv/bin/python scripts/news_check.py --log
```

## 뉴스 수집에 대한 판단

현재 구현은 `Google News RSS`를 사용합니다. 추가 키 없이 바로 동작하지만, 기사 원문 자체보다는 `제목/링크/발행시각/출처` 수집용으로 쓰는 것이 적절합니다.

운영 안정성은 보통 `기업 IR/공식 공시 > 뉴스 제목 수집` 순서입니다.

## 추천 방향

- 먼저 `공시`를 구조화해서 로그로 누적
- 그 다음 `뉴스`는 기업 IR 또는 포털 기사 제목/링크/발행시각만 가볍게 수집
- 매매 판단에서는 뉴스 원문보다 `공시 우선`으로 보는 것이 안전합니다.

## 즉시 공시 알림

중요 공시는 별도 감시기로 즉시 텔레그램 전송할 수 있습니다.

- `scripts/important_disclosure_watcher.py`

기본 중요 키워드 예시:

- `유상증자`
- `자기주식취득결정`
- `자기주식처분결정`
- `기업가치제고계획`
- `단일판매ㆍ공급계약체결`
- `타법인주식및출자증권취득결정`
- `중대재해발생`
