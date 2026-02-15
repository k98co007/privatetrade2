# TICKET-065-BUGFIX-REPORT

## 1) 개요
- **티켓**: TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY
- **처리일**: 2026-02-16
- **대상 모듈**: `webapi`
- **목표**: CORS wildcard 정책 제거 및 LLD 최소 허용 정책 정렬

## 2) 원인 분석 (Before)
- `src/webapi/constants.py`에서 아래 값이 wildcard로 설정되어 있었음.
  - `CORS_ALLOW_ORIGINS = ['*']`
  - `CORS_ALLOW_HEADERS = ['*']`
- `src/webapi/middleware/cors.py`는 해당 상수를 그대로 `CORSMiddleware`에 주입하므로,
  결과적으로 브라우저 preflight에서 과도 허용 정책이 적용됨.

## 3) 수정 내용 (After)
- `src/webapi/constants.py`
  - `CORS_ALLOW_ORIGINS_ENV = 'WEBAPI_CORS_ALLOW_ORIGINS'` 추가
  - `CORS_DEFAULT_ALLOW_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']` 추가
  - `_parse_cors_allow_origins()` 추가:
    - 환경변수의 콤마 구분 origin을 파싱
    - 공백/빈 값 제거
    - `*` 토큰 제거
    - 결과가 비면 개발 기본 allowlist로 fallback
  - `CORS_ALLOW_ORIGINS = _parse_cors_allow_origins()`로 변경
  - `CORS_ALLOW_HEADERS`를 최소 허용 헤더로 축소:
    - `['Authorization', 'Content-Type', 'Last-Event-ID']`
- `src/webapi/middleware/cors.py`
  - wiring은 유지하되, 변경된 상수를 통해 명시 allowlist 정책이 그대로 적용됨.

## 4) 검증 수행 및 결과

### 4.1 변경 파일 정적 오류 검사
- 실행: `get_errors`
- 대상:
  - `src/webapi/constants.py`
  - `src/webapi/middleware/cors.py`
  - `src/webapi/__init__.py`
- 결과: **No errors found**

### 4.2 App Startup + CORS Attachment Smoke
- 실행(요약):
  - `PYTHONPATH=src` 환경에서 `from webapi import create_app` 호출
  - `app.user_middleware`에서 `CORSMiddleware` 탐색
  - constants와 middleware kwargs에 `*` 미포함 검증
- 결과 출력 요약:
  - `CONST_ORIGINS ['http://localhost:3000', 'http://localhost:5173']`
  - `CONST_HEADERS ['Authorization', 'Content-Type', 'Last-Event-ID']`
  - `MW_ORIGINS ['http://localhost:3000', 'http://localhost:5173']`
  - `MW_HEADERS ['Authorization', 'Content-Type', 'Last-Event-ID']`
  - `SMOKE_OK`

### 4.3 Env Override Smoke
- 실행(요약):
  - `WEBAPI_CORS_ALLOW_ORIGINS='https://app.example.com,*'`
  - constants import 후 파싱 결과 확인
- 결과 출력 요약:
  - `OVERRIDE_ORIGINS ['https://app.example.com']`
  - `ENV_OVERRIDE_SMOKE_OK`

## 5) 산출물
- 코드 수정:
  - `src/webapi/constants.py`
- 티켓 이관/상태 갱신:
  - `docs/tickets/done/TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY.md`
- 버그 수정 보고서:
  - `docs/tickets/reports/TICKET-065-BUGFIX-REPORT.md`

## 6) 결론
- WebAPI CORS 정책에서 wildcard 허용을 제거했고,
- 개발 편의(명시 localhost allowlist)와 운영 확장성(env 기반 origin 지정)을 동시에 확보했으며,
- LLD 최소 허용 정책(명시 origin, 최소 헤더, `Last-Event-ID` 허용)과 정렬됨을 smoke로 확인했다.
