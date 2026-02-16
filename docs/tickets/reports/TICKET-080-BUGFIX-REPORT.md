# TICKET-080-BUGFIX-REPORT

- 티켓 ID: TICKET-080-BUG-WEBAPI-SIMULATION-START-RESPONSE-CONTRACT
- 작업 일시: 2026-02-16
- 대상 파일: `src/webapi/routers/simulation_router.py`

## 1) 원인 분석
- `start_simulation`에서 반환 객체를 로깅할 때 `result.simulation_id`, `result.status`를 직접 접근하고 있었습니다.
- ILD 테스트 더블은 `SimpleNamespace`에 `model_dump`만 제공하고 `simulation_id`/`status` 속성은 직접 노출하지 않아 `AttributeError`가 발생했습니다.
- 예외가 라우터 공통 예외 처리로 전달되며 500 응답이 반환되어 `test_simulation_router_start_returns_202`가 실패했습니다.

## 2) 수정 내용
- 파일: `src/webapi/routers/simulation_router.py`
- `start_simulation` 내부에서 반환값 정규화 로직을 추가했습니다.
	- 우선순위:
		1. `model_dump(mode="json")` 지원 객체
		2. `dict` 객체
		3. `dict()` 지원 객체(호환)
		4. `__dict__` 기반 객체
- 정규화된 `result_payload`에서 `simulation_id`, `status`를 안전하게 추출해 로깅하도록 변경했습니다.
- 응답은 기존 계약을 유지했습니다.
	- `HTTP 202 Accepted`
	- `ResponseFormatter.ok(result_payload, request_id)`

## 3) 검증 결과
- 실행 명령:
	- `$env:PYTHONPATH='src'; python docs/tests/ild/ticket_062_ild_conformance.py`
- 결과: **PASS**
	- `Ran 15 tests in 0.054s`
	- `OK`
	- 포함 확인: `test_simulation_router_start_returns_202 ... ok`

## 4) 호환성 영향
- API 응답 스키마 및 상태코드(202) 변경 없음.
- 기존 pydantic 모델 반환 경로는 그대로 동작하며, 테스트 더블/유사 객체 반환 경로 호환성이 확장되었습니다.
- 요청 범위 외 모듈/파일 동작에 영향 없음.
