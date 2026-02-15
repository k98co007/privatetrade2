# TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY

## 기본 정보
- **티켓 ID**: TICKET-065-BUG-WEBAPI-CORS-WILDCARD-POLICY
- **유형**: BUG
- **상태**: INPROGRESS
- **우선순위**: Medium
- **발견일**: 2026-02-16
- **발견 티켓**: TICKET-061-LLD-TEST-RUN
- **영향 모듈**: webapi

## 결함 분류
- **Classification**: Security/Compliance Design Violation
- **Severity**: Medium

## 결함 설명
LLD(`docs/lld/lld-webapi-v1.0.0.md`)는 CORS에서 `allow_origins=['*']` 금지 및 최소 허용 헤더 정책을 요구합니다. 그러나 구현(`src/webapi/constants.py`)은 아래와 같이 wildcard를 허용합니다.
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
