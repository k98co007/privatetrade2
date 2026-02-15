from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR
from typing import Any

import pandas as pd

from .constants import ERROR_CODES, PROFIT_TRIGGER_RATE, TIME_0905
from .errors import StrategyExecutionError, StrategyInputError
from .models import SellReason, TradeContext, TradeSignal
from .strategy_input_validator import StrategyInputValidator


class BaseStrategy(ABC):
    required_times: tuple[str, ...] = (TIME_0905,)

    def __init__(self, input_validator: StrategyInputValidator | None = None) -> None:
        self.input_validator = input_validator or StrategyInputValidator()

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def initialize_day(self, candle_0905: pd.Series, seed_money: Decimal) -> TradeContext:
        raise NotImplementedError

    @abstractmethod
    def should_buy(self, candle: pd.Series, context: TradeContext, rsi_value: float | None = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def should_sell(self, candle: pd.Series, context: TradeContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def should_stop_loss(self, candle: pd.Series, context: TradeContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def resolve_stop_loss_fill(self, daily_candles: pd.DataFrame) -> tuple[datetime, Decimal]:
        raise NotImplementedError

    def evaluate(
        self,
        daily_candles: pd.DataFrame,
        rsi_data: pd.DataFrame | None,
        seed_money: Decimal,
    ) -> TradeSignal:
        try:
            normalized_candles, normalized_rsi = self.input_validator.validate_inputs(
                daily_candles=daily_candles,
                rsi_data=rsi_data,
                required_times=self.required_times,
            )
            candle_0905 = self._must_find_candle(normalized_candles, TIME_0905)
            context = self.initialize_day(candle_0905, seed_money)
            rsi_lookup = self._build_rsi_lookup(normalized_rsi)

            for _, candle in normalized_candles.iterrows():
                candle_ts = candle["timestamp"]

                if not context.is_bought:
                    rsi_value = self._lookup_rsi(rsi_lookup, candle_ts)
                    if self.should_buy(candle, context, rsi_value):
                        buy_price = self._to_decimal(candle["close"])
                        quantity = int((seed_money / buy_price).to_integral_value(rounding=ROUND_FLOOR))
                        if quantity <= 0:
                            return self._build_no_trade_signal(context, ERROR_CODES["E_ST_007"])

                        context.is_bought = True
                        context.buy_datetime = candle_ts
                        context.buy_price = buy_price
                        context.buy_quantity = quantity
                    continue

                if context.buy_price is None:
                    raise StrategyExecutionError(
                        ERROR_CODES["E_ST_008"],
                        "strategy_execution_failed",
                    )

                context.latest_profit_rate = self._calc_profit_rate(context.buy_price, candle["close"])
                if context.latest_profit_rate >= PROFIT_TRIGGER_RATE:
                    context.is_trailing_started = True
                    context.highest_profit_rate = max(context.highest_profit_rate, context.latest_profit_rate)

                if self.should_sell(candle, context):
                    context.sell_reason = SellReason.PROFIT_PRESERVE
                    return self._build_signal(
                        context=context,
                        sell_ts=candle_ts,
                        sell_price=self._to_decimal(candle["close"]),
                        reason=SellReason.PROFIT_PRESERVE,
                    )

                if self.should_stop_loss(candle, context):
                    stop_ts, stop_price = self.resolve_stop_loss_fill(normalized_candles)
                    context.sell_reason = SellReason.STOP_LOSS
                    return self._build_signal(
                        context=context,
                        sell_ts=stop_ts,
                        sell_price=stop_price,
                        reason=SellReason.STOP_LOSS,
                    )

            return self._build_no_trade_signal(context)
        except (StrategyInputError, StrategyExecutionError):
            raise
        except Exception as exc:
            raise StrategyExecutionError(
                ERROR_CODES["E_ST_008"],
                "strategy_execution_failed",
                cause=exc,
            ) from exc

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        return Decimal(str(value))

    @classmethod
    def _calc_profit_rate(cls, buy_price: Decimal, now_price: Any) -> Decimal:
        now = cls._to_decimal(now_price)
        return ((now - buy_price) / buy_price) * Decimal("100")

    @staticmethod
    def _calc_preserve_ratio(current_profit: Decimal, highest_profit: Decimal) -> Decimal:
        if highest_profit <= Decimal("0"):
            return Decimal("0")
        return (current_profit / highest_profit) * Decimal("100")

    @staticmethod
    def _lookup_rsi(rsi_lookup: dict[datetime, float | None] | None, ts: datetime) -> float | None:
        if rsi_lookup is None:
            return None
        return rsi_lookup.get(ts)

    @staticmethod
    def _build_rsi_lookup(rsi_data: pd.DataFrame | None) -> dict[datetime, float | None] | None:
        if rsi_data is None:
            return None

        lookup: dict[datetime, float | None] = {}
        for _, row in rsi_data.iterrows():
            value = row["rsi"]
            lookup[row["timestamp"]] = None if pd.isna(value) else float(value)
        return lookup

    def _build_signal(
        self,
        context: TradeContext,
        sell_ts: datetime,
        sell_price: Decimal,
        reason: SellReason,
    ) -> TradeSignal:
        preserve_ratio = self._calc_preserve_ratio(context.latest_profit_rate, context.highest_profit_rate)
        meta = {
            "highest_profit_rate": str(context.highest_profit_rate),
            "latest_profit_rate": str(context.latest_profit_rate),
            "preserve_ratio": str(preserve_ratio),
        }
        meta.update(context.meta)
        return TradeSignal(
            has_trade=True,
            trade_date=context.trade_date,
            buy_datetime=context.buy_datetime,
            buy_price=context.buy_price,
            buy_quantity=context.buy_quantity,
            sell_datetime=sell_ts,
            sell_price=sell_price,
            sell_reason=reason,
            meta=meta,
        )

    def _build_no_trade_signal(self, context: TradeContext, error_code: str | None = None) -> TradeSignal:
        meta = {
            "highest_profit_rate": str(context.highest_profit_rate),
            "latest_profit_rate": str(context.latest_profit_rate),
            "preserve_ratio": str(self._calc_preserve_ratio(context.latest_profit_rate, context.highest_profit_rate)),
        }
        if error_code is not None:
            meta["error_code"] = error_code
        meta.update(context.meta)
        return TradeSignal(
            has_trade=False,
            trade_date=context.trade_date,
            buy_datetime=context.buy_datetime,
            buy_price=context.buy_price,
            buy_quantity=context.buy_quantity,
            sell_datetime=None,
            sell_price=None,
            sell_reason=SellReason.NO_TRADE,
            meta=meta,
        )

    @staticmethod
    def _must_find_candle(daily_candles: pd.DataFrame, hhmm: str) -> pd.Series:
        matched = daily_candles[daily_candles["timestamp"].dt.strftime("%H:%M") == hhmm]
        if matched.empty:
            raise StrategyInputError(
                ERROR_CODES["E_ST_004"],
                "strategy_input_missing_mandatory_candle",
            )
        return matched.iloc[0]
