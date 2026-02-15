# TICKET-030-DEV-MARKETDATA: 시세 데이터 수집 모듈 개발

## 기본 정보
- **티켓 ID**: TICKET-030-DEV-MARKETDATA
- **유형**: DEV (구현)
- **담당**: 실무 개발자 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-16
- **완료일**: 2026-02-16
- **선행 조건**: TICKET-010-ILD-MARKETDATA (DONE)
- **후행 티켓**: TICKET-031-DEV-STRATEGY, TICKET-040-ILD-TEST-DOC-MARKETDATA, TICKET-041-ILD-TEST-ENV-MARKETDATA

## 대상 모듈
- **모듈명**: 시세 데이터 수집 모듈 (MARKETDATA)
- **참조 문서**:
  - `docs/ild/ild-marketdata-v1.0.0.md`
  - `docs/lld/lld-marketdata-v1.0.0.md`
  - `docs/hld/hld-v1.0.0.md` (4.2)

## ILD 인용 범위
- 구현 단위/파일 구조: `src/marketdata/*`
- 핵심 컴포넌트: `YahooFinanceClient`, `RSICalculator`, `MarketDataValidator`, `MarketDataCacheRepository`, `MarketDataService`
- 처리 정책: 캐시 우선, 원격 재시도(1/2/4초, 최대 3회), RSI(14) 계산, SQLite upsert

## 작업 내용
1. ILD 계약에 맞춘 MARKETDATA 코드 구현
2. 예외 코드 표준화(`E-MD-001`~`E-MD-012`) 및 전파 규칙 적용
3. 최소 단위 검증(모듈 단위 테스트 또는 실행 검증) 수행
4. 완료 리포트 작성

## 출력 산출물
- 구현 코드(백엔드 소스)
- `docs/tickets/reports/TICKET-030-COMPLETION-REPORT.md`

## 수용 기준
1. ILD 명시 함수 시그니처/호출 규약 구현
2. 캐시/원격 조회/검증/RSI/업서트 흐름 동작
3. 오류 처리 및 재시도 정책 확인 가능
4. 빌드 또는 모듈 실행 검증 성공

## 완료 결과 요약
- ILD 계약 기준의 MARKETDATA 모듈 코드(`src/marketdata/*`) 구현 완료
- 도메인 예외 코드(`E-MD-001`~`E-MD-012`) 및 재시도/백오프(1/2/4초, 최대 3회) 반영
- RSI(14, Wilder EWM), SQLite 캐시 조회/최신성(TTL 15분)/upsert 반영
- 완료 보고서 작성: `docs/tickets/reports/TICKET-030-COMPLETION-REPORT.md`
