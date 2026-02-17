# LLD 테스트 케이스 문서 - MARKETDATA v1.3.0

## 범위
- 대상: `docs/lld/lld-marketdata-v1.3.0.md`
- 초점: 2분봉/다중 종목 조회, 캐시 TTL, 재시도/부분 실패

## 테스트 케이스
| ID | 시나리오 | 기대 결과 |
|----|----------|-----------|
| LLD-MD-130-001 | symbols 1~20 경계값 | 유효 범위 통과, 범위 외 오류 |
| LLD-MD-130-002 | interval=2m 강제 | 전략D에서 2m 외 입력 시 오류 |
| LLD-MD-130-003 | 09:03 캔들 누락 | `REFERENCE_CANDLE_0903_MISSING` |
| LLD-MD-130-004 | 캐시 TTL 2m=6분 경계 | hit/miss 판정 정확 |
| LLD-MD-130-005 | 캐시 TTL 5m=15분 경계 | hit/miss 판정 정확 |
| LLD-MD-130-006 | 재시도 3회/백오프 1-2-4초 | 시도 횟수/간격 준수 |
| LLD-MD-130-007 | 배치 일부 심볼 실패 | `BATCH_FETCH_PARTIAL_FAILURE`, failed_symbols 포함 |

## 커버리지 계획
- 요구사항/오류경로 기준 80% 이상
