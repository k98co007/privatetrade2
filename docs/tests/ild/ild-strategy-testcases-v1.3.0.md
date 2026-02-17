# ILD 테스트 케이스 문서 - STRATEGY v1.3.0

## 범위
- 대상: `docs/ild/ild-strategy-v1.3.0.md`
- 초점: 함수 시그니처, 상태 생명주기, 예외 코드 일관성

## 테스트 케이스
| ID | 시나리오 | 기대 결과 |
|----|----------|-----------|
| ILD-STR-130-001 | `evaluate_multi_symbol` 입력 정상 | 단일 진입 결정 객체 반환 |
| ILD-STR-130-002 | symbols 범위 위반 | 입력 검증 예외 반환 |
| ILD-STR-130-003 | candles_by_symbol 누락 | `SYMBOL_CANDLES_MISSING` |
| ILD-STR-130-004 | 상태 불변식 위반(BUY->BUY) | 체결 거부 및 오류 코드 반환 |
| ILD-STR-130-005 | trailing 시작/종료 경계 | 매도 조건 정확히 충족 시점에만 시그널 |

## 커버리지 계획
- 핵심 함수/예외 경로 기준 80% 이상
