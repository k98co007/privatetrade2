# 구현수준 설계 문서 (ILD)
# Implementation-Level Design - MARKETDATA

| 항목 | 내용 |
|------|------|
| 문서 버전 | 1.3.0 |
| 작성일 | 2026-02-17 |
| 대상 모듈 | MARKETDATA |
| 기반 문서 | docs/lld/lld-marketdata-v1.3.0.md |
| 관련 티켓 | TICKET-101-ILD-MARKETDATA |

## 1. 구현 목표
전략D 경로의 다중 종목/2분봉 조회를 코드 레벨에서 즉시 구현 가능한 절차와 함수 시그니처로 정의한다.

## 2. 핵심 함수 시그니처
```text
fetch_market_data_batch(symbols: list[str], period: str='60d', interval: str='2m') -> dict[str, DataFrame]
fetch_market_data_with_rsi(symbol: str, period: str='60d', interval: str='5m') -> DataFrame
validate_symbols(symbols: list[str]) -> None
fetch_with_retry(symbol: str, period: str, interval: str, timeout_sec: int=10, max_attempts: int=3) -> DataFrame
ensure_reference_candle_0903(df: DataFrame) -> None
upsert_market_data_cache(symbol: str, df: DataFrame) -> int
```

## 3. 단계별 구현 절차
1. `validate_symbols`에서 길이(1~20), 중복, 정규식 검증
2. 심볼별 캐시 조회(`symbol, period, interval`)
3. cache hit면 TTL/범위/09:03 검증 후 반환 후보에 적재
4. miss/stale 심볼은 `fetch_with_retry` 호출
5. 원본 데이터 정규화(컬럼 소문자, KST 정렬, 세션 필터)
6. 데이터 무결성 검증 및 RSI 부착
7. 캐시 upsert 후 결과 맵에 적재
8. 실패 심볼이 있으면 `BatchFetchPartialError(results, failed_symbols)` 반환

## 4. 외부 의존성 호출 규약
- `yfinance.download(tickers=symbol, period=period, interval=interval, auto_adjust=True, threads=False, progress=False, timeout=10)`
- 재시도 백오프: 1초, 2초, 4초
- 최대 3회 실패 시 `ExternalAPIError` 변환

## 5. 예외 처리 규칙
- 입력 검증 실패: `InvalidSymbolsError`
- 2분봉 제약 위반: `IntervalConstraintError`
- 09:03 캔들 누락: `ReferenceCandleMissingError`
- 부분 실패: `BatchFetchPartialError`
- 저장 실패: `StorageError`

## 6. 생명주기/상태
- 배치 실행 상태: `STARTED -> CACHE_CHECK -> REMOTE_FETCH -> VALIDATED -> CACHED -> COMPLETED`
- 심볼 단위 실패는 격리하되, 최종 반환에서 실패 목록을 반드시 노출

## 7. 개발 체크리스트
- 함수별 단위 테스트(정상/오류/경계) 작성
- retry 호출 횟수/백오프 시간 검증
- TTL 경계 검증(2m=6분, 5m=15분)
- 부분 실패 결과 구조 검증
