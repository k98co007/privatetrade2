from __future__ import annotations

from decimal import Decimal

import pandas as pd

from .buy_sell_trailing_stop_strategy import BuySellTrailingStopStrategy
from .constants import ERROR_CODES, RSI_BUY_SELL_TRAILING_STOP, RSI_BUY_THRESHOLD
from .models import TradeContext


class RSIBuySellTrailingStopStrategy(BuySellTrailingStopStrategy):
    def name(self) -> str:
        return RSI_BUY_SELL_TRAILING_STOP

    def should_buy(self, candle: pd.Series, context: TradeContext, rsi_value: float | None = None) -> bool:
        if not super().should_buy(candle, context, None):
            return False

        if rsi_value is None:
            context.meta["last_skip_reason"] = ERROR_CODES["E_ST_006"]
            return False

        if Decimal(str(rsi_value)) <= RSI_BUY_THRESHOLD:
            context.meta["rsi_at_entry"] = rsi_value
            return True

        return False
