# TICKET-081-DEV-SIMULATION-STRATEGY-INTERVAL-ALIGNMENT: 시뮬레이션 엔진 전략별 분봉 정합성 반영

## 기본 정보
- **티켓 ID**: TICKET-081-DEV-SIMULATION-STRATEGY-INTERVAL-ALIGNMENT
- **유형**: 개발(구현) 보완
- **담당**: 실무 개발 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.2.1
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-078-DEV-STRATEGY (DONE)
- **후행 티켓**: 없음

## 작업 내용
전략C(3분봉) 추가 후 시뮬레이션 엔진이 5분봉 고정 호출을 사용하던 정합성 이슈를 수정해 전략별 분봉 호출/검증이 일치하도록 보완한다.

### 입력 산출물
- src/simulation/simulation_engine.py
- src/marketdata/constants.py

### 출력 산출물
- 전략별 분봉 연동 코드
- docs/tickets/reports/TICKET-081-COMPLETION-REPORT.md

### 수용 기준
1. 시뮬레이션 엔진이 전략별 분봉(5m/3m)을 선택해야 함
2. 필수 캔들 검증이 전략별 required_times 기반이어야 함
3. ILD conformance가 PASS 해야 함
