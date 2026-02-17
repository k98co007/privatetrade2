# 구현수준 설계 문서 (ILD)
# Implementation-Level Design Document - STRATEGY

| 항목 | 내용 |
|------|------|
| 문서 버전 | 1.3.0 |
| 작성일 | 2026-02-16 |
| 대상 모듈 | STRATEGY (전략 엔진 모듈) |
| 기반 문서 | LLD STRATEGY v1.3.0, ILD STRATEGY v1.2.0 |
| 관련 티켓 | TICKET-100-ILD-STRATEGY |

---

## v1.3.0 변경 요약

- 전략 D(`two_minute_multi_symbol_buy_trailing_then_sell_trailing`) 구현 명세 추가
- 다중 종목 입력(1~20) 대비 단일 진입 시그널(0 또는 1건) 계약 추가
- 첫 후보 선택 정책(`FIRST_CANDIDATE_BY_INPUT_ORDER`) 구현 절차 추가
- 전략 D 전용 예외 코드/복구 규칙/주니어 구현 체크리스트 추가

---

## 1. 목적 및 범위

### 1.1 목적

본 문서는 `docs/lld/lld-strategy-v1.3.0.md`를 기준으로 전략 D를 실제 코드로 구현하기 위한 함수 단위 명세를 정의한다. 초급 개발자가 외부 문서 없이 구현 가능하도록 시그니처, 파라미터, 반환 모델, 외부 호출 계약, 예외 처리, 구현 순서를 제공한다.

### 1.2 범위 (In-Scope)

- 전략 D 입력/상태/출력 모델 정의
- 전략 D 엔트리 후보 계산 및 단일 선택 구현
- 전략 D trailing 매도 규칙(기존 규칙 재사용) 구현
- 전략 D 입력 검증 및 예외 처리 규칙 정의
- SimulationEngine/StrategyRegistry 연동 호출 계약 정의

### 1.3 비범위 (Out-of-Scope)

- 2분봉 수집/정제 파이프라인 구현
- 체결 엔진(수수료/세금 포함) 구현
- WebAPI/Frontend 라우팅/화면 구현

---

## 2. 구현 단위 및 파일 책임

```text
src/
  strategy/
    models.py
    errors.py
    strategy_input_validator.py
    strategy_registry.py
    two_minute_multi_symbol_buy_trailing_then_sell_trailing_strategy.py   # 신규
```

| 파일 | 책임 |
|------|------|
| `models.py` | Strategy D 입력/상태/반환 모델 추가 |
| `errors.py` | Strategy D 오류 코드 및 예외 타입 추가 |
| `strategy_input_validator.py` | symbols/candles/interval/reference time 검증 함수 추가 |
| `two_minute_multi_symbol_buy_trailing_then_sell_trailing_strategy.py` | 전략 D 핵심 로직 구현 |
| `strategy_registry.py` | 전략 D 등록 및 조회 가능 상태 보장 |

---

## 3. 외부/상위 모듈 호출 계약

### 3.1 SimulationEngine → Strategy D

| 호출 함수 | 시그니처 | 반환 | 실패 시 |
|-----------|----------|------|---------|
| `evaluate_multi_symbol` | `(strategy_input: StrategyDInput) -> list[TradeSignal]` | 시간순 처리 결과(0..N) | `StrategyInputError`, `StrategyExecutionError` |

호출 규약:
1. `symbols` 순서는 호출자가 결정하며 전략 D는 입력 순서를 그대로 우선순위로 사용한다.
2. 전략 D는 엔트리 판단 시점마다 `SingleEntryDecision`을 내부 생성하고, 체결 가능 시 `TradeSignal(BUY)` 1건만 만든다.
3. 보유 중에는 엔트리 계산을 수행하지 않고 보유 종목 매도 판단만 수행한다.

### 3.2 StrategyRegistry 계약

| 메서드 | 시그니처 | 계약 |
|--------|----------|------|
| `register_defaults` | `() -> None` | 전략 D 기본 등록 포함 |
| `get` | `(name: str) -> BaseStrategy` | `two_minute_multi_symbol_buy_trailing_then_sell_trailing` 조회 가능 |
| `list_all` | `() -> list[str]` | 전략 D ID 포함 |

### 3.3 MarketData 입력 데이터 계약

| 항목 | 타입 | 규칙 |
|------|------|------|
| `candles_by_symbol[symbol]` | DataFrame | 컬럼 `timestamp, open, high, low, close, volume` 필수 |
| `timestamp` | tz-aware datetime | KST, 오름차순, 중복 없음 |
| `interval` | string | `2m` 고정 |
| `09:03` 캔들 | row | 종목별 필수 |

---

## 4. 모델/시그니처 상세 (구현용)

