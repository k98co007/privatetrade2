from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class SellReason(str, Enum):
    PROFIT_PRESERVE = "PROFIT_PRESERVE"
    STOP_LOSS = "STOP_LOSS"
    NO_TRADE = "NO_TRADE"


@dataclass
class TradeContext:
    trade_date: date
    reference_price: Decimal | None = None
    low_point: Decimal | None = None
    buy_price: Decimal | None = None
    buy_quantity: int = 0
    buy_datetime: datetime | None = None
    is_bought: bool = False
    is_trailing_started: bool = False
    highest_profit_rate: Decimal = Decimal("0")
    latest_profit_rate: Decimal = Decimal("0")
    sell_reason: SellReason | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeSignal:
    has_trade: bool
    trade_date: date
    buy_datetime: datetime | None = None
    buy_price: Decimal | None = None
    buy_quantity: int = 0
    sell_datetime: datetime | None = None
    sell_price: Decimal | None = None
    sell_reason: SellReason = SellReason.NO_TRADE
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyExecutionResult:
    signal: TradeSignal
    error_code: str | None = None
