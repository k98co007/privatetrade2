# TICKET-006-LLD-SIMULATION: 시뮬레이션 엔진 모듈 LLD 작성

## 기본 정보
- **티켓 ID**: TICKET-006-LLD-SIMULATION
- **유형**: LLD (Low-Level Design) 작성
- **담당**: LLD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-15
- **선행 조건**: TICKET-005-LLD-STRATEGY (DONE), TICKET-004-LLD-MARKETDATA (DONE)
- **후행 티켓**: TICKET-012-ILD-SIMULATION, TICKET-024-LLD-TEST-DOC-SIMULATION, TICKET-025-LLD-TEST-ENV-SIMULATION

## 대상 모듈
- **모듈명**: 시뮬레이션 엔진 모듈 (Simulation Engine Module)
- **HLD 섹션**: 4.4 시뮬레이션 엔진 모듈
- **관련 요구사항**: FR-007, FR-008, FR-009

## HLD에서 인용된 모듈 정보

### 책임
60일 반복 매매 시뮬레이션 실행, 매매 비용 처리, 시드머니 누적 관리

### 컴포넌트
| 컴포넌트 | 책임 |
|---------|------|
| `SimulationEngine` | 전체 시뮬레이션 루프 제어. 거래일별 전략 실행 반복 |
| `CostCalculator` | 매도 세금(0.2%), 수수료(0.011%) 계산. Decimal 정밀 연산 |
| `SeedMoneyManager` | 시드머니 잔액 관리. 매수 수량 산출(floor), 잔여 현금 보존 |
| `TradeExecutor` | 개별 거래 실행. 매수 금액, 매도 금액, 비용 차감, 순수익 산출 |
| `SimulationEventEmitter` | 시뮬레이션 진행 이벤트(진행률, 매수/매도) 발행 → SSE로 전달 |

### 입력
| 입력 | 타입 | 설명 |
|------|------|------|
| `symbol` | string | 대상 종목 심볼 |
| `strategy_name` | string | 선택된 전략 이름 |
| `initial_seed` | Decimal | 초기 시드머니 (₩10,000,000) |

### 출력
| 출력 | 타입 | 설명 |
|------|------|------|
| `simulation_result` | SimulationResult | 시뮬레이션 결과 (거래 내역, 시드머니, 통계) |
| `events` | AsyncGenerator | 실시간 모니터링 이벤트 스트림 |

### 의존 관계
- 시세 데이터 수집 모듈 (OHLCV, RSI 데이터)
- 전략 엔진 모듈 (매매 시그널)

## 작업 내용
HLD에서 정의된 시뮬레이션 엔진 모듈의 상세 설계(LLD)를 작성한다.

### 출력 산출물
- `docs/lld/lld-simulation-v1.0.0.md`
- `docs/tickets/reports/TICKET-006-COMPLETION-REPORT.md`

### 완료 정보
- **완료일**: 2026-02-15
- **검증 결과**: 수용 기준 1~6 충족

### 수용 기준
1. 시뮬레이션 루프/거래 실행/비용 계산/시드머니 갱신 인터페이스 정의
2. 60일 반복 실행 시퀀스 및 이벤트 발행 흐름 다이어그램
3. 비용 계산(세금/수수료) 및 Decimal 정밀도 규칙 명세
4. 거래 실패/데이터 누락/전략 신호 없음 시 처리 정책 명세
5. 언어 중립 수도코드가 실행 가능한 수준으로 제공
6. SRS FR-007~FR-009 추적성 확보
