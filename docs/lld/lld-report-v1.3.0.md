# 저수준 설계 문서 (LLD)
# Low-Level Design Document - REPORT

| 항목 | 내용 |
|------|------|
| 문서 버전 | 1.3.0 |
| 작성일 | 2026-02-17 |
| 대상 모듈 | REPORT |
| 기반 문서 | HLD v1.3.0 (3.1, 3.2, 4.5), LLD Report v1.0.0 |
| 관련 티켓 | TICKET-091-LLD-REPORT |

## 1. 메타 저장 계약 확장
- `strategy`: 실행 전략 식별자
- `input_symbols`: 전략D 입력 종목 목록(string[])
- `selected_symbol`: 실제 체결 종목(string|null)

## 2. 저장 스키마 규칙
- 기존 summary/trades 구조 유지
- `meta` 하위에 전략D 확장 필드를 추가
- 기존 전략은 `input_symbols=[]`, `selected_symbol=symbol`로 정규화

## 3. 조회/표시 계약
- 결과 API 반환 시 `meta.input_symbols`, `meta.selected_symbol` 포함
- 프론트는 선택 종목과 입력 목록을 동시 표시 가능해야 함

## 4. 추적성
- FR-019, CON-010 반영
