from __future__ import annotations

from decimal import Decimal

import pandas as pd

from .constants import ERROR_CODES, RSI_BUY_THRESHOLD, RSI_ONLY_TRAILING_STOP, TIME_0905
from .models import TradeContext
from .sell_trailing_stop_strategy import SellTrailingStopStrategy


class RSIOnlyTrailingStopStrategy(SellTrailingStopStrategy):
    required_times: tuple[str, ...] = (TIME_0905,)

    def name(self) -> str:
        return RSI_ONLY_TRAILING_STOP

    def should_buy(self, candle: pd.Series, context: TradeContext, rsi_value: float | None = None) -> bool:
        if rsi_value is None:
            context.meta["last_skip_reason"] = ERROR_CODES["E_ST_006"]
            return False

        if Decimal(str(rsi_value)) <= RSI_BUY_THRESHOLD:
            context.meta["rsi_at_entry"] = rsi_value
            return True

        return False

    def should_stop_loss(self, candle: pd.Series, context: TradeContext) -> bool:
        return False
