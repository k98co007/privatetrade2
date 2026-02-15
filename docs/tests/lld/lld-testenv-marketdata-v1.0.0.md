# LLD 테스트 환경 정의 문서
# Low-Level Test Environment Specification - MARKETDATA

| 항목 | 내용 |
|------|------|
| **문서 버전** | 1.0.0 |
| **작성일** | 2026-02-16 |
| **대상 모듈** | MARKETDATA (시세 데이터 수집 모듈) |
| **기반 문서** | LLD MARKETDATA v1.0.0, SRS v1.0.0 (FR-001, FR-002) |
| **관련 티켓** | TICKET-021-LLD-TEST-ENV-MARKETDATA |
| **산출물 경로** | `docs/tests/lld/lld-testenv-marketdata-v1.0.0.md` |

---

## 목차

1. [목적 및 범위](#1-목적-및-범위)
2. [테스트 환경 요구사항](#2-테스트-환경-요구사항)
3. [의존 라이브러리/버전 기준선](#3-의존-라이브러리버전-기준선)
4. [네트워크 조건 정의](#4-네트워크-조건-정의)
5. [Mock/Stub 범위](#5-mockstub-범위)
6. [테스트 데이터 준비/정리 절차](#6-테스트-데이터-준비정리-절차)
7. [재현 가능한 실행 명령 예시](#7-재현-가능한-실행-명령-예시)
8. [실행 체크리스트](#8-실행-체크리스트)
9. [장애 대응 및 재현성 보장 규칙](#9-장애-대응-및-재현성-보장-규칙)

---

## 1. 목적 및 범위

본 문서는 MarketData LLD 검증을 위한 **실행 환경 기준**과 **절차 표준**을 정의한다.

- 대상: `YahooFinanceClient`, `RSICalculator`, `MarketDataService`, `market_data_cache(SQLite)`
- 목적: 동일 입력/동일 환경에서 동일 결과를 재현 가능한 테스트 운영
- 범위: 단위/통합 레벨 (LLD 검증)

비범위:
- 전략 모듈 전체 시뮬레이션 성능 벤치마크
- 프론트엔드/E2E 시나리오

---

## 2. 테스트 환경 요구사항

### 2.1 하드웨어/OS 기준

| 항목 | 최소 기준 | 권장 기준 |
|------|-----------|-----------|
| OS | Windows 10/11 x64 또는 Linux x64 | Windows 11 x64 |
| CPU | 2 vCPU | 4 vCPU 이상 |
| 메모리 | 8 GB | 16 GB 이상 |
| 디스크 여유 | 5 GB | 10 GB 이상 |
| 시간 동기화 | NTP 동기화 필수 | 동일 |

### 2.2 로케일/타임존 기준

| 항목 | 기준 값 | 목적 |
|------|---------|------|
| 서버/테스트 TZ | `Asia/Seoul` | 거래시간 필터(09:00~15:30) 재현 일관성 |
| 로그 시간대 | UTC + KST 병기 | 장애 분석 시 상호 검증 |
| 로케일 | UTF-8 | 한글 로그/문서 깨짐 방지 |

### 2.3 테스트 실행 레벨

| 레벨 | 포함 범위 | 외부 네트워크 필요 |
|------|-----------|--------------------|
| Unit | RSI 계산, 데이터 검증, 예외 변환 | 불필요 |
| Integration(Local) | cache + service + mocked yahoo client | 불필요 |
| Live-Sanity(선택) | 실 Yahoo 응답 포맷 변화 감지 | 필요 |

---

## 3. 의존 라이브러리/버전 기준선

> 아래 버전은 LLD 검증 재현을 위한 **기준선(Baseline)** 이다. 실제 프로젝트 lock 파일이 존재하면 lock 파일 버전을 우선한다.

### 3.1 런타임/도구 기준

| 항목 | 버전 기준 | 비고 |
|------|-----------|------|
| Python | 3.11.x | 권장 3.11.8 |
| pip | 24.x 이상 | 최신 보안 패치 |
| pytest | 8.3.x | 테스트 러너 |
| pytest-mock | 3.14.x | mock/spy |
| freezegun | 1.5.x | 시간 고정(TTL 경계 테스트) |

### 3.2 데이터/외부 연동 라이브러리 기준

| 라이브러리 | 버전 기준 | 용도 |
|------------|-----------|------|
| pandas | 2.2.x | OHLCV/RSI 데이터 처리 |
| numpy | 1.26.x | 수치 연산 |
| yfinance | 0.2.5x | Yahoo 데이터 조회 |
| requests | 2.32.x | yfinance 하위 의존/네트워크 |
| sqlite3 | Python stdlib | cache 저장소 |

### 3.3 권장 고정 예시 (`requirements-test.txt`)

```text
pytest==8.3.4
pytest-mock==3.14.0
freezegun==1.5.1
pandas==2.2.3
numpy==1.26.4
yfinance==0.2.54
requests==2.32.3
```

---

## 4. 네트워크 조건 정의

### 4.1 기본 프로파일

| 프로파일 | RTT | 손실률 | 용도 |
|----------|-----|--------|------|
| NET-NORMAL | 20~100ms | <0.1% | 일반 성공 경로 |
| NET-DEGRADED | 300~800ms | 1~3% | retry 동작 검증 |
| NET-FAIL | timeout 또는 연결 실패 | N/A | 예외 변환/최종 실패 검증 |

### 4.2 적용 규칙

1. Unit/Integration(Local)은 외부 네트워크 의존 금지(모든 Yahoo 응답 mock 처리)
2. Live-Sanity만 실제 인터넷 사용
3. 네트워크 장애 검증은 실제 회선 제어보다 **mock 기반 Timeout 주입**을 우선 사용

---

## 5. Mock/Stub 범위

### 5.1 Mock 대상 및 이유

| 대상 | Mock/Stub 방식 | 이유 |
|------|----------------|------|
| `yfinance.download` | 함수 monkeypatch/mock | 외부 API 변동성 제거, 재현성 확보 |
| 현재 시간(`now_kst`) | freezegun 또는 clock provider stub | TTL 15분 경계값 결정론 검증 |
| DB 파일 경로 | 임시 sqlite 파일 fixture | 테스트 격리 |
| 네트워크 오류 | TimeoutError/ConnectionError 강제 raise | retry/예외 경로 검증 |

### 5.2 Mock 비대상

| 항목 | 정책 |
|------|------|
| `RSICalculator` 수식 | 실제 계산 로직 그대로 실행 (pure function 검증) |
| `validate_market_data` 무결성 규칙 | 실제 로직 실행 |
| sqlite upsert/read | 실제 sqlite 동작 검증 (in-memory 또는 temp file) |

### 5.3 Live-Sanity 범위(선택)

- 목적: Yahoo 응답 스키마 drift 조기 탐지
- 범위: 1개 심볼(`005930.KS`), 1회 조회, 스키마 검증만 수행
- 결과 불안정 시 release gate로 사용하지 않고 경보성 지표로만 사용

---

## 6. 테스트 데이터 준비/정리 절차

### 6.1 데이터 준비 (Setup)

1. 테스트 시작 전 임시 DB 생성
2. 표준 OHLCV fixture 3종 준비
   - `fixture_normal_5m_2days.csv` (정상)
   - `fixture_with_invalid_rows.csv` (무결성 위반 포함)
   - `fixture_short_close_series.csv` (RSI 기간 부족)
3. timestamp는 KST(`+09:00`) 기준으로 생성
4. 기본 심볼은 `005930.KS` 사용

### 6.2 샘플 캐시 시드 SQL

```sql
CREATE TABLE IF NOT EXISTS market_data_cache (
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    rsi REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY(symbol, timestamp)
);
```

### 6.3 테스트 데이터 정리 (Teardown)

1. 테스트 종료 후 트랜잭션 rollback 또는 DB 파일 삭제
2. temp 디렉터리/캐시 파일 제거
3. 환경변수(`MARKETDATA_LIVE_TEST`, `TZ`) 초기화
4. mock patch 원복 여부 확인

---

## 7. 재현 가능한 실행 명령 예시

> 아래 명령은 PowerShell 기준이며, 프로젝트 루트(`c:\Dev\privatetrade2`)에서 실행한다.

### 7.1 환경 초기화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-test.txt
```

### 7.2 Unit 테스트 실행

```powershell
$env:TZ = "Asia/Seoul"
pytest tests/marketdata -m "unit" -q
```

### 7.3 Integration(Local) 실행

```powershell
$env:TZ = "Asia/Seoul"
pytest tests/marketdata -m "integration" -q
```

### 7.4 재시도/예외 경로 단일 케이스 실행

```powershell
pytest tests/marketdata/test_marketdata_service.py::test_retry_timeout_then_success -q
pytest tests/marketdata/test_marketdata_service.py::test_retry_exhausted_raises_external_api_error -q
```

### 7.5 Live-Sanity(선택) 실행

```powershell
$env:MARKETDATA_LIVE_TEST = "1"
pytest tests/marketdata -m "live" -q
```

### 7.6 결과 로그 저장 예시

```powershell
pytest tests/marketdata -m "unit or integration" -q --maxfail=1 --disable-warnings | Tee-Object -FilePath .\artifacts\marketdata-test.log
```

---

## 8. 실행 체크리스트

### 8.1 실행 전 체크

- [ ] Python/pytest 버전이 기준선과 일치한다.
- [ ] 시스템 타임존 또는 테스트 타임존이 `Asia/Seoul`로 설정되어 있다.
- [ ] 테스트 DB/fixture 경로가 쓰기 가능하다.
- [ ] Unit/Integration 실행 시 외부 네트워크 호출이 차단(mock)되어 있다.
- [ ] 테스트 대상 브랜치가 최신 LLD 반영 상태다.

### 8.2 실행 중 체크

- [ ] Core 시나리오(P0) 먼저 실행했다.
- [ ] Timeout/NoData/Validation 오류 경로를 모두 실행했다.
- [ ] 캐시 hit/miss/TTL 경계 케이스를 실행했다.
- [ ] RSI 계산 규칙(길이 부족/횡보/상승)을 검증했다.

### 8.3 실행 후 체크

- [ ] 실패 로그에 테스트 데이터 결함과 코드 결함을 분리 기록했다.
- [ ] mock 원복, 임시 파일 정리, 환경변수 초기화를 완료했다.
- [ ] 요구사항 추적 매트릭스(FR-001/FR-002) 커버 상태를 갱신했다.
- [ ] 재현 명령과 동일 조건에서 1회 이상 재실행하여 동일 결과를 확인했다.

---

## 9. 장애 대응 및 재현성 보장 규칙

1. **flake 방지**: 시간 의존 테스트는 반드시 clock freeze 적용
2. **외부 의존 분리**: unit/integration은 live API 금지
3. **데이터 고정**: fixture 파일은 해시(또는 git tracked)로 변경 이력 관리
4. **로그 표준화**: 테스트 시작 시점에 `git commit hash`, `python version`, `pip freeze` 스냅샷 남김
5. **실패 분류**: `환경 이슈` / `테스트 데이터 이슈` / `코드 결함` 3분류로 보고
