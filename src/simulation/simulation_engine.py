from __future__ import annotations

import re
import uuid
from decimal import Decimal
from typing import Any

import pandas as pd

from marketdata.errors import DataIntegrityError as MarketDataIntegrityError
from marketdata.errors import NoDataError
from marketdata.market_data_service import MarketDataService
from strategy.errors import StrategyExecutionError as StrategyModuleExecutionError
from strategy.errors import StrategyInputError
from strategy.errors import StrategyNotFoundError as StrategyModuleNotFoundError
from strategy.strategy_registry import StrategyRegistry

from .constants import (
    DEFAULT_INITIAL_SEED,
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    ERROR_CODES,
    MANDATORY_CANDLE_TIMES,
    MAX_TRADING_DAYS,
    SELL_REASON_ERROR_SKIP,
    SELL_REASON_NO_TRADE,
    STATUS_COMPLETED,
    STATUS_RUNNING,
    SYMBOL_PATTERN,
)
from .cost_calculator import CostCalculator
from .errors import (
    DataIntegrityError,
    DataUnavailableError,
    DayProcessingError,
    MissingMandatoryCandleError,
    SimulationFatalError,
    SimulationValidationError,
    StrategyExecutionError,
    StrategyNotFoundError,
)
from .models import DailyCandles, DayProcessResult, SeedState, SimulationRequest, SimulationResult, TradeRecord
from .precision import floor_to_won
from .seed_money_manager import SeedMoneyManager
from .simulation_event_emitter import SimulationEventEmitter
from .trade_executor import TradeExecutor


