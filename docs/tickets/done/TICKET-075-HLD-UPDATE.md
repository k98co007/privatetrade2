# TICKET-075: HLD 갱신 (v1.2.0)

## 기본 정보
- **티켓 ID**: TICKET-075
- **유형**: HLD 갱신
- **담당**: HLD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.2.0
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-074-SRS-UPDATE (DONE)
- **후행 티켓**: TICKET-076-LLD-STRATEGY-UPDATE

## 작업 내용
SRS v1.2.0을 기반으로 HLD를 v1.2.0으로 갱신하고, 전략C 도입에 따른 아키텍처 영향 및 모듈 인터페이스를 정의한다.

### 입력 산출물
- docs/srs/srs-v1.2.0.md
- docs/hld/hld-v1.1.0.md

### 출력 산출물
- docs/hld/hld-v1.2.0.md
- docs/tickets/reports/TICKET-075-COMPLETION-REPORT.md

### 수용 기준
1. 전략 엔진 확장(전략C 추가) 아키텍처 흐름이 반영되어야 함
2. Strategy/WebAPI/Frontend 계약 영향이 명시되어야 함
3. 모듈 분해 섹션에서 전략 모듈 LLD 갱신 범위가 명확해야 함
4. 버전 Minor 증가(1.2.0) 반영
