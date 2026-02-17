# LLD 테스트 케이스 문서 - STRATEGY v1.3.0

## 범위
- 대상: `docs/lld/lld-strategy-v1.3.0.md`
- 초점: 전략D 입력 검증, 후보 선택, 단일 체결/교대 규칙

## 테스트 케이스
| ID | 시나리오 | 기대 결과 |
|----|----------|-----------|
| LLD-STR-130-001 | symbols 0개/21개 입력 | `INVALID_SYMBOLS_COUNT` |
| LLD-STR-130-002 | 잘못된 종목 포맷 | `INVALID_SYMBOL_FORMAT` |
| LLD-STR-130-003 | 09:03 캔들 누락 | `REFERENCE_CANDLE_0903_MISSING` |
| LLD-STR-130-004 | interval!=2m | `INTERVAL_MISMATCH_2M_REQUIRED` |
| LLD-STR-130-005 | 동시 후보 다수 | 입력 순서 첫 종목 1건만 선택 |
| LLD-STR-130-006 | BUY 직후 BUY 시도 | `ALTERNATION_RULE_VIOLATION` |
| LLD-STR-130-007 | 수익 1% 후 이익보전율 하락 | trailing 매도 신호 발생 |

## 커버리지 계획
- 기능/제약 매핑 기준 80% 이상
