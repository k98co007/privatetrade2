# TICKET-005-LLD-STRATEGY: 전략 엔진 모듈 LLD 작성

## 기본 정보
- **티켓 ID**: TICKET-005-LLD-STRATEGY
- **유형**: LLD (Low-Level Design) 작성
- **담당**: LLD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-15
- **선행 조건**: TICKET-003 (HLD 완료)
- **후행 티켓**: TICKET-011-ILD-STRATEGY, TICKET-022-LLD-TEST-DOC-STRATEGY, TICKET-023-LLD-TEST-ENV-STRATEGY

## 대상 모듈
- **모듈명**: 전략 엔진 모듈 (Strategy Engine Module)
- **HLD 섹션**: 4.3 전략 엔진 모듈
- **관련 요구사항**: FR-003, FR-004, FR-005, FR-006, NFR-008

## HLD에서 인용된 모듈 정보

### 책임
투자 전략 인터페이스 정의 및 3개 전략 구현체 제공. Strategy Pattern 기반 확장 구조

### 컴포넌트
| 컴포넌트 | 책임 |
|---------|------|
| `BaseStrategy` (ABC) | 전략 추상 기반 클래스. 매수/매도/손절 판단 메서드 인터페이스 정의 |
| `SellTrailingStopStrategy` | 전략 1: 09:05 매수, 1% 수익 후 이익보전 80% 매도, 15:00 손절 |
| `BuySellTrailingStopStrategy` | 전략 2: 기준가 대비 1% 하락→전저점 추적→0.2% 반등 매수, 전략 1 매도 동일 |
| `RSIBuySellTrailingStopStrategy` | 전략 3: 전략 2 매수 조건 + RSI ≤ 30 조건 추가 |
| `StrategyRegistry` | 전략 등록/조회. 전략 이름 → 전략 인스턴스 매핑 |

### 입력
| 입력 | 타입 | 설명 |
|------|------|------|
| `daily_candles` | DataFrame | 특정 거래일의 5분 분봉 데이터 (09:00~15:30) |
| `rsi_data` | DataFrame | 해당 거래일의 RSI 값 (전략 3 전용) |
| `seed_money` | Decimal | 현재 시드머니 잔액 |

### 출력
| 출력 | 타입 | 설명 |
|------|------|------|
| `trade_signal` | TradeSignal | 매수/매도 시점, 가격, 수량, 매도 사유를 포함한 거래 시그널 |

### 의존 관계
- 시세 데이터 수집 모듈 (OHLCV, RSI 데이터)

## 작업 내용
HLD에서 정의된 전략 엔진 모듈의 상세 설계(LLD)를 작성한다.

### 출력 산출물
- `docs/lld/lld-strategy-v1.0.0.md`
- `docs/tickets/reports/TICKET-005-COMPLETION-REPORT.md`

### 완료 정보
- **완료일**: 2026-02-15
- **검증 결과**: 수용 기준 1~6 충족

### 수용 기준
1. 각 컴포넌트(BaseStrategy, 전략 3종, StrategyRegistry)의 클래스/함수 인터페이스 정의
2. 전략 선택/실행 시퀀스 및 거래 시그널 생성 흐름 다이어그램
3. 전략별 매수/매도/손절 조건의 언어 중립 수도코드
4. 전략 확장(신규 전략 추가) 절차와 제약사항 명시
5. 에러/예외 처리(입력 데이터 부족, RSI 누락, 장시간 데이터 누락) 정의
6. SRS FR-003~FR-006 및 NFR-008 추적성 확보
