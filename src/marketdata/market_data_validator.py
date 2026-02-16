from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from .constants import MARKETDATA_REQUIRED_COLUMNS
from .errors import (
    ERROR_CODES,
    DataIntegrityError,
    NoDataError,
    ValidationError,
)


class MarketDataValidator:
    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame):
            raise ValidationError(ERROR_CODES["E_MD_003"], "missing_required_columns")

        if df.empty:
            raise NoDataError(ERROR_CODES["E_MD_005"], "no_market_data")

        normalized = df.copy()
        normalized.columns = [str(col).strip() for col in normalized.columns]
        normalized = normalized.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

        missing = [col for col in MARKETDATA_REQUIRED_COLUMNS if col not in normalized.columns]
        if missing:
            raise ValidationError(ERROR_CODES["E_MD_003"], "missing_required_columns")

        if not isinstance(normalized.index, pd.DatetimeIndex):
            if "timestamp" in normalized.columns:
                normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")
                normalized = normalized.set_index("timestamp")
            else:
                raise ValidationError(ERROR_CODES["E_MD_003"], "missing_required_columns")

        normalized.index.name = "timestamp"
        normalized = normalized.loc[:, list(MARKETDATA_REQUIRED_COLUMNS)]

        for column in ("open", "high", "low", "close"):
            normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        normalized["volume"] = pd.to_numeric(normalized["volume"], errors="raise").astype("int64")

        return normalized

    def normalize_timezone(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValidationError(ERROR_CODES["E_MD_010"], "timezone_normalization_failed")

        try:
            output = df.copy()
            idx = pd.DatetimeIndex(output.index)
            if idx.tz is None:
                output.index = idx.tz_localize(ZoneInfo("Asia/Seoul"))
            else:
                output.index = idx.tz_convert(ZoneInfo("Asia/Seoul"))
            output.index.name = "timestamp"
            return output
        except Exception as exc:
            raise ValidationError(
                ERROR_CODES["E_MD_010"],
                "timezone_normalization_failed",
                cause=exc,
            ) from exc

    def filter_trading_session(self, df: pd.DataFrame, interval_minutes: int = 5) -> pd.DataFrame:
        if df.empty:
            raise NoDataError(ERROR_CODES["E_MD_005"], "no_market_data")

        if interval_minutes <= 0:
            raise ValidationError(ERROR_CODES["E_MD_003"], "missing_required_columns")

        idx = pd.DatetimeIndex(df.index)
        output = df[idx.weekday < 5]
        output = output.between_time("09:00", "15:30")

        if not output.empty:
            output = self._filter_by_interval_anchor(output, interval_minutes)

        if output.empty:
            raise NoDataError(ERROR_CODES["E_MD_005"], "no_market_data")

        return output

    @staticmethod
    def _filter_by_interval_anchor(df: pd.DataFrame, interval_minutes: int) -> pd.DataFrame:
        filtered_frames: list[pd.DataFrame] = []
        index = pd.DatetimeIndex(df.index)
        by_date = pd.Series(index=index, data=index.date)

        for trade_date in by_date.unique():
            date_mask = by_date == trade_date
            day_df = df[date_mask.to_numpy()]
            if day_df.empty:
                continue

            day_idx = pd.DatetimeIndex(day_df.index)
            anchor_minute = int(day_idx[0].hour) * 60 + int(day_idx[0].minute)
            day_minutes = day_idx.hour * 60 + day_idx.minute
            keep_mask = ((day_minutes - anchor_minute) % interval_minutes) == 0
            filtered_frames.append(day_df[keep_mask])

        if not filtered_frames:
            return df.iloc[0:0]

        return pd.concat(filtered_frames).sort_index()

    def validate_integrity(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise NoDataError(ERROR_CODES["E_MD_005"], "no_market_data")

        missing = [col for col in MARKETDATA_REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValidationError(ERROR_CODES["E_MD_003"], "missing_required_columns")

        if df[list(MARKETDATA_REQUIRED_COLUMNS)].isna().any().any():
            raise ValidationError(ERROR_CODES["E_MD_004"], "invalid_market_data_structure")

        if not df.index.is_monotonic_increasing or not df.index.is_unique:
            raise ValidationError(ERROR_CODES["E_MD_004"], "invalid_market_data_structure")

        if (df["high"] < df["low"]).any():
            raise DataIntegrityError(ERROR_CODES["E_MD_009"], "market_data_integrity_violation")

        if ((df["open"] < df["low"]) | (df["open"] > df["high"])).any():
            raise DataIntegrityError(ERROR_CODES["E_MD_009"], "market_data_integrity_violation")

        if ((df["close"] < df["low"]) | (df["close"] > df["high"])).any():
            raise DataIntegrityError(ERROR_CODES["E_MD_009"], "market_data_integrity_violation")

        if (df["volume"] < 0).any():
            raise DataIntegrityError(ERROR_CODES["E_MD_009"], "market_data_integrity_violation")
