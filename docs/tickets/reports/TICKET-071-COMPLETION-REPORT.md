# TICKET-071-COMPLETION-REPORT

## 1) 개요
- 티켓: TICKET-071-DEV-STRATEGY
- 목적: 2026-02-16 인터뷰 기반 신규 전략 2종(A/B) 구현 및 WebAPI/Frontend 전략 ID 연계 반영
- 작업일: 2026-02-16

## 2) 변경 파일
- `src/strategy/constants.py`
- `src/strategy/rsi_only_trailing_stop_strategy.py` (신규)
- `src/strategy/buy_trailing_then_sell_trailing_strategy.py` (신규)
- `src/strategy/strategy_registry.py`
- `src/strategy/__init__.py`
- `src/webapi/constants.py`
- `src/frontend/src/domain/types.ts`
- `src/frontend/src/domain/mappers.ts`
- `src/frontend/src/domain/validators.ts`
- `docs/tickets/reports/TICKET-071-COMPLETION-REPORT.md` (신규)

## 3) 구현 요약
- 전략 A(`rsi_only_trailing_stop`) 추가
  - 매수: RSI `<= 30`일 때만 허용
  - 매도: 기존 Trailing Stop 매도 규칙 재사용
  - 손절: 당일 손절 미적용(`should_stop_loss() -> False`)
- 전략 B(`buy_trailing_then_sell_trailing`) 추가
  - 매수: 기존 전략2(기준가 1.0% 하락 + 전저점 대비 0.2% 반등) 재사용
  - 매도: 기존 Trailing Stop 매도 규칙 재사용
  - 손절: 당일 손절 미적용(`should_stop_loss() -> False`)
- `StrategyRegistry.register_defaults()`에 전략 A/B 등록
- WebAPI `VALID_STRATEGIES`에 전략 A/B 추가
- Frontend 도메인
  - `StrategyId` union에 전략 A/B 추가
  - 전략 옵션 라벨 2건 추가
  - 허용 전략 목록 및 검증 메시지를 5전략 기준으로 갱신

## 4) 검증 결과
### 4.1 정적/문제 체크
- 대상: 본 티켓에서 편집한 9개 코드 파일
- 결과: **PASS** (No errors found)

### 4.2 전략 등록 스모크 테스트
- 명령:
  - `PYTHONPATH=src python -c "from strategy.strategy_registry import StrategyRegistry; r=StrategyRegistry(); r.register_defaults(); print(sorted(r.list_all()))"`
- 결과: **PASS**
- 출력:
  - `['buy_sell_trailing_stop', 'buy_trailing_then_sell_trailing', 'rsi_buy_sell_trailing_stop', 'rsi_only_trailing_stop', 'sell_trailing_stop']`

### 4.3 ILD conformance 스크립트
- 명령:
  - `python docs/tests/ild/ticket_062_ild_conformance.py` (초기 실행 실패: PYTHONPATH 미설정)
  - `PYTHONPATH=src python docs/tests/ild/ticket_062_ild_conformance.py`
- 결과: **FAIL (1/15)**
- 실패 테스트:
  - `test_simulation_router_start_returns_202`
- 실패 요약:
  - `simulation_router` 내부에서 `types.SimpleNamespace`에 `simulation_id` 속성이 없어 `500` 발생
  - 본 티켓 변경 범위(전략 A/B 추가 및 목록 연계)와 직접 무관한 기존/인접 이슈로 판단

## 5) 호환성 및 제약 준수
- 기존 전략 1/2/3 ID 및 동작은 변경하지 않음
- 신규 전략은 기존 클래스 로직을 상속/재사용하여 최소 변경으로 구현
- 기존 일일 평가 사이클(`BaseStrategy.evaluate`)의 `context.is_bought` 제약을 그대로 따르므로 당일 연속 매수(BUY->BUY) 문제를 유발하지 않음

## 6) 가정(Assumptions)
- 신규 전략 ID는 ILD/LDD v1.1.0 계약을 따라 다음으로 확정함:
  - `rsi_only_trailing_stop` (전략 A)
  - `buy_trailing_then_sell_trailing` (전략 B)
- 전략 A/B의 "당일 손절 미적용"은 각 전략의 `should_stop_loss()`를 항상 `False`로 구현해 충족한다고 가정함.
