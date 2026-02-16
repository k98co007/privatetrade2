# TICKET-072-TEST-RUN-REPORT

## 1) 개요
- **티켓**: TICKET-072-ILD-TEST-RUN-UPDATE
- **처리일**: 2026-02-16
- **대상 변경**: 전략 신규 2종 추가 및 WebAPI/Frontend 전략 목록 연계

## 2) 수행 항목 및 결과

### 2.1 변경 파일 정적 오류 검사
- 대상:
  - `src/strategy/constants.py`
  - `src/strategy/rsi_only_trailing_stop_strategy.py`
  - `src/strategy/buy_trailing_then_sell_trailing_strategy.py`
  - `src/strategy/strategy_registry.py`
  - `src/strategy/__init__.py`
  - `src/webapi/constants.py`
  - `src/frontend/src/domain/types.ts`
  - `src/frontend/src/domain/mappers.ts`
  - `src/frontend/src/domain/validators.ts`
- 결과: **PASS** (No errors found)

### 2.2 전략 레지스트리 기본 등록 스모크
- 실행 명령:
  - `PYTHONPATH=src python -c "from strategy.strategy_registry import StrategyRegistry; r=StrategyRegistry(); r.register_defaults(); print(sorted(r.list_all()))"`
- 결과: **PASS**
- 출력:
  - `['buy_sell_trailing_stop', 'buy_trailing_then_sell_trailing', 'rsi_buy_sell_trailing_stop', 'rsi_only_trailing_stop', 'sell_trailing_stop']`

### 2.3 ILD Conformance 실행
- 실행 명령:
  - `PYTHONPATH=src python docs/tests/ild/ticket_062_ild_conformance.py`
- 결과: **FAIL (1/15)**
- 실패 테스트:
  - `test_simulation_router_start_returns_202`
- 오류 요약:
  - `simulation_router`의 테스트 더블(`SimpleNamespace`)에서 `simulation_id` 속성 누락으로 500 반환
- 관련성 판단:
  - 본 티켓 변경 범위(전략 식별자/전략 구현 추가)와 **직접 무관**한 기존 테스트 스텁 이슈로 판단

## 3) 수용 기준 판정
1. 변경 파일 정적 오류 없음: **충족**
2. 신규 전략 2종 레지스트리 포함: **충족**
3. ILD conformance PASS/FAIL 기록: **충족**
4. 실패 항목 원인 및 관련성 명시: **충족**

## 4) 결론
- 신규 전략 2종 및 연계 변경은 정적 검사/스모크에서 정상 반영됨.
- ILD conformance의 1건 실패는 기존 테스트 더블 구성 이슈로 분리 관리가 필요함.
