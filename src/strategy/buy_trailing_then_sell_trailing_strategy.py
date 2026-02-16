from __future__ import annotations

import pandas as pd

from .buy_sell_trailing_stop_strategy import BuySellTrailingStopStrategy
from .constants import BUY_TRAILING_THEN_SELL_TRAILING
from .models import TradeContext


class BuyTrailingThenSellTrailingStrategy(BuySellTrailingStopStrategy):
    def name(self) -> str:
        return BUY_TRAILING_THEN_SELL_TRAILING

    def should_stop_loss(self, candle: pd.Series, context: TradeContext) -> bool:
        return False
