from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd

from .base_strategy import BaseStrategy
from .constants import (
    PRESERVE_RATIO_THRESHOLD,
    SELL_TRAILING_STOP,
    TIME_0905,
    TIME_1500,
    TIME_1505,
)
from .models import TradeContext


class SellTrailingStopStrategy(BaseStrategy):
    required_times: tuple[str, ...] = (TIME_0905, TIME_1500, TIME_1505)

    def name(self) -> str:
        return SELL_TRAILING_STOP

    def initialize_day(self, candle_0905: pd.Series, seed_money: Decimal) -> TradeContext:
        return TradeContext(trade_date=candle_0905["timestamp"].date())

    def should_buy(self, candle: pd.Series, context: TradeContext, rsi_value: float | None = None) -> bool:
        return candle["timestamp"].strftime("%H:%M") == TIME_0905

    def should_sell(self, candle: pd.Series, context: TradeContext) -> bool:
        if not context.is_trailing_started:
            return False

        preserve_ratio = self._calc_preserve_ratio(context.latest_profit_rate, context.highest_profit_rate)
        context.meta["preserve_ratio"] = str(preserve_ratio)
        return preserve_ratio <= PRESERVE_RATIO_THRESHOLD

    def should_stop_loss(self, candle: pd.Series, context: TradeContext) -> bool:
        return candle["timestamp"].strftime("%H:%M") == TIME_1500 and not context.is_trailing_started

    def resolve_stop_loss_fill(self, daily_candles: pd.DataFrame) -> tuple[datetime, Decimal]:
        candle_1505 = self._must_find_candle(daily_candles, TIME_1505)
        return candle_1505["timestamp"], self._to_decimal(candle_1505["close"])
