# TICKET-063-BUGFIX-REPORT

## 1) 개요
- **티켓**: TICKET-063-BUG-MARKETDATA-SERVICE-CONTRACT-MISMATCH
- **처리일**: 2026-02-16
- **대상 모듈**: `marketdata`
- **목표**: `MarketDataService`의 LLD 계약 메서드 3종 미구현 문제 해결

## 2) 원인 분석 (Before)
- `src/marketdata/market_data_service.py`에 아래 공개 메서드가 부재:
  - `validate_market_data(df) -> None`
  - `is_cache_fresh(symbol, period, interval, now_kst) -> bool`
  - `upsert_market_data_cache(df, symbol, fetched_at) -> int`
- 근거: `docs/tickets/reports/TICKET-061-TEST-RUN-REPORT.md`의 contract probe 결과
  - `validate_market_data=False`
  - `is_cache_fresh=False`
  - `upsert_market_data_cache=False`

## 3) 수정 내용 (After)
- `src/marketdata/market_data_service.py`에 공개 메서드 3종 추가.
- 기존 내부 로직 재사용:
  - `validate_market_data`: `MarketDataValidator`의 `normalize_columns`, `normalize_timezone`, `filter_trading_session`, `validate_integrity` 재사용
  - `is_cache_fresh`: `MarketDataCacheRepository.is_cache_fresh` 재사용
  - `upsert_market_data_cache`: 기존 `_to_cache_rows` + `MarketDataCacheRepository.upsert_market_data_cache` 재사용
- 기존 조회 플로우 역호환 유지:
  - `fetch_market_data_with_rsi`에서 캐시 신선도 판정/검증/upsert를 새 공개 메서드를 경유하도록 연결

## 4) 검증 수행 및 결과

### 4.1 변경 파일 정적 오류 검사
- 실행: `get_errors` (changed files)
- 결과: **No errors found**
  - `src/marketdata/market_data_service.py`
  - `docs/tickets/done/TICKET-063-BUG-MARKETDATA-SERVICE-CONTRACT-MISMATCH.md`
  - `docs/tickets/reports/TICKET-063-BUGFIX-REPORT.md`

### 4.2 Contract + Basic Call Path Smoke
- 실행 명령(요약):
  - `PYTHONPATH=c:/Dev/privatetrade2/src python -c "..."`
  - 검증 항목:
    - `hasattr(service, 'validate_market_data')`
    - `hasattr(service, 'is_cache_fresh')`
    - `hasattr(service, 'upsert_market_data_cache')`
    - `validate_market_data` 기본 정상 경로
    - `is_cache_fresh`/`upsert_market_data_cache` 기본 호출 경로
- 출력:
  - `HAS_METHODS_OK True`
  - `VALIDATE_OK True`
  - `FRESH_OK True`
  - `UPSERT_ROWS 1`
- 결과: **PASS**

## 5) 산출물
- 코드 수정: `src/marketdata/market_data_service.py`
- 티켓 상태 갱신/이관:
  - `docs/tickets/done/TICKET-063-BUG-MARKETDATA-SERVICE-CONTRACT-MISMATCH.md`
- 버그 수정 보고서:
  - `docs/tickets/reports/TICKET-063-BUGFIX-REPORT.md`

## 6) 결론
- LLD에 명시된 `MarketDataService` 공개 계약 불일치 결함이 해소되었고,
- 기존 fetch 동작을 유지한 채 계약 메서드가 서비스 레벨에 복원되었으며,
- 스모크 검증으로 인터페이스 존재 및 기본 호출 경로를 확인했다.
