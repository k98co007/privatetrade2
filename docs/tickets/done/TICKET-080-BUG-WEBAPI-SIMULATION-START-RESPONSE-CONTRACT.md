# TICKET-080-BUG-WEBAPI-SIMULATION-START-RESPONSE-CONTRACT: 시뮬레이션 시작 응답 계약 불일치 버그 수정

## 기본 정보
- **티켓 ID**: TICKET-080-BUG-WEBAPI-SIMULATION-START-RESPONSE-CONTRACT
- **유형**: 버그 수정
- **담당**: 버그 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.2.1
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-079-ILD-TEST-RUN (DONE, FAIL)
- **후행 티켓**: 없음

## 작업 내용
`docs/tests/ild/ticket_062_ild_conformance.py`의 `test_simulation_router_start_returns_202` 실패를 유발한 WebAPI 응답 계약 불일치를 수정한다.

### 입력 산출물
- src/webapi/routers/simulation_router.py
- docs/tests/ild/ticket_062_ild_conformance.py
- docs/tickets/reports/TICKET-079-TEST-RUN-REPORT.md

### 출력 산출물
- WebAPI 버그 수정 코드
- docs/tickets/reports/TICKET-080-BUGFIX-REPORT.md

### 수용 기준
1. `ticket_062_ild_conformance.py` 전체 테스트가 PASS 해야 함
2. 시뮬레이션 시작 API가 202를 정상 반환해야 함
3. 응답 조립 시 테스트 더블/실객체 모두 호환되는 계약 처리여야 함
4. 기존 API 응답 스키마 호환성이 유지되어야 함
