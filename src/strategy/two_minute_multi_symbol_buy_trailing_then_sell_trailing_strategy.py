from __future__ import annotations

from .three_minute_buy_trailing_then_sell_trailing_strategy import ThreeMinuteBuyTrailingThenSellTrailingStrategy
from .constants import TWO_MINUTE_MULTI_SYMBOL_BUY_TRAILING_THEN_SELL_TRAILING


class TwoMinuteMultiSymbolBuyTrailingThenSellTrailingStrategy(ThreeMinuteBuyTrailingThenSellTrailingStrategy):
    def name(self) -> str:
        return TWO_MINUTE_MULTI_SYMBOL_BUY_TRAILING_THEN_SELL_TRAILING
