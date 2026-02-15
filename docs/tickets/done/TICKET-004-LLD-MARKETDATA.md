# TICKET-004-LLD-MARKETDATA: 시세 데이터 수집 모듈 LLD 작성

## 기본 정보
- **티켓 ID**: TICKET-004-LLD-MARKETDATA
- **유형**: LLD (Low-Level Design) 작성
- **담당**: LLD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-15
- **선행 조건**: TICKET-003 (HLD 완료)
- **후행 티켓**: TICKET-010-ILD-MARKETDATA, TICKET-020-LLD-TEST-DOC-MARKETDATA, TICKET-021-LLD-TEST-ENV-MARKETDATA

## 대상 모듈
- **모듈명**: 시세 데이터 수집 모듈 (Market Data Module)
- **HLD 섹션**: 4.2 시세 데이터 수집 모듈
- **관련 요구사항**: FR-001 (코스피 종목 5분 분봉 데이터 조회), FR-002 (RSI 지표 데이터 조회)

## HLD에서 인용된 모듈 정보

### 책임
Yahoo Finance API를 통한 5분 분봉 데이터 조회 및 RSI 지표 산출

### 컴포넌트
| 컴포넌트 | 책임 |
|---------|------|
| `YahooFinanceClient` | yfinance 라이브러리를 통한 API 호출, 5분 분봉 OHLCV 데이터 조회 (60일) |
| `RSICalculator` | 5분 분봉 종가 기반 14기간 RSI 산출. pandas rolling 연산 활용 |
| `MarketDataService` | 데이터 조회 + RSI 산출을 통합한 서비스 레이어. 에러 처리(재시도 3회) |

### 입력
| 입력 | 타입 | 설명 |
|------|------|------|
| `symbol` | string | 코스피 종목 심볼 (예: `005930.KS`) |
| `period` | string | 조회 기간 (`60d`) |
| `interval` | string | 분봉 간격 (`5m`) |

### 출력
| 출력 | 타입 | 설명 |
|------|------|------|
| `ohlcv_data` | DataFrame | 타임스탬프, OHLCV 컬럼 포함 시계열 데이터 |
| `rsi_data` | DataFrame | 타임스탬프, RSI 값 (0~100) 컬럼 포함 |

### 외부 의존성
- 외부: Yahoo Finance API (HTTPS)
- 라이브러리: yfinance, pandas, numpy

### 관련 데이터 모델 (HLD 8.2.3)
- `market_data_cache` 테이블: symbol, timestamp, open, high, low, close, volume, rsi, fetched_at

### 관련 인터페이스 (HLD 5.1)
- 시뮬레이션 엔진 → 시세 데이터 수집: 함수 호출 (in-process)
- 시세 데이터 수집 → Yahoo Finance: HTTPS REST API (yfinance 라이브러리)

## 작업 내용
HLD에서 정의된 시세 데이터 수집 모듈의 상세 설계(LLD)를 작성한다.

### 출력 산출물
- `docs/lld/lld-marketdata-v1.0.0.md`
- `docs/tickets/reports/TICKET-004-COMPLETION-REPORT.md`

### 완료 정보
- **완료일**: 2026-02-15
- **검증 결과**: 수용 기준 1~9 충족

### 수용 기준
1. 각 컴포넌트(YahooFinanceClient, RSICalculator, MarketDataService)의 클래스/함수 인터페이스 정의 (메서드 시그니처, 파라미터, 반환값)
2. 컴포넌트 간 시퀀스 다이어그램 (데이터 조회 → RSI 계산 → 결과 반환 흐름)
3. Yahoo Finance API 호출 상세 (yfinance 라이브러리 사용법, 파라미터, 반환 데이터 구조)
4. RSI 계산 알고리즘 수도코드 (14기간 기준, pandas rolling 연산)
5. 에러 처리 시퀀스 (재시도 3회, 타임아웃, 데이터 없음 등)
6. 데이터 검증 로직 (빈 DataFrame, 누락 컬럼, 비정상 값 등)
7. market_data_cache 테이블 CRUD 상세
8. 언어 중립적 수도코드 실행 가능 수준
9. SRS FR-001, FR-002 요구사항과의 추적성 확보
