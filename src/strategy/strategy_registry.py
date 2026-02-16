from __future__ import annotations

from .base_strategy import BaseStrategy
from .buy_trailing_then_sell_trailing_strategy import BuyTrailingThenSellTrailingStrategy
from .buy_sell_trailing_stop_strategy import BuySellTrailingStopStrategy
from .constants import ERROR_CODES
from .errors import DuplicateStrategyError, StrategyNotFoundError
from .rsi_buy_sell_trailing_stop_strategy import RSIBuySellTrailingStopStrategy
from .rsi_only_trailing_stop_strategy import RSIOnlyTrailingStopStrategy
from .sell_trailing_stop_strategy import SellTrailingStopStrategy
from .three_minute_buy_trailing_then_sell_trailing_strategy import ThreeMinuteBuyTrailingThenSellTrailingStrategy


class StrategyRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, BaseStrategy] = {}

    def register(self, strategy: BaseStrategy) -> None:
        strategy_name = strategy.name()
        if strategy_name in self._registry:
            raise DuplicateStrategyError(
                ERROR_CODES["E_ST_002"],
                "strategy_duplicate_registration",
            )
        self._registry[strategy_name] = strategy

    def get(self, name: str) -> BaseStrategy:
        if name not in self._registry:
            raise StrategyNotFoundError(ERROR_CODES["E_ST_001"], "strategy_not_found")
        return self._registry[name]

    def list_all(self) -> list[str]:
        return list(self._registry.keys())

    def register_defaults(self) -> None:
        self.register(SellTrailingStopStrategy())
        self.register(BuySellTrailingStopStrategy())
        self.register(RSIBuySellTrailingStopStrategy())
        self.register(RSIOnlyTrailingStopStrategy())
        self.register(BuyTrailingThenSellTrailingStrategy())
        self.register(ThreeMinuteBuyTrailingThenSellTrailingStrategy())
