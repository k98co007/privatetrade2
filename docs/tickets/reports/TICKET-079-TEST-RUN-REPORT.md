# TICKET-079 TEST RUN REPORT

- 티켓 ID: TICKET-079
- 수행 일시: 2026-02-16
- 수행 범위:
  - src/strategy/*
  - src/webapi/constants.py
  - src/frontend/src/domain/*
  - docs/tests/ild/ticket_062_ild_conformance.py

## 1) 전략 레지스트리 기본 등록 점검 (전략C 포함 여부)
- 결과: PASS
- 검증 방법:
  - `PYTHONPATH=src` 환경에서 `StrategyRegistry.register_defaults()` 실행 후 등록 전략 목록 확인
- 확인 결과:
  - 등록 목록에 `three_minute_buy_trailing_then_sell_trailing` 포함 확인

## 2) 변경 파일 정적 오류 점검 (get_errors 기준)
- 결과: PASS
- 점검 대상:
  - src/strategy
  - src/webapi/constants.py
  - src/frontend/src/domain
  - docs/tests/ild/ticket_062_ild_conformance.py
- 점검 결과:
  - get_errors 기준 오류 없음 (No errors found)

## 3) ILD conformance 실행 결과
- 결과: FAIL
- 실행 대상:
  - docs/tests/ild/ticket_062_ild_conformance.py
- 실행 결과 요약:
  - 총 15건 중 14건 PASS, 1건 FAIL
  - 실패 테스트: `test_simulation_router_start_returns_202`
  - 실패 내용: 기대 HTTP 202 대비 실제 HTTP 500 (`AssertionError: 500 != 202`)
- 원인 분석:
  - `src/webapi/routers/simulation_router.py`에서 `result.simulation_id` 접근 시,
    테스트 더블(`_SimulationFacadeForApiRouter.start_simulation`)이 반환한 `SimpleNamespace`에
    `simulation_id` 속성이 없어 `AttributeError` 발생
- 영향도:
  - 이번 변경과 직접 관련 여부: **직접 관련 가능성 높음**
  - 근거: 실패 지점이 WebAPI simulation start 응답 조립 경로이며,
    테스트 더블과 런타임 기대 계약(반환 객체 속성) 불일치가 직접 트리거됨

## 4) 실행한 검증 명령
1. 전략 레지스트리 기본 등록 확인
   - `$env:PYTHONPATH='src'; python -c "from strategy.strategy_registry import StrategyRegistry; r=StrategyRegistry(); r.register_defaults(); print('\n'.join(r.list_all()))"`
2. ILD conformance 실행
   - `$env:PYTHONPATH='src'; python docs/tests/ild/ticket_062_ild_conformance.py`
3. 정적 오류 점검
   - VS Code `get_errors` 도구로 대상 경로별 점검 수행

## 종합 판정
- 최종 결과: **FAIL**
- 사유: ILD conformance 1건 실패(시뮬레이션 시작 API 경로 반환 객체 계약 불일치)
