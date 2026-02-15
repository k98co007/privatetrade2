# TICKET-061-TEST-RUN-REPORT

## 1) 실행 개요
- **티켓**: TICKET-061-LLD-TEST-RUN
- **실행일**: 2026-02-16
- **범위**: `marketdata`, `strategy`, `simulation`, `report`, `webapi`, `frontend`
- **목적**: LLD 인터페이스 계약, 시퀀스 제약, 모듈 설계 정합성 검증

## 2) LLD Contract Checklist (Pass/Fail)

| 모듈 | 검증 항목 | 결과 | 근거 |
|---|---|---|---|
| marketdata | `MarketDataService.fetch_market_data_with_rsi` 존재 | PASS | Python contract probe 결과 `True` |
| marketdata | `MarketDataService.validate_market_data` 존재 (LLD 명시) | FAIL | contract probe 결과 `False` |
| marketdata | `MarketDataService.is_cache_fresh` 존재 (LLD 명시) | FAIL | contract probe 결과 `False` |
| marketdata | `MarketDataService.upsert_market_data_cache` 존재 (LLD 명시) | FAIL | contract probe 결과 `False` |
| strategy | `StrategyRegistry.register_defaults()` 기본 전략 3종 등록 | PASS | `['buy_sell_trailing_stop','rsi_buy_sell_trailing_stop','sell_trailing_stop']` |
| simulation | `split_trading_days()` 거래일 분리/정렬 동작 | PASS | in-memory DataFrame 검증 성공 |
| simulation | 필수 캔들 제약이 LLD(09:05, 15:00)와 일치 | FAIL | 구현: `('09:05','15:00','15:05')` |
| report | 핵심 인터페이스(`ProfitCalculator`, `TradeHistoryFormatter`, `SummaryReportGenerator`, `ReportRepository`) 존재 | PASS | contract probe 결과 `True` |
| webapi | 라우트 계약(`/api/simulations`, `/report`, `/stream`) 등록 | PASS | `create_app()` 라우트 확인 |
| webapi | CORS 정책 LLD 준수(`*` 금지) | FAIL | 구현 상 `CORS_ALLOW_ORIGINS=['*']`, `CORS_ALLOW_HEADERS=['*']` |
| frontend | TypeScript 타입 계약(`npm run typecheck`) | PASS | 종료코드 0 |
| frontend | 빌드 계약(`npm run build`) | PASS | 종료코드 0, `vite build` 성공 |

## 3) Commands and Outcomes

### 3.1 Backend/Module Validation
1. `python -m compileall src/marketdata src/strategy src/simulation src/report src/webapi`
   - **Outcome**: PASS (컴파일 오류 없음)

2. Python contract probe (runtime/introspection)
   - 핵심 결과:
     - `CHECK marketdata.contract.methods False`
     - `validate_market_data=False, is_cache_fresh=False, upsert_market_data_cache=False`
     - `CHECK strategy.registry.defaults ['buy_sell_trailing_stop', 'rsi_buy_sell_trailing_stop', 'sell_trailing_stop']`
     - `CHECK simulation.mandatory_candles ('09:05', '15:00', '15:05')`
     - `CHECK simulation.mandatory_matches_lld_0905_1500 False`
     - `CHECK webapi.cors.origins ['*']`
     - `CHECK webapi.cors.headers ['*']`
     - `CHECK webapi.cors.ll_d_conformance_no_wildcard False`
     - `CHECK report.interfaces True`

3. Python runtime validator probe
   - 핵심 결과:
     - `validate_start_request(valid)` 성공
     - `validate_start_request(invalid symbol)`에서 `InvalidSymbolError` 발생 (의도된 검증)
     - `validate_simulation_id(valid)` 성공
     - `split_trading_days` 2일 데이터 분리/정렬 성공

### 3.2 Frontend Validation
1. `npm.cmd install`
   - **Outcome**: PASS (의존성 최신 상태)
2. `npm.cmd run typecheck`
   - **Outcome**: PASS
3. `npm.cmd run build`
   - **Outcome**: PASS (`vite build` 성공)

## 4) Defects (Classification + Reproduction)

### DEFECT-1: MarketDataService LLD 공개 인터페이스 불일치
- **분류**: Contract Violation / Design Conformance
- **심각도**: High
- **영향 모듈**: marketdata
- **설명**: LLD에서 `MarketDataService` 공개 메서드로 정의된 `validate_market_data`, `is_cache_fresh`, `upsert_market_data_cache`가 구현 클래스에 존재하지 않음.
- **재현 방법**:
  1. `PYTHONPATH=src` 설정 후 Python 실행
  2. `hasattr(MarketDataService, 'validate_market_data')` 확인
  3. 결과 `False`
- **결과**: 재현됨
- **생성 버그 티켓**: `TICKET-063-BUG-MARKETDATA-SERVICE-CONTRACT-MISMATCH`

### DEFECT-2: Simulation 필수 캔들 시간 제약 LLD 불일치
- **분류**: Sequence Constraint Violation
- **심각도**: High
- **영향 모듈**: simulation
- **설명**: LLD는 필수 캔들을 `09:05`, `15:00`로 정의하나 구현 상 `MANDATORY_CANDLE_TIMES=('09:05','15:00','15:05')`로 추가 제약이 존재.
- **재현 방법**:
  1. `from simulation.constants import MANDATORY_CANDLE_TIMES`
  2. 값 확인
  3. LLD 정의와 비교
- **결과**: 재현됨
- **생성 버그 티켓**: `TICKET-064-BUG-SIMULATION-MANDATORY-CANDLE-CONSTRAINT`

### DEFECT-3: WebAPI CORS 정책 LLD 불일치 (`*` 허용)
- **분류**: Security/Compliance Design Violation
- **심각도**: Medium
- **영향 모듈**: webapi
- **설명**: LLD는 `allow_origins=['*']` 금지 및 최소 허용 헤더 정책을 명시하나, 구현은 `CORS_ALLOW_ORIGINS=['*']`, `CORS_ALLOW_HEADERS=['*']`.
- **재현 방법**:
  1. `from webapi.constants import CORS_ALLOW_ORIGINS, CORS_ALLOW_HEADERS`
  2. 값 확인
  3. 둘 다 `*` 포함 확인
- **결과**: 재현됨
- **생성 버그 티켓**: `TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY`

## 5) 결론
- 총 12개 체크 항목 중 **PASS 8 / FAIL 4**
- FAIL 4건 중 3건은 실질 결함으로 버그 티켓 생성 완료 (marketdata 3개 항목은 동일 루트 원인 1건으로 묶음)
- frontend 빌드/타입 계약 및 주요 webapi 라우트 계약은 정상
