# TICKET-032-DEV-SIMULATION: 시뮬레이션 엔진 모듈 개발

## 기본 정보
- **티켓 ID**: TICKET-032-DEV-SIMULATION
- **유형**: DEV (구현)
- **담당**: 실무 개발자 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-16
- **완료일**: 2026-02-16
- **선행 조건**: TICKET-012-ILD-SIMULATION (DONE), TICKET-030-DEV-MARKETDATA (DONE), TICKET-031-DEV-STRATEGY (DONE)
- **후행 티켓**: TICKET-033-DEV-WEBAPI, TICKET-034-DEV-REPORT, TICKET-044-ILD-TEST-DOC-SIMULATION, TICKET-045-ILD-TEST-ENV-SIMULATION

## 대상 모듈
- **모듈명**: 시뮬레이션 엔진 모듈 (SIMULATION)
- **참조 문서**:
  - `docs/ild/ild-simulation-v1.0.0.md`
  - `docs/lld/lld-simulation-v1.0.0.md`
  - `docs/hld/hld-v1.0.0.md` (4.4)

## 작업 내용
1. 시뮬레이션 루프/거래 실행/비용 계산/시드머니 관리 구현
2. 진행 이벤트 발행 계약 구현
3. 검증 및 완료 리포트 작성

## 출력 산출물
- 구현 코드(백엔드 소스)
- `docs/tickets/reports/TICKET-032-COMPLETION-REPORT.md`

## 완료 결과 요약
- `src/simulation/*` 구현 완료: `SimulationEngine`, `TradeExecutor`, `CostCalculator`, `SeedMoneyManager`, `SimulationEventEmitter`, 모델/상수/예외/정밀도 유틸
- ILD 계약 반영 완료: 60일 거래일 루프, 거래일 분할/일별 처리, 비용 계산(세금 0.2%, 수수료 0.011%, 절사), 시드머니 갱신, 이벤트 수명주기
- 거래일 단위 원자성 반영: 일별 스냅샷 기반 롤백 및 `error_skip`/`no_trade` 처리
- 경량 검증 완료: `src/simulation` 진단 오류 0건, 인메모리 스모크 실행 성공
- 완료 보고서 작성: `docs/tickets/reports/TICKET-032-COMPLETION-REPORT.md`
