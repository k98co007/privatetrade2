# TICKET-070-ILD-STRATEGY: 전략 모듈 ILD 갱신 (v1.1.0)

## 기본 정보
- **티켓 ID**: TICKET-070-ILD-STRATEGY
- **유형**: ILD 갱신 (모듈별)
- **담당**: ILD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.1.0
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-069-LLD-STRATEGY-UPDATE (DONE)
- **후행 티켓**: TICKET-071-DEV-STRATEGY

## 작업 내용
LLD 전략 모듈 v1.1.0을 기반으로 ILD를 v1.1.0으로 갱신한다.

### 입력 산출물
- docs/lld/lld-strategy-v1.1.0.md
- docs/ild/ild-strategy-v1.0.0.md

### 출력 산출물
- docs/ild/ild-strategy-v1.1.0.md
- docs/tickets/reports/TICKET-070-COMPLETION-REPORT.md

### LLD 인용 범위
- 전략 A/B 인터페이스
- 제약(당일 손절 미적용, 매수-매도 교대)
- 에러 처리/경계조건

### 수용 기준
1. 함수 시그니처/파라미터/반환값 수준으로 구현 절차가 명시되어야 함
2. 외부 의존 호출 규약(StrategyRegistry, validators, API strategy enum 연계)이 명시되어야 함
3. 초급 개발자가 공식문서 없이 구현 가능한 절차여야 함
4. LLD ↔ ILD 추적성이 명시되어야 함
5. 버전 Minor 증가(1.1.0)가 반영되어야 함
