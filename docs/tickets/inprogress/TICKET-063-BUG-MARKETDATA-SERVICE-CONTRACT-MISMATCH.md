# TICKET-063-BUG-MARKETDATA-SERVICE-CONTRACT-MISMATCH

## 기본 정보
- **티켓 ID**: TICKET-063-BUG-MARKETDATA-SERVICE-CONTRACT-MISMATCH
- **유형**: BUG
- **상태**: DONE
- **우선순위**: High
- **발견일**: 2026-02-16
- **발견 티켓**: TICKET-061-LLD-TEST-RUN
- **영향 모듈**: marketdata

## 결함 분류
- **Classification**: Contract Violation / Design Conformance
- **Severity**: High

## 결함 설명
LLD(`docs/lld/lld-marketdata-v1.0.0.md`)에서 `MarketDataService` 공개 인터페이스로 정의된 아래 메서드가 구현 클래스(`src/marketdata/market_data_service.py`)에 존재하지 않습니다.
- `validate_market_data(df: DataFrame) -> None`
- `is_cache_fresh(symbol: str, period: str, interval: str, now_kst: datetime) -> bool`
- `upsert_market_data_cache(df: DataFrame, symbol: str, fetched_at: datetime) -> int`

## 재현 절차
1. `PYTHONPATH=src` 설정
2. Python에서 아래 실행
   - `hasattr(MarketDataService, 'validate_market_data')`
   - `hasattr(MarketDataService, 'is_cache_fresh')`
   - `hasattr(MarketDataService, 'upsert_market_data_cache')`
3. 모두 `False` 반환 확인

## 기대 결과
LLD에 명시된 공개 인터페이스가 구현 클래스에 동일 명세로 존재해야 함.

## 실제 결과
3개 메서드 미구현(혹은 내부 의존성으로만 우회) 상태.

## 수용 기준
- 위 3개 공개 메서드가 `MarketDataService`에 LLD 시그니처와 의미로 구현됨
- 기존 동작(캐시 신선도 판정/검증/upsert)과의 역호환성 유지
- 간단한 contract smoke 검증(인터페이스 존재 + 기본 동작) 통과

## 처리 결과 요약
- `src/marketdata/market_data_service.py`에 공개 계약 메서드 3종 추가:
   - `validate_market_data(df) -> None`
   - `is_cache_fresh(symbol, period, interval, now_kst) -> bool`
   - `upsert_market_data_cache(df, symbol, fetched_at) -> int`
- 기존 내부 `MarketDataValidator`/`MarketDataCacheRepository` 로직을 재사용하도록 구현하여 중복 로직 없이 계약 정합성 확보.
- `fetch_market_data_with_rsi` 흐름에서 새 공개 메서드를 사용하도록 연결해 역호환 동작 유지.

## 완료 정보
- **완료일**: 2026-02-16
- **검증**: contract hasattr 스모크 + 기본 호출 경로 스모크 + 변경 파일 정적 오류 점검
- **결과 보고서**: `docs/tickets/reports/TICKET-063-BUGFIX-REPORT.md`