### 4.1 입력/상태/결정 모델

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any
import pandas as pd

@dataclass(slots=True)
class StrategyDInput:
    symbols: list[str]
    candles_by_symbol: dict[str, pd.DataFrame]
    seed_money: Decimal
    trade_date: date

@dataclass(slots=True)
class StrategyDSymbolState:
    symbol: str
    reference_price_0903: Decimal
    drop_triggered: bool = False
    lowest_price_since_trigger: Decimal | None = None
    last_evaluated_time: datetime | None = None

@dataclass(slots=True)
class StrategyDGlobalState:
    is_bought: bool = False
    position_symbol: str | None = None
    buy_price: Decimal | None = None
    buy_quantity: int = 0
    last_action: str = "NONE"
    highest_profit_rate: Decimal = Decimal("0")
    is_trailing_started: bool = False

@dataclass(slots=True)
class SingleEntryDecision:
    has_entry: bool
    selected_symbol: str | None
    entry_price: Decimal | None
    entry_time: datetime | None
    reason: str
    meta: dict[str, Any] = field(default_factory=dict)
```

### 4.2 전략 D 클래스 시그니처

```python
class TwoMinuteMultiSymbolBuyTrailingThenSellTrailingStrategy(BaseStrategy):
    def name(self) -> str: ...
    def required_interval(self) -> str: ...
    def required_reference_time(self) -> str: ...

    def evaluate_multi_symbol(self, strategy_input: StrategyDInput) -> list[TradeSignal]: ...
    def initialize_states(self, strategy_input: StrategyDInput) -> tuple[StrategyDGlobalState, dict[str, StrategyDSymbolState]]: ...

    def evaluate_entry_at_time(
        self,
        ts: datetime,
        symbols: list[str],
        candles_by_symbol: dict[str, pd.DataFrame],
        state_by_symbol: dict[str, StrategyDSymbolState],
        global_state: StrategyDGlobalState,
        seed_money: Decimal,
    ) -> SingleEntryDecision: ...

    def should_sell(self, current_price: Decimal, global_state: StrategyDGlobalState) -> bool: ...
    def build_buy_signal(self, decision: SingleEntryDecision, qty: int, trade_date: date) -> TradeSignal: ...
    def build_sell_signal(self, ts: datetime, price: Decimal, global_state: StrategyDGlobalState, trade_date: date) -> TradeSignal: ...
```

### 4.3 검증 함수 시그니처

```python
def validate_strategy_d_input(strategy_input: StrategyDInput) -> None: ...
def validate_symbols(symbols: list[str]) -> None: ...
def validate_candles_by_symbol(symbols: list[str], candles_by_symbol: dict[str, pd.DataFrame], required_interval: str) -> None: ...
def ensure_reference_candle_0903(symbol: str, candles: pd.DataFrame) -> None: ...
```

---

## 5. 예외 처리 규칙

### 5.1 오류 코드

| 코드 | 예외 타입 | 조건 | 치명도 |
|------|-----------|------|--------|
| `INVALID_SYMBOLS_COUNT` | `StrategyInputError` | symbols 길이 1~20 위반 | 치명 |
| `INVALID_SYMBOL_FORMAT` | `StrategyInputError` | 코드 포맷 불일치 | 치명 |
| `DUPLICATE_SYMBOLS` | `StrategyInputError` | 중복 종목 | 치명 |
| `SYMBOL_CANDLES_MISSING` | `StrategyInputError` | 종목 캔들 누락 | 치명 |
| `INTERVAL_MISMATCH_2M_REQUIRED` | `StrategyInputError` | 2분봉 아님 | 치명 |
| `REFERENCE_CANDLE_0903_MISSING` | `StrategyInputError` | 09:03 캔들 없음 | 치명 |
| `INSUFFICIENT_SEED_MONEY` | `InsufficientSeedMoneyError` | `floor(seed/price)==0` | 비치명 |
| `ALTERNATION_RULE_VIOLATION` | `AlternationRuleViolationError` | `BUY->BUY` 시도 | 비치명 |
| `STRATEGY_D_EXECUTION_ERROR` | `StrategyExecutionError` | 상태 전이/연산 오류 | 치명 |

### 5.2 처리 정책

1. 치명 입력 오류: 즉시 예외 발생 후 거래일 실패.
2. `INSUFFICIENT_SEED_MONEY`: 해당 시점 엔트리만 스킵, 다음 2분봉 진행.
3. `ALTERNATION_RULE_VIOLATION`: 매수 거절, `meta.alternation_blocked=true` 기록 후 진행.
4. 실행 오류: `STRATEGY_D_EXECUTION_ERROR`로 래핑해 상위 전파.

---

## 6. 구현 절차 (주니어 개발자용)

1. `models.py`에 `StrategyDInput`, `StrategyDSymbolState`, `StrategyDGlobalState`, `SingleEntryDecision`를 추가한다.
2. `errors.py`에 전략 D 오류 코드 상수와 예외 타입 매핑을 추가한다.
3. `strategy_input_validator.py`에 4개 검증 함수(`validate_strategy_d_input` 등)를 구현한다.
4. 신규 파일 `two_minute_multi_symbol_buy_trailing_then_sell_trailing_strategy.py`를 생성한다.
5. `name`은 `two_minute_multi_symbol_buy_trailing_then_sell_trailing`, `required_interval`은 `2m`, `required_reference_time`은 `09:03`으로 고정한다.
6. `initialize_states`에서 종목별 `reference_price_0903=open@09:03`를 읽어 상태를 만든다.
7. 각 2분봉 시각마다 미보유 상태면 `evaluate_entry_at_time`을 호출해 후보를 계산한다.
8. 후보 계산은 입력 순서대로 순회하며 하락 1.0% 트리거 후 전저점 대비 반등 0.2% 충족 시 후보에 넣는다.
9. 후보가 여러 개면 첫 후보 1건만 선택한다. 선택 근거는 `meta.policy=FIRST_CANDIDATE_BY_INPUT_ORDER`로 남긴다.
10. `qty=floor(seed_money/entry_price)` 계산 후 0이면 매수 스킵하고 다음 캔들로 진행한다.
11. 보유 중에는 보유 종목만 trailing 매도 규칙(수익률 1.0% 시작, 이익보전율 80% 이하 매도)으로 평가한다.
12. 매도 후 상태를 초기화하고 `last_action=SELL`로 갱신한다. 연속 BUY 시도는 거절한다.

---

## 7. 상세 알고리즘

### 7.1 엔트리 판단

```text
입력: ts, symbols(입력순서), candles_by_symbol, state_by_symbol, global_state, seed_money
출력: SingleEntryDecision

