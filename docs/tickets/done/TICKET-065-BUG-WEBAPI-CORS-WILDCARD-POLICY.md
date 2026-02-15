# TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY

## 기본 정보
- **티켓 ID**: TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY
- **유형**: BUG
- **상태**: DONE
- **우선순위**: Medium
- **발견일**: 2026-02-16
- **발견 티켓**: TICKET-061-LLD-TEST-RUN
- **영향 모듈**: webapi

## 결함 분류
- **Classification**: Security/Compliance Design Violation
- **Severity**: Medium

## 결함 설명
LLD(`docs/lld/lld-webapi-v1.0.0.md`)는 CORS에서 `allow_origins=['*']` 금지 및 최소 허용 헤더 정책을 요구합니다. 그러나 구현(`src/webapi/constants.py`)은 아래와 같이 wildcard를 허용했습니다.
- `CORS_ALLOW_ORIGINS = ['*']`
- `CORS_ALLOW_HEADERS = ['*']`

## 재현 절차
1. `PYTHONPATH=src` 설정
2. `from webapi.constants import CORS_ALLOW_ORIGINS, CORS_ALLOW_HEADERS`
3. 두 값 모두 `*` 포함 확인

## 기대 결과
환경별 명시 Origin 및 최소 헤더 허용 정책을 사용해야 함.

## 실제 결과
Origin/헤더 모두 wildcard 허용 상태.

## 수용 기준
- `CORS_ALLOW_ORIGINS`를 환경별 명시 도메인 기반으로 변경
- `CORS_ALLOW_HEADERS`를 최소 필요 헤더 목록으로 축소
- `configure_cors` 연계 동작 확인 및 회귀 smoke 통과

## 처리 결과 요약
- `src/webapi/constants.py`에 env 기반 origin 파서(`WEBAPI_CORS_ALLOW_ORIGINS`)를 추가하고 wildcard token(`*`) 제거 정책을 적용.
- 기본 allow origin을 명시 localhost 목록(`http://localhost:3000`, `http://localhost:5173`)으로 변경하여 개발 사용성을 유지.
- `CORS_ALLOW_HEADERS`를 최소 허용 헤더(`Authorization`, `Content-Type`, `Last-Event-ID`)로 축소.
- `create_app()` startup 및 `CORSMiddleware` 부착 상태에서 constants/middleware 값 모두 wildcard가 없음을 smoke로 검증.

## 완료 정보
- **완료일**: 2026-02-16
- **검증**: `get_errors`(changed webapi files) + constants/create_app/CORSMiddleware smoke + env override smoke
- **결과 보고서**: `docs/tickets/reports/TICKET-065-BUGFIX-REPORT.md`
