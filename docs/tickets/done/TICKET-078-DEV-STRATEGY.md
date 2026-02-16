# TICKET-078-DEV-STRATEGY: 전략 모듈 개발 및 연계 반영 (v1.2.0)

## 기본 정보
- **티켓 ID**: TICKET-078-DEV-STRATEGY
- **유형**: 개발(구현) (모듈별)
- **담당**: 실무 개발 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.2.0
- **생성일**: 2026-02-16
- **선행 조건**: TICKET-077-ILD-STRATEGY-UPDATE (DONE)
- **후행 티켓**: TICKET-079-ILD-TEST-RUN

## 작업 내용
전략 모듈 ILD v1.2.0에 따라 신규 전략C를 구현하고 WebAPI/Frontend 전략 식별자 연계를 반영한다.

### 입력 산출물
- docs/ild/ild-strategy-v1.2.0.md
- src/strategy/*
- src/webapi/constants.py
- src/frontend/src/domain/*

### 출력 산출물
- 전략 모듈 코드 변경
- WebAPI 전략 허용값 변경
- Frontend 전략 선택/검증 변경
- docs/tickets/reports/TICKET-078-COMPLETION-REPORT.md

### 구현 요구사항
1. 신규 전략C(3분봉 Trailing Buy + 매도 Trailing Stop, 당일 손절 미적용) 구현
2. 09:03 기준가/1% 하락/전저점 대비 0.2% 반등/반등 시점 캔들 종가 전액 매수 규칙 반영
3. 매수-매도 교대 제약(연속 매수 금지)을 기존 규칙과 충돌 없이 반영
4. StrategyRegistry 기본 등록 목록에 전략C 추가
5. WebAPI VALID_STRATEGIES와 Frontend 전략 목록/타입 갱신
6. 기존 전략(1/2/3/A/B) 호환성 유지
