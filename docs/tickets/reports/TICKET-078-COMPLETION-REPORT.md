# TICKET-078-COMPLETION-REPORT

## 기본 정보
- Ticket: TICKET-078-DEV-STRATEGY
- 완료일: 2026-02-16
- 범위: 전략C 추가 및 StrategyRegistry/WebAPI/Frontend 6전략 계약 확장

## 구현 요약
1. 전략C `three_minute_buy_trailing_then_sell_trailing`를 신규 추가했다.
2. 전략C 규칙을 반영했다.
   - 09:03 기준가: `open`
   - 09:03 이후 1.0% 하락 시 저점 추적 시작
   - 저점 대비 0.2% 반등 시 해당 캔들 `close`로 매수
   - 당일 손절 미적용
3. StrategyRegistry 기본 등록을 6개 전략으로 확장했다.
4. WebAPI `VALID_STRATEGIES`를 6개 전략으로 확장했다.
5. Frontend 전략 타입/옵션/검증 계약을 6개 전략으로 확장했다.

## 상세 변경 파일
- src/strategy/constants.py
- src/strategy/__init__.py
- src/strategy/base_strategy.py
- src/strategy/strategy_input_validator.py
- src/strategy/strategy_registry.py
- src/strategy/three_minute_buy_trailing_then_sell_trailing_strategy.py
- src/webapi/constants.py
- src/frontend/src/domain/types.ts
- src/frontend/src/domain/mappers.ts
- src/frontend/src/domain/validators.ts
- docs/tickets/reports/TICKET-078-COMPLETION-REPORT.md

## 검증 결과
### 1) Python 전략 레지스트리 기본 등록 검증
- 명령: `$env:PYTHONPATH='src'; python -c "from strategy.strategy_registry import StrategyRegistry; r=StrategyRegistry(); r.register_defaults(); names=r.list_all(); assert 'three_minute_buy_trailing_then_sell_trailing' in names; print('registry_ok', len(names))"`
- 결과: `registry_ok 6`

### 2) Frontend 타입 검증
- 명령: `npm.cmd run typecheck`
- 위치: `src/frontend`
- 결과: 성공 (`tsc --noEmit` 통과)

## 비고
- 티켓 상태 파일(`docs/tickets/inprogress/TICKET-078-DEV-STRATEGY.md`)은 수정하지 않았다.
- 불필요한 리팩터링 없이 요청 범위 내 변경만 적용했다.
