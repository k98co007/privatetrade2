# 저수준 설계 문서 (LLD)
# Low-Level Design Document - FRONTEND

| 항목 | 내용 |
|------|------|
| 문서 버전 | 1.3.0 |
| 작성일 | 2026-02-17 |
| 대상 모듈 | FRONTEND |
| 기반 문서 | HLD v1.3.0 (3.1, 3.2, 4.4), LLD Frontend v1.0.0 |
| 관련 티켓 | TICKET-090-LLD-FRONTEND |

## 1. 전략D 입력 UX
- 전략 선택값에 전략D 추가
- 전략D 선택 시 다중 종목 입력 컴포넌트 표시(1~20)
- 중복 종목 금지, 형식 검증(`^[0-9]{6}\\.KS$`)

## 2. 요청 매핑 규칙
- 기존 전략: `{ strategy, symbol }`
- 전략D: `{ strategy, symbols }`
- 분기 규칙은 `strategy` enum 기반 단일 함수로 처리

## 3. 상태 전이
- `editing -> validating -> submitting -> running -> completed | failed`
- 검증 실패 시 `editing`으로 복귀

## 4. 호환성 규칙
- 기존 전략 폼 입력 필드/검증/요청 계약은 변경 없음
- 전략D 전용 컴포넌트는 조건부 렌더링으로 격리

## 5. 추적성
- FR-019, CON-009~011 및 기존 FR-010~015 호환 반영
