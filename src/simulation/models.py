from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SimulationRequest:
    symbol: str
    strategy_name: str
    initial_seed: Decimal | None = None
    symbols: list[str] | None = None


@dataclass
class SeedState:
    balance: Decimal
    initial: Decimal
    last_updated: datetime


@dataclass(frozen=True)
class DailyCandles:
    trade_date: date
    candles: pd.DataFrame
    rsi: pd.DataFrame | None


@dataclass(frozen=True)
class SellCosts:
    tax: Decimal
    fee: Decimal
    net_sell_amount: Decimal


@dataclass(frozen=True)
class ProfitResult:
    tax: Decimal
    fee: Decimal
    net_sell_amount: Decimal
    net_profit: Decimal
    profit_rate: Decimal


@dataclass(frozen=True)
class TradeRecord:
    trade_date: date
    buy_datetime: datetime | None
    buy_price: Decimal | None
    buy_quantity: int
    buy_amount: Decimal
    sell_datetime: datetime | None
    sell_price: Decimal | None
    sell_quantity: int
    sell_amount: Decimal
    tax: Decimal
    fee: Decimal
    net_profit: Decimal
    profit_rate: Decimal
    sell_reason: str
    seed_money_after: Decimal
    symbol_code: str | None = None


@dataclass(frozen=True)
class TradeExecutionResult:
    trade_record: TradeRecord
    seed_state_after: SeedState
    committed: bool


@dataclass(frozen=True)
class DayProcessResult:
    trade_record: TradeRecord
    seed_state_after: SeedState
    commit: bool


@dataclass(frozen=True)
class SimulationResult:
    simulation_id: str
    symbol: str
    strategy: str
    start_date: date
    end_date: date
    initial_seed: Decimal
    final_seed: Decimal
    total_profit: Decimal
    total_profit_rate: Decimal
    total_trades: int
    no_trade_days: int
    error_skip_days: int
    status: str
    trades: list[TradeRecord] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
