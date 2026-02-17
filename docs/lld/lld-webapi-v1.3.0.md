# 저수준 설계 문서 (LLD)
# Low-Level Design Document - WEBAPI

| 항목 | 내용 |
|------|------|
| 문서 버전 | 1.3.0 |
| 작성일 | 2026-02-17 |
| 대상 모듈 | WEBAPI |
| 기반 문서 | HLD v1.3.0 (3.1, 3.2, 4.3), LLD WebAPI v1.0.0 |
| 관련 티켓 | TICKET-089-LLD-WEBAPI |

## 1. POST /api/simulations 요청 계약
- 공통 필수: `strategy`
- 전략 1/2/3/A/B/C: `symbol` 필수
- 전략D: `symbols` 필수(1~20), `symbol` 금지
- 형식: 각 심볼 `^[0-9]{6}\\.KS$`

### 예시
```json
{ "strategy": "two_minute_multi_symbol_buy_trailing_then_sell_trailing", "symbols": ["005930.KS", "000660.KS"] }
```

## 2. 검증 오류 코드
- `SYMBOL_REQUIRED`
- `SYMBOLS_REQUIRED_FOR_STRATEGY_D`
- `INVALID_SYMBOLS_COUNT`
- `INVALID_SYMBOLS_FORMAT`
- `SYMBOL_AND_SYMBOLS_CONFLICT`

## 3. 상태/결과 응답 메타 확장
- 상태 조회: `input_symbols`, `selected_symbol`, `failed_symbols?`
- 결과 조회: 기존 `summary`, `trades` + `meta.strategy`, `meta.input_symbols`, `meta.selected_symbol`

## 4. 핸들러 시퀀스
1) Request validation
2) Simulation start
3) job_id 반환
4) status/result API에서 전략D 메타 포함 반환

## 5. 추적성
- FR-019, CON-009~011 반영
