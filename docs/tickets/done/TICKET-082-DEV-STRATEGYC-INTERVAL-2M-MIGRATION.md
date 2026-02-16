# TICKET-082-DEV-STRATEGYC-INTERVAL-2M-MIGRATION: 전략C 2분봉 전환 및 Yahoo interval 호환성 수정

## 기본 정보
- **티켓 ID**: TICKET-082-DEV-STRATEGYC-INTERVAL-2M-MIGRATION
- **유형**: 버그 수정(구현/설계 정합)
- **담당**: 실무 개발 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.2.2
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-081-DEV-SIMULATION-STRATEGY-INTERVAL-ALIGNMENT (DONE), docs/userinterview/20260216.md 갱신(2분봉)
- **후행 티켓**: TICKET-083-USERSTORY-UPDATE-INTERVIEW-20260216-2M

## 작업 내용
인터뷰 변경사항(전략C 3분봉→2분봉)을 반영하여 Yahoo Finance 미지원 interval(3m) 호출 오류를 제거하고, 시뮬레이션/전략/프론트 표기를 2분봉 기준으로 정합화한다.

### 입력 산출물
- docs/userinterview/20260216.md
- src/marketdata/constants.py
- src/simulation/simulation_engine.py
- src/strategy/three_minute_buy_trailing_then_sell_trailing_strategy.py
- src/frontend/src/domain/mappers.ts

### 출력 산출물
- 2분봉 기준 전략 실행 코드
- docs/tickets/reports/TICKET-082-COMPLETION-REPORT.md

### 수용 기준
1. Yahoo API 호출 interval에 `3m`이 더 이상 사용되지 않고 전략C는 `2m`을 사용해야 함
2. 전략C 입력 검증/실행이 `required_interval_minutes=2` 기준으로 동작해야 함
3. 프론트 전략 라벨이 2분봉으로 표시되어 사용자 입력과 구현이 일치해야 함
4. 최소 단위 검증(전략 등록/시뮬레이션 interval 매핑)이 통과해야 함
