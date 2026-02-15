# TICKET-064-BUG-SIMULATION-MANDATORY-CANDLE-CONSTRAINT

## 기본 정보
- **티켓 ID**: TICKET-064-BUG-SIMULATION-MANDATORY-CANDLE-CONSTRAINT
- **유형**: BUG
- **상태**: DONE
- **우선순위**: High
- **발견일**: 2026-02-16
- **발견 티켓**: TICKET-061-LLD-TEST-RUN
- **영향 모듈**: simulation

## 결함 분류
- **Classification**: Sequence Constraint Violation
- **Severity**: High

## 결함 설명
LLD(`docs/lld/lld-simulation-v1.0.0.md`)는 필수 캔들을 `09:05`, `15:00`으로 정의하지만, 구현(`src/simulation/constants.py`)은 `MANDATORY_CANDLE_TIMES = ('09:05', '15:00', '15:05')`로 추가 제약을 강제했습니다.

## 재현 절차
1. `PYTHONPATH=src` 설정
2. `from simulation.constants import MANDATORY_CANDLE_TIMES`
3. 값이 `('09:05', '15:00', '15:05')`인지 확인

## 기대 결과
필수 캔들 제약은 LLD 정의(`09:05`, `15:00`)와 일치해야 함.

## 실제 결과
`15:05`가 추가 강제되어 LLD 대비 과도한 제약 발생.

## 수용 기준
- 필수 캔들 시간 제약을 LLD와 정렬
- `SimulationEngine._validate_mandatory_candles` 동작이 갱신된 제약을 정확히 반영
- 영향 범위(누락 캔들 skip 처리) 회귀 검증 통과

## 처리 결과 요약
- `src/simulation/constants.py`의 `MANDATORY_CANDLE_TIMES`를 `('09:05', '15:00')`로 수정.
- `src/simulation/simulation_engine.py` 검증 경로가 상수 기반만 사용함을 확인하여 `15:05` 숨은 의존성 제거.
- 스모크 검증 결과:
  - `15:05` 누락 + `09:05/15:00` 존재 시 검증 통과
  - `15:00` 누락 시 `missing_mandatory_candle_times:15:00`
  - `09:05` 누락 시 `missing_mandatory_candle_times:09:05`
  - `run_simulation` 루프에서 누락일은 `missing_mandatory_candle`로 skip 처리 확인

## 완료 정보
- **완료일**: 2026-02-16
- **검증**: `get_errors`(changed simulation files) + mandatory validator smoke + simulation skip behavior smoke
- **결과 보고서**: `docs/tickets/reports/TICKET-064-BUGFIX-REPORT.md`
