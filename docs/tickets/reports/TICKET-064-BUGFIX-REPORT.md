# TICKET-064-BUGFIX-REPORT

## 1) 개요
- **티켓**: TICKET-064-BUG-SIMULATION-MANDATORY-CANDLE-CONSTRAINT
- **처리일**: 2026-02-16
- **대상 모듈**: `simulation`
- **목표**: 시뮬레이션 필수 캔들 제약을 LLD(`09:05`, `15:00`)와 정렬

## 2) 원인 분석 (Before)
- `src/simulation/constants.py`에 `MANDATORY_CANDLE_TIMES = ('09:05', '15:00', '15:05')`가 정의되어 있었음.
- `src/simulation/simulation_engine.py`의 `_validate_mandatory_candles`가 위 상수를 그대로 사용하여 `15:05` 누락도 필수 누락으로 판정.
- 결과적으로 LLD 대비 과도한 제약으로 `missing_mandatory_candle_times:15:05` 케이스가 발생 가능.

## 3) 수정 내용 (After)
- `src/simulation/constants.py`
  - `MANDATORY_CANDLE_TIMES`를 `('09:05', '15:00')`로 수정.
- `src/simulation/simulation_engine.py`
  - 별도 하드코딩 없이 `MANDATORY_CANDLE_TIMES` 기반 검증을 유지하여, 숨은 `15:05` 의존성이 없음을 확인.

## 4) 검증 수행 및 결과

### 4.1 변경 파일 정적 오류 검사
- 실행: `get_errors`
- 대상:
  - `src/simulation/constants.py`
  - `src/simulation/simulation_engine.py`
- 결과: **No errors found**

### 4.2 Mandatory Candle Smoke (정책 검증)
- 실행 명령(요약):
  - `PYTHONPATH=c:/Dev/privatetrade2/src python -c "..."`
  - `_validate_mandatory_candles` 직접 호출로 시나리오 검증
- 출력:
  - `NO_1505_BUT_HAS_0905_1500 PASS`
  - `MISSING_1500 FAIL missing_mandatory_candle_times:15:00`
  - `MISSING_0905 FAIL missing_mandatory_candle_times:09:05`
- 결과: **PASS**

### 4.3 Missing-Candle Skip Behavior Smoke
- 실행 명령(요약):
  - `PYTHONPATH=c:/Dev/privatetrade2/src python -c "...SimulationEngine.run_simulation(...)..."`
  - 3개 거래일 데이터 주입:
    - Day1: `09:05`, `15:00`만 존재(`15:05` 없음)
    - Day2: `15:00` 누락
    - Day3: `09:05` 누락
- 출력 요약:
  - `MANDATORY ('09:05', '15:00')`
  - `TOTAL_TRADES 3`
  - `NO_TRADE_DAYS 3`
  - `ERROR_SKIP_DAYS 0`
  - `TRADE 2026-02-10 no_trade`
  - `TRADE 2026-02-11 missing_mandatory_candle`
  - `TRADE 2026-02-12 missing_mandatory_candle`
- 해석:
  - `15:05` 부재는 필수 누락으로 처리되지 않음.
  - `09:05`/`15:00` 누락일은 정책대로 `missing_mandatory_candle`로 skip 처리됨.

## 5) 산출물
- 코드 수정:
  - `src/simulation/constants.py`
- 티켓 이관/상태 갱신:
  - `docs/tickets/done/TICKET-064-BUG-SIMULATION-MANDATORY-CANDLE-CONSTRAINT.md`
- 버그 수정 보고서:
  - `docs/tickets/reports/TICKET-064-BUGFIX-REPORT.md`

## 6) 결론
- 시뮬레이션 필수 캔들 제약이 LLD(`09:05`, `15:00`)와 일치하도록 수정되었고,
- SimulationEngine 검증 경로에서 `15:05` 숨은 의존성이 제거되었으며,
- 스모크 검증으로 누락 캔들 skip 정책의 기대 동작을 확인했다.