class SimulationEngine:
    def __init__(
        self,
        market_data_service: MarketDataService | None = None,
        strategy_registry: StrategyRegistry | None = None,
        event_emitter: SimulationEventEmitter | None = None,
        seed_money_manager: SeedMoneyManager | None = None,
        cost_calculator: CostCalculator | None = None,
        trade_executor: TradeExecutor | None = None,
    ) -> None:
        self.market_data_service = market_data_service or MarketDataService()
        self.strategy_registry = strategy_registry or StrategyRegistry()
        if not self.strategy_registry.list_all():
            self.strategy_registry.register_defaults()
        self.event_emitter = event_emitter or SimulationEventEmitter()
        self.seed_money_manager = seed_money_manager or SeedMoneyManager()
        self.cost_calculator = cost_calculator or CostCalculator()
        self.trade_executor = trade_executor or TradeExecutor(
            cost_calculator=self.cost_calculator,
            seed_money_manager=self.seed_money_manager,
        )

    def run_simulation(self, request: SimulationRequest) -> SimulationResult:
        self._validate_request(request)

        try:
            strategy = self._load_strategy(request.strategy_name)
            interval = self._resolve_strategy_interval(strategy)
            seed_state = self.seed_money_manager.initialize(
                request.initial_seed if request.initial_seed is not None else DEFAULT_INITIAL_SEED
            )
            candles = self.market_data_service.fetch_market_data_with_rsi(
                symbol=request.symbol,
                period=DEFAULT_PERIOD,
                interval=interval,
            )
            days = self.split_trading_days(candles)

            trades: list[TradeRecord] = []
            no_trade_days = 0
            error_skip_days = 0

            for index, day_data in enumerate(days, start=1):
                seed_before_day = SeedState(
                    balance=seed_state.balance,
                    initial=seed_state.initial,
                    last_updated=seed_state.last_updated,
                )
                try:
                    day_result = self.process_one_day(day_data, seed_state, strategy)
                    if day_result.commit:
                        seed_state = day_result.seed_state_after
                        trades.append(day_result.trade_record)

                        if day_result.trade_record.sell_reason == SELL_REASON_NO_TRADE:
                            no_trade_days += 1
                            self.event_emitter.emit_warning(
                                ERROR_CODES["E_SIM_010"],
                                "no_trade_day",
                                day_data.trade_date,
                            )
                        elif day_result.trade_record.sell_reason == SELL_REASON_ERROR_SKIP:
                            error_skip_days += 1
                            self.event_emitter.emit_warning(
                                ERROR_CODES["E_SIM_007"],
                                "error_skip_day",
                                day_data.trade_date,
                            )
                        else:
                            self.event_emitter.emit_trade(day_result.trade_record)
                except MissingMandatoryCandleError as exc:
                    seed_state = seed_before_day
                    trades.append(
                        self.trade_executor.build_no_trade_record(
                            day_data.trade_date,
                            "missing_mandatory_candle",
                            seed_state.balance,
                        )
                    )
                    no_trade_days += 1
                    self.event_emitter.emit_warning(exc.code, exc.message, day_data.trade_date)
                except DayProcessingError as exc:
                    seed_state = seed_before_day
                    trades.append(
                        self.trade_executor.build_no_trade_record(
                            day_data.trade_date,
                            SELL_REASON_ERROR_SKIP,
                            seed_state.balance,
                        )
                    )
                    error_skip_days += 1
                    self.event_emitter.emit_warning(exc.code, exc.message, day_data.trade_date)

                self.event_emitter.emit_progress(
                    current_day=index,
                    total_days=len(days),
                    trading_date=day_data.trade_date,
                    status=STATUS_RUNNING,
                )

            result = self._build_simulation_result(
                request=request,
                days=days,
                final_seed_state=seed_state,
                trades=trades,
                no_trade_days=no_trade_days,
                error_skip_days=error_skip_days,
            )
            self.event_emitter.emit_completed(
                simulation_id=result.simulation_id,
                final_seed=result.final_seed,
                summary={
                    "total_trades": result.total_trades,
                    "no_trade_days": result.no_trade_days,
                    "error_skip_days": result.error_skip_days,
                },
            )
            return result
        except SimulationFatalError:
            raise
        except Exception as exc:
            self.event_emitter.emit_error(
                ERROR_CODES["E_SIM_014"],
                "simulation_fatal_error",
                detail=str(exc),
            )
            raise SimulationFatalError(
                ERROR_CODES["E_SIM_014"],
                "simulation_fatal_error",
                cause=exc,
            ) from exc

    def split_trading_days(self, candles_df: pd.DataFrame) -> list[DailyCandles]:
        if candles_df is None or candles_df.empty:
            raise DataUnavailableError(
                ERROR_CODES["E_SIM_003"],
                "empty_market_data",
            )

        if "timestamp" not in candles_df.columns:
            raise DataIntegrityError(
                ERROR_CODES["E_SIM_004"],
                "timestamp_column_missing",
            )

        normalized = candles_df.copy()
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")
        if normalized["timestamp"].isnull().any():
            raise DataIntegrityError(
                ERROR_CODES["E_SIM_004"],
                "invalid_timestamp_found",
            )

        normalized = normalized.sort_values("timestamp")
        normalized["trade_date"] = normalized["timestamp"].dt.date

        daily: list[DailyCandles] = []
        for trade_date, day_df in normalized.groupby("trade_date", sort=True):
            candles = day_df.drop(columns=["trade_date"]).reset_index(drop=True)
            rsi_df = candles[["timestamp", "rsi"]].copy() if "rsi" in candles.columns else None
            daily.append(
                DailyCandles(
                    trade_date=trade_date,
                    candles=candles,
                    rsi=rsi_df,
                )
            )

        if not daily:
            raise DataIntegrityError(
                ERROR_CODES["E_SIM_004"],
                "no_trading_days_after_split",
            )

        if len(daily) > MAX_TRADING_DAYS:
            daily = daily[-MAX_TRADING_DAYS:]
        return daily

    def process_one_day(self, day_data: DailyCandles, seed_state: SeedState, strategy: Any) -> DayProcessResult:
        try:
            self._validate_mandatory_candles(day_data.candles, strategy)
            signal = strategy.evaluate(
                daily_candles=day_data.candles,
                rsi_data=day_data.rsi,
                seed_money=seed_state.balance,
            )
        except MissingMandatoryCandleError:
            raise
        except (StrategyInputError, StrategyModuleExecutionError) as exc:
            raise StrategyExecutionError(
                ERROR_CODES["E_SIM_006"],
                "strategy_evaluation_failed",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise DayProcessingError(
                ERROR_CODES["E_SIM_007"],
                "day_processing_failed",
                cause=exc,
            ) from exc

        try:
            execution = self.trade_executor.execute(signal, day_data, seed_state)
            return DayProcessResult(
                trade_record=execution.trade_record,
                seed_state_after=execution.seed_state_after,
                commit=execution.committed,
            )
        except Exception as exc:
            if isinstance(exc, DayProcessingError):
                raise
            raise DayProcessingError(
                ERROR_CODES["E_SIM_007"],
                "day_trade_execution_failed",
                cause=exc,
            ) from exc

    def _validate_request(self, request: SimulationRequest) -> None:
        if not re.match(SYMBOL_PATTERN, request.symbol):
            raise SimulationValidationError(
                ERROR_CODES["E_SIM_001"],
                "invalid_symbol_format",
            )
        if not request.strategy_name:
            raise SimulationValidationError(
                ERROR_CODES["E_SIM_001"],
                "strategy_name_required",
            )
        if request.initial_seed is not None and request.initial_seed <= Decimal("0"):
            raise SimulationValidationError(
                ERROR_CODES["E_SIM_002"],
                "initial_seed_must_be_positive",
            )

    def _load_strategy(self, strategy_name: str) -> Any:
        try:
            return self.strategy_registry.get(strategy_name)
        except StrategyModuleNotFoundError as exc:
            raise StrategyNotFoundError(
                ERROR_CODES["E_SIM_005"],
                "strategy_not_found",
                cause=exc,
            ) from exc

    def _validate_mandatory_candles(self, candles: pd.DataFrame, strategy: Any) -> None:
        if "timestamp" not in candles.columns:
            raise MissingMandatoryCandleError(
                ERROR_CODES["E_SIM_009"],
                "timestamp_column_missing",
            )

        required_times = tuple(getattr(strategy, "required_times", MANDATORY_CANDLE_TIMES))
        interval_minutes = getattr(strategy, "required_interval_minutes", 1)
        missing = [
            value
            for value in required_times
            if not self._has_required_time(candles, value, interval_minutes)
        ]
        if missing:
            raise MissingMandatoryCandleError(
                ERROR_CODES["E_SIM_009"],
                f"missing_mandatory_candle_times:{','.join(missing)}",
            )

    @staticmethod
    def _has_required_time(candles: pd.DataFrame, required_time: str, interval_minutes: int) -> bool:
        hhmm_series = candles["timestamp"].dt.strftime("%H:%M")
        if (hhmm_series == required_time).any():
            return True

        target_minutes = SimulationEngine._parse_hhmm_to_minutes(required_time)
        if target_minutes is None:
            return False

        try:
            interval = int(interval_minutes)
        except (TypeError, ValueError):
            interval = 1

        if interval <= 1:
            return False

        day_minutes = candles["timestamp"].dt.hour * 60 + candles["timestamp"].dt.minute
        window_end = target_minutes + interval - 1
        return ((day_minutes >= target_minutes) & (day_minutes <= window_end)).any()

    @staticmethod
    def _parse_hhmm_to_minutes(hhmm: str) -> int | None:
        parts = hhmm.split(":")
        if len(parts) != 2:
            return None

        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError:
            return None

        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None

        return hour * 60 + minute

    @staticmethod
    def _resolve_strategy_interval(strategy: Any) -> str:
        raw_interval_minutes = getattr(strategy, "required_interval_minutes", None)
        try:
            interval_minutes = int(raw_interval_minutes)
        except (TypeError, ValueError):
            return DEFAULT_INTERVAL

        if interval_minutes <= 0:
            return DEFAULT_INTERVAL
        return f"{interval_minutes}m"

    def _build_simulation_result(
        self,
        request: SimulationRequest,
        days: list[DailyCandles],
        final_seed_state: SeedState,
        trades: list[TradeRecord],
        no_trade_days: int,
        error_skip_days: int,
    ) -> SimulationResult:
        initial_seed = final_seed_state.initial
        final_seed = floor_to_won(final_seed_state.balance)
        total_profit = floor_to_won(final_seed - initial_seed)
        if initial_seed == Decimal("0"):
            total_profit_rate = Decimal("0")
        else:
            total_profit_rate = (total_profit / initial_seed) * Decimal("100")

        return SimulationResult(
            simulation_id=str(uuid.uuid4()),
            symbol=request.symbol,
            strategy=request.strategy_name,
            start_date=days[0].trade_date,
            end_date=days[-1].trade_date,
            initial_seed=initial_seed,
            final_seed=final_seed,
            total_profit=total_profit,
            total_profit_rate=total_profit_rate,
            total_trades=len(trades),
            no_trade_days=no_trade_days,
            error_skip_days=error_skip_days,
            status=STATUS_COMPLETED,
            trades=trades,
            meta={
                "days_processed": len(days),
            },
        )
