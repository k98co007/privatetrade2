from __future__ import annotations

from decimal import Decimal

import pandas as pd

from .buy_trailing_then_sell_trailing_strategy import BuyTrailingThenSellTrailingStrategy
from .constants import THREE_MINUTE_BUY_TRAILING_THEN_SELL_TRAILING, TIME_0903
from .models import TradeContext


class ThreeMinuteBuyTrailingThenSellTrailingStrategy(BuyTrailingThenSellTrailingStrategy):
    required_times: tuple[str, ...] = (TIME_0903,)
    required_reference_time: str = TIME_0903
    required_interval_minutes: int = 2

    def name(self) -> str:
        return THREE_MINUTE_BUY_TRAILING_THEN_SELL_TRAILING

    def initialize_day(self, candle_0903: pd.Series, seed_money: Decimal) -> TradeContext:
        return TradeContext(
            trade_date=candle_0903["timestamp"].date(),
            reference_price=self._to_decimal(candle_0903["open"]),
            low_point=None,
        )

    def should_buy(self, candle: pd.Series, context: TradeContext, rsi_value: float | None = None) -> bool:
        if candle["timestamp"].strftime("%H:%M") <= TIME_0903:
            return False

        if context.reference_price is None:
            return False

        current_close = self._to_decimal(candle["close"])
        drop_rate = ((context.reference_price - current_close) / context.reference_price) * Decimal("100")

        if context.low_point is None:
            if drop_rate >= Decimal("1.0"):
                context.low_point = current_close
            return False

        context.low_point = min(context.low_point, current_close)
        rebound_rate = ((current_close - context.low_point) / context.low_point) * Decimal("100")
        context.meta["rebound_rate"] = str(rebound_rate)
        return rebound_rate >= Decimal("0.2")
