from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd

from .base_strategy import BaseStrategy
from .constants import (
    BUY_SELL_TRAILING_STOP,
    ENTRY_DROP_RATE,
    PRESERVE_RATIO_THRESHOLD,
    REBOUND_RATE,
    TIME_0905,
    TIME_1500,
)
from .models import TradeContext


class BuySellTrailingStopStrategy(BaseStrategy):
    required_times: tuple[str, ...] = (TIME_0905, TIME_1500)

    def name(self) -> str:
        return BUY_SELL_TRAILING_STOP

    def initialize_day(self, candle_0905: pd.Series, seed_money: Decimal) -> TradeContext:
        return TradeContext(
            trade_date=candle_0905["timestamp"].date(),
            reference_price=self._to_decimal(candle_0905["close"]),
            low_point=None,
        )

    def should_buy(self, candle: pd.Series, context: TradeContext, rsi_value: float | None = None) -> bool:
        if candle["timestamp"].strftime("%H:%M") <= TIME_0905:
            return False

        if context.reference_price is None:
            return False

        current_close = self._to_decimal(candle["close"])
        drop_rate = ((context.reference_price - current_close) / context.reference_price) * Decimal("100")

        if context.low_point is None:
            if drop_rate >= ENTRY_DROP_RATE:
                context.low_point = current_close
            return False

        context.low_point = min(context.low_point, current_close)
        rebound_rate = ((current_close - context.low_point) / context.low_point) * Decimal("100")
        context.meta["rebound_rate"] = str(rebound_rate)
        return rebound_rate >= REBOUND_RATE

    def should_sell(self, candle: pd.Series, context: TradeContext) -> bool:
        if not context.is_trailing_started:
            return False

        preserve_ratio = self._calc_preserve_ratio(context.latest_profit_rate, context.highest_profit_rate)
        context.meta["preserve_ratio"] = str(preserve_ratio)
        return preserve_ratio <= PRESERVE_RATIO_THRESHOLD

    def should_stop_loss(self, candle: pd.Series, context: TradeContext) -> bool:
        return candle["timestamp"].strftime("%H:%M") == TIME_1500 and not context.is_trailing_started

    def resolve_stop_loss_fill(self, daily_candles: pd.DataFrame) -> tuple[datetime, Decimal]:
        candle_1500 = self._must_find_candle(daily_candles, TIME_1500)
        return candle_1500["timestamp"], self._to_decimal(candle_1500["close"])
