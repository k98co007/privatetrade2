from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from .constants import (
    ERROR_CODES,
    SELL_REASON_NO_TRADE,
)
from .cost_calculator import CostCalculator
from .errors import TradeExecutionError
from .models import DailyCandles, SeedState, TradeExecutionResult, TradeRecord
from .precision import floor_to_won, round_display_percent, to_decimal
from .seed_money_manager import SeedMoneyManager


class TradeExecutor:
    def __init__(
        self,
        cost_calculator: CostCalculator | None = None,
        seed_money_manager: SeedMoneyManager | None = None,
    ) -> None:
        self.cost_calculator = cost_calculator or CostCalculator()
        self.seed_money_manager = seed_money_manager or SeedMoneyManager()

    def execute(
        self,
        day_signal: Any,
        day_data: DailyCandles,
        seed_state: SeedState,
    ) -> TradeExecutionResult:
        self.validate_signal(day_signal)

        if not bool(day_signal.has_trade):
            reason = self._normalize_reason(getattr(day_signal, "sell_reason", SELL_REASON_NO_TRADE))
            record = self.build_no_trade_record(day_data.trade_date, reason, seed_state.balance)
            return TradeExecutionResult(
                trade_record=record,
                seed_state_after=seed_state,
                committed=True,
            )

        try:
            buy_price = to_decimal(day_signal.buy_price)
            sell_price = to_decimal(day_signal.sell_price)
            buy_qty = int(day_signal.buy_quantity)
            sell_qty = buy_qty

            if buy_qty <= 0 or buy_price <= Decimal("0") or sell_price <= Decimal("0"):
                raise TradeExecutionError(
                    ERROR_CODES["E_SIM_013"],
                    "invalid_trade_signal_values",
                )

            buy_amount = floor_to_won(buy_price * Decimal(buy_qty))
            sell_amount = floor_to_won(sell_price * Decimal(sell_qty))

            profit = self.cost_calculator.calculate_net_profit(
                buy_amount=buy_amount,
                sell_amount=sell_amount,
            )
            seed_after = self.seed_money_manager.apply_trade_result(seed_state, profit.net_profit)

            record = TradeRecord(
                trade_date=day_data.trade_date,
                buy_datetime=day_signal.buy_datetime,
                buy_price=buy_price,
                buy_quantity=buy_qty,
                buy_amount=buy_amount,
                sell_datetime=day_signal.sell_datetime,
                sell_price=sell_price,
                sell_quantity=sell_qty,
                sell_amount=sell_amount,
                tax=profit.tax,
                fee=profit.fee,
                net_profit=profit.net_profit,
                profit_rate=round_display_percent(profit.profit_rate, 2),
                sell_reason=self._normalize_reason(day_signal.sell_reason),
                seed_money_after=seed_after.balance,
            )
            return TradeExecutionResult(
                trade_record=record,
                seed_state_after=seed_after,
                committed=True,
            )
        except TradeExecutionError:
            raise
        except Exception as exc:
            raise TradeExecutionError(
                ERROR_CODES["E_SIM_013"],
                "trade_execution_failed",
                cause=exc,
            ) from exc

    def build_no_trade_record(self, trade_date: date, reason: str, seed_after: Decimal) -> TradeRecord:
        seed_money_after = floor_to_won(to_decimal(seed_after))
        zero = Decimal("0")
        return TradeRecord(
            trade_date=trade_date,
            buy_datetime=None,
            buy_price=None,
            buy_quantity=0,
            buy_amount=zero,
            sell_datetime=None,
            sell_price=None,
            sell_quantity=0,
            sell_amount=zero,
            tax=zero,
            fee=zero,
            net_profit=zero,
            profit_rate=zero,
            sell_reason=self._normalize_reason(reason),
            seed_money_after=seed_money_after,
        )

    def validate_signal(self, signal: Any) -> None:
        has_trade = getattr(signal, "has_trade", None)
        trade_date = getattr(signal, "trade_date", None)
        if has_trade is None or trade_date is None:
            raise TradeExecutionError(
                ERROR_CODES["E_SIM_013"],
                "signal_missing_required_fields",
            )

        if bool(has_trade):
            required = ("buy_datetime", "buy_price", "buy_quantity", "sell_datetime", "sell_price")
            for field_name in required:
                if getattr(signal, field_name, None) is None:
                    raise TradeExecutionError(
                        ERROR_CODES["E_SIM_013"],
                        f"signal_missing_{field_name}",
                    )

    @staticmethod
    def _normalize_reason(reason: Any) -> str:
        value = str(getattr(reason, "value", reason)).lower()
        return value