1) global_state.is_bought가 True면 NO_CANDIDATE 반환
2) candidates=[]
3) symbols를 입력순서로 순회
   - candle(close@ts) 미존재면 continue
   - drop_rate=((ref_0903-close)/ref_0903)*100
   - drop_triggered=False and drop_rate>=1.0 이면
       drop_triggered=True, lowest=close, continue
   - drop_triggered=True면 lowest=min(lowest, close)
     rebound_rate=((close-lowest)/lowest)*100
     rebound_rate>=0.2이면 candidates에 추가
4) candidates가 비면 NO_CANDIDATE 반환
5) selected=candidates[0]
6) qty=floor(seed_money/selected.price)
7) qty<=0이면 NO_CANDIDATE + error=INSUFFICIENT_SEED_MONEY 반환
8) has_entry=True로 selected 1건 반환
```

### 7.2 매도 판단

```text
profit_rate=((current_price-buy_price)/buy_price)*100

- profit_rate>=1.0 and trailing 미시작:
  trailing 시작, highest_profit_rate=profit_rate
- trailing 시작 후:
  highest_profit_rate=max(highest_profit_rate, profit_rate)
  preserve_ratio=(profit_rate/highest_profit_rate)*100
  preserve_ratio<=80이면 매도
```

---

## 8. 구현 완료 체크리스트

- [ ] 전략 D 클래스가 고정 ID/2분봉/09:03 기준 계약을 만족한다.
- [ ] 함수 시그니처와 반환 모델이 본 문서와 일치한다.
- [ ] 동시 후보 발생 시 입력 순서 첫 후보 1건만 선택된다.
- [ ] 보유 중 추가 매수 금지 및 `BUY->BUY` 차단이 동작한다.
- [ ] `INSUFFICIENT_SEED_MONEY`는 스킵 처리되고 시뮬레이션이 계속된다.
- [ ] trailing 매도 규칙(1.0% 시작, 80% 보전율)이 동작한다.
- [ ] 치명 입력 오류는 즉시 실패로 전파된다.

---

## 9. 추적성 (LLD v1.3.0 → ILD v1.3.0)

| LLD 항목 | ILD 반영 |
|----------|----------|
| 입력 계약(2.2) | 3.1, 4.1, 4.3, 5.1 |
| 단일 시그널 계약(2.3) | 4.1, 4.2, 7.1 |
| 후보 선택 정책(4.x) | 3.1, 6, 7.1 |
| 매수/매도 규칙(6.x) | 6, 7 |
| 제약 CON-009~011 | 5, 6, 8 |
| 오류 코드/정책(7.x) | 5 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.3.0 | 2026-02-16 | 전략 D 구현수준 명세 신규 작성 | ILD 담당 에이전트 |
