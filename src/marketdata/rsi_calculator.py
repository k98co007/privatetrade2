from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import DEFAULT_RSI_PERIOD
from .errors import ERROR_CODES, CalculationError, ValidationError


class RSICalculator:
    def calculate_rsi(self, candles_df: pd.DataFrame, period: int = DEFAULT_RSI_PERIOD) -> pd.Series:
        if "close" not in candles_df.columns:
            raise ValidationError(ERROR_CODES["E_MD_003"], "missing_required_columns")

        if period <= 0:
            raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval")

        if len(candles_df) < period + 1:
            return pd.Series(np.nan, index=candles_df.index, name="rsi", dtype="float64")

        try:
            close = candles_df["close"].astype("float64")
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = (-delta).clip(lower=0)

            avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

            rs = avg_gain / avg_loss.replace(0.0, np.nan)
            rsi = 100.0 - (100.0 / (1.0 + rs))

            both_zero_mask = (avg_gain == 0) & (avg_loss == 0)
            only_loss_zero_mask = (avg_loss == 0) & (avg_gain > 0)

            rsi = rsi.mask(both_zero_mask, 50.0)
            rsi = rsi.mask(only_loss_zero_mask, 100.0)
            rsi = rsi.clip(0.0, 100.0)
            rsi.name = "rsi"
            return rsi
        except ValidationError:
            raise
        except Exception as exc:
            raise CalculationError(
                ERROR_CODES["E_MD_012"],
                "rsi_calculation_failed",
                cause=exc,
            ) from exc
