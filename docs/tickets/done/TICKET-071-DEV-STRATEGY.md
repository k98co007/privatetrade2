# TICKET-071-DEV-STRATEGY: 전략 모듈 개발 및 연계 반영 (v1.1.0)

## 기본 정보
- **티켓 ID**: TICKET-071-DEV-STRATEGY
- **유형**: 개발(구현) (모듈별)
- **담당**: 실무 개발 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.1.0
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-070-ILD-STRATEGY-UPDATE (DONE)
- **후행 티켓**: TICKET-072-ILD-TEST-RUN-UPDATE

## 작업 내용
전략 모듈 ILD v1.1.0에 따라 신규 전략 2종을 구현하고 WebAPI/Frontend 전략 식별자 연계를 반영한다.

### 입력 산출물
- docs/ild/ild-strategy-v1.1.0.md
- src/strategy/*
- src/webapi/constants.py
- src/frontend/src/domain/*

### 출력 산출물
- 전략 모듈 코드 변경
- WebAPI 전략 허용값 변경
- Frontend 전략 선택/검증 변경
- docs/tickets/reports/TICKET-071-COMPLETION-REPORT.md

### 구현 요구사항
1. 신규 전략A(예: RSI 기반 매수 + 매도 Trailing Stop, 당일 손절 미적용) 구현
2. 신규 전략B(예: 매수 Trailing Stop + 매도 Trailing Stop, 당일 손절 미적용) 구현
3. 신규 전략 공통 제약(연속 매수 금지/매수-매도 교대)을 기존 엔진 제약과 충돌 없이 반영
4. StrategyRegistry 기본 등록 목록에 신규 전략 추가
5. WebAPI VALID_STRATEGIES와 Frontend 전략 목록/검증 메시지 갱신
6. 기존 전략(1/2/3) 호환성 유지
7. 정적 오류/기본 검증 통과
