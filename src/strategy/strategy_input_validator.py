from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from .constants import ERROR_CODES, RSI_REQUIRED_COLUMNS, STRATEGY_REQUIRED_CANDLE_COLUMNS
from .errors import StrategyInputError


class StrategyInputValidator:
    def validate_inputs(
        self,
        daily_candles: pd.DataFrame,
        rsi_data: pd.DataFrame | None,
        required_times: tuple[str, ...],
    ) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        candles = self._normalize_candles(daily_candles)
        self._validate_required_times(candles, required_times)

        normalized_rsi: pd.DataFrame | None = None
        if rsi_data is not None:
            normalized_rsi = self._normalize_rsi(rsi_data)
            self._validate_rsi_alignment(candles, normalized_rsi)

        return candles, normalized_rsi

    def _normalize_candles(self, daily_candles: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(daily_candles, pd.DataFrame) or daily_candles.empty:
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        candles = daily_candles.copy()
        if "timestamp" not in candles.columns:
            if isinstance(candles.index, pd.DatetimeIndex):
                candles = candles.reset_index().rename(columns={candles.index.name or "index": "timestamp"})
            else:
                raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        missing = [col for col in STRATEGY_REQUIRED_CANDLE_COLUMNS if col not in candles.columns]
        if missing:
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        candles = candles.loc[:, list(STRATEGY_REQUIRED_CANDLE_COLUMNS)].copy()
        candles["timestamp"] = pd.to_datetime(candles["timestamp"], errors="coerce")
        if candles["timestamp"].isna().any():
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        if candles["timestamp"].dt.tz is None:
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        candles["timestamp"] = candles["timestamp"].dt.tz_convert(ZoneInfo("Asia/Seoul"))
        candles = candles.sort_values("timestamp").reset_index(drop=True)

        if candles["timestamp"].duplicated().any():
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        ts = candles["timestamp"].dt
        if ((ts.minute % 5) != 0).any() or (ts.second != 0).any() or (ts.microsecond != 0).any():
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        for column in ("open", "high", "low", "close"):
            candles[column] = pd.to_numeric(candles[column], errors="coerce")
        candles["volume"] = pd.to_numeric(candles["volume"], errors="coerce")

        if candles[list(STRATEGY_REQUIRED_CANDLE_COLUMNS[1:])].isna().any().any():
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        if (candles["high"] < candles["low"]).any():
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")
        if ((candles["open"] < candles["low"]) | (candles["open"] > candles["high"]) ).any():
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")
        if ((candles["close"] < candles["low"]) | (candles["close"] > candles["high"]) ).any():
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")
        if (candles["volume"] < 0).any():
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        return candles

    def _normalize_rsi(self, rsi_data: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(rsi_data, pd.DataFrame) or rsi_data.empty:
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        rsi_frame = rsi_data.copy()
        if "timestamp" not in rsi_frame.columns:
            if isinstance(rsi_frame.index, pd.DatetimeIndex):
                rsi_frame = rsi_frame.reset_index().rename(
                    columns={rsi_frame.index.name or "index": "timestamp"}
                )
            else:
                raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        missing = [col for col in RSI_REQUIRED_COLUMNS if col not in rsi_frame.columns]
        if missing:
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        rsi_frame = rsi_frame.loc[:, list(RSI_REQUIRED_COLUMNS)].copy()
        rsi_frame["timestamp"] = pd.to_datetime(rsi_frame["timestamp"], errors="coerce")
        if rsi_frame["timestamp"].isna().any():
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        if rsi_frame["timestamp"].dt.tz is None:
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        rsi_frame["timestamp"] = rsi_frame["timestamp"].dt.tz_convert(ZoneInfo("Asia/Seoul"))
        rsi_frame = rsi_frame.sort_values("timestamp").reset_index(drop=True)

        if rsi_frame["timestamp"].duplicated().any():
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")

        rsi_frame["rsi"] = pd.to_numeric(rsi_frame["rsi"], errors="coerce")
        non_nan_rsi = rsi_frame["rsi"].dropna()
        if ((non_nan_rsi < 0) | (non_nan_rsi > 100)).any():
            raise StrategyInputError(ERROR_CODES["E_ST_003"], "strategy_input_missing_columns")

        return rsi_frame

    def _validate_required_times(self, candles: pd.DataFrame, required_times: tuple[str, ...]) -> None:
        times = set(candles["timestamp"].dt.strftime("%H:%M").tolist())
        for required_time in required_times:
            if required_time not in times:
                raise StrategyInputError(
                    ERROR_CODES["E_ST_004"],
                    "strategy_input_missing_mandatory_candle",
                )

    def _validate_rsi_alignment(self, candles: pd.DataFrame, rsi_frame: pd.DataFrame) -> None:
        candle_ts = candles["timestamp"].tolist()
        rsi_ts = rsi_frame["timestamp"].tolist()
        if candle_ts != rsi_ts:
            raise StrategyInputError(ERROR_CODES["E_ST_005"], "strategy_input_invalid_timestamp")
