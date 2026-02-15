from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class ProfitSummary:
    initial_seed: Decimal
    final_seed: Decimal
    total_profit: Decimal
    total_profit_rate: Decimal


@dataclass(frozen=True)
class TradeDetail:
    trade_id: int
    trade_date: str
    buy_datetime: str | None
    buy_price: Decimal | None
    buy_quantity: int
    buy_amount: Decimal
    sell_datetime: str | None
    sell_price: Decimal | None
    sell_quantity: int
    sell_amount: Decimal
    sell_reason: str
    sell_reason_display: str
    tax: Decimal
    fee: Decimal
    net_profit: Decimal
    profit_rate: Decimal
    seed_money_after: Decimal


@dataclass(frozen=True)
class ReportSummary:
    total_trades: int
    profit_trades: int
    loss_trades: int
    flat_trades: int
    no_trade_days: int
    total_profit_amount: Decimal
    total_loss_amount: Decimal
    win_rate: Decimal


@dataclass(frozen=True)
class ReportWarning:
    code: str
    message: str
    trade_date: str | None = None


@dataclass(frozen=True)
class SimulationMeta:
    simulation_id: str
    symbol: str
    strategy: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class ComprehensiveReport:
    schema_version: str
    simulation_id: str
    symbol: str
    strategy: str
    period: dict[str, str]
    profit_summary: ProfitSummary
    summary: ReportSummary
    trades: list[TradeDetail]
    warnings: list[ReportWarning] = field(default_factory=list)
