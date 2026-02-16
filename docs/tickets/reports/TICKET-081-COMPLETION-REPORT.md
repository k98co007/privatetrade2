# TICKET-081-COMPLETION-REPORT

## 1) 작업 요약
- 티켓: TICKET-081-DEV-SIMULATION-STRATEGY-INTERVAL-ALIGNMENT
- 목적: 전략C(3분봉) 도입 이후 시뮬레이션 엔진/마켓데이터의 전략별 분봉 정합성 보완
- 작업일: 2026-02-16

## 2) 변경 파일
- src/simulation/simulation_engine.py
- src/marketdata/constants.py

## 3) 반영 상세
- `SimulationEngine.run_simulation`에서 전략 로드를 선행하고 전략별 분봉 interval(`5m`/`3m`)을 선택하도록 변경
- `process_one_day`의 필수 캔들 검증을 전략별 `required_times` 기반으로 변경
- `_resolve_strategy_interval` 유틸 추가(전략의 `required_interval_minutes` 기준)
- MarketData `SUPPORTED_INTERVALS`에 `3m` 추가

## 4) 수용기준 체크
- [x] 전략별 분봉 선택 로직 반영
- [x] 전략별 필수 캔들 검증 로직 반영
- [x] ILD conformance PASS 확인

## 5) 검증 결과
- 명령: `$env:PYTHONPATH='src'; python docs/tests/ild/ticket_062_ild_conformance.py`
- 결과: PASS (`Ran 15 tests`, `OK`)
