# TICKET-007-LLD-WEBAPI: 웹 API 모듈 LLD 작성

## 기본 정보
- **티켓 ID**: TICKET-007-LLD-WEBAPI
- **유형**: LLD (Low-Level Design) 작성
- **담당**: LLD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-15
- **선행 조건**: TICKET-006-LLD-SIMULATION (DONE), TICKET-005-LLD-STRATEGY (DONE)
- **후행 티켓**: TICKET-013-ILD-WEBAPI, TICKET-026-LLD-TEST-DOC-WEBAPI, TICKET-027-LLD-TEST-ENV-WEBAPI

## 대상 모듈
- **모듈명**: 웹 API 모듈 (Web API Module)
- **HLD 섹션**: 4.5 웹 API 모듈
- **관련 요구사항**: FR-010, FR-011, FR-012

## HLD에서 인용된 모듈 정보

### 책임
REST API 엔드포인트 제공, SSE 실시간 이벤트 스트리밍, 입력 검증

### 컴포넌트
| 컴포넌트 | 책임 |
|---------|------|
| `SimulationRouter` | 시뮬레이션 시작/상태 조회/결과 조회 REST API |
| `SSERouter` | 시뮬레이션 모니터링 SSE 엔드포인트 |
| `RequestValidator` | Pydantic 기반 요청 데이터 유효성 검증 (심볼 형식, 전략 선택) |
| `ResponseFormatter` | API 응답 데이터 포맷팅 (금액 표시, 날짜 형식) |
| `ErrorHandler` | 전역 예외 처리, 한국어 오류 메시지 반환 |
| `CORSMiddleware` | 프론트엔드 SPA의 크로스 오리진 요청 허용 |

### 입력
| 입력 | 타입 | 설명 |
|------|------|------|
| HTTP 요청 | Request | REST API 요청 (JSON body, path params) |

### 출력
| 출력 | 타입 | 설명 |
|------|------|------|
| HTTP 응답 | Response | JSON 응답 (시뮬레이션 결과, 상태, 에러 메시지) |
| SSE 스트림 | StreamingResponse | 실시간 이벤트 스트림 |

### 의존 관계
- 시뮬레이션 엔진 모듈 (시뮬레이션 실행)
- 결과 보고서 모듈 (결과 조회)

## 작업 내용
HLD에서 정의된 웹 API 모듈의 상세 설계(LLD)를 작성한다.

### 출력 산출물
- `docs/lld/lld-webapi-v1.0.0.md`
- `docs/tickets/reports/TICKET-007-COMPLETION-REPORT.md`

### 완료 정보
- **완료일**: 2026-02-15
- **검증 결과**: 수용 기준 1~6 충족

### 수용 기준
1. REST/SSE 엔드포인트 인터페이스(요청/응답/상태코드) 정의
2. 입력 검증, 에러 매핑, 전역 예외 처리 정책 명세
3. SSE 이벤트 페이로드 스키마/연결 수명주기/재연결 정책 정의
4. 라우터-서비스 호출 시퀀스 및 장애 시나리오 흐름 제공
5. 언어 중립 수도코드 제공
6. SRS FR-010~FR-012 추적성 확보
