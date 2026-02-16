from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from .constants import (
    CACHE_TTL_MIN,
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    DEFAULT_TIMEOUT_SEC,
    MARKETDATA_REQUIRED_COLUMNS,
    RETRY_BACKOFF_SECONDS,
    RETRY_MAX_ATTEMPTS,
    SUPPORTED_INTERVALS,
    SUPPORTED_PERIODS,
    SYMBOL_PATTERN,
)
from .errors import (
    ERROR_CODES,
    CalculationError,
    DataIntegrityError,
    ExternalAPIError,
    NoDataError,
    StorageError,
    ValidationError,
)
from .market_data_cache_repository import MarketDataCacheRepository
from .market_data_validator import MarketDataValidator
from .rsi_calculator import RSICalculator
from .yahoo_finance_client import YahooFinanceClient


class MarketDataService:
    def __init__(
        self,
        cache_repository: MarketDataCacheRepository | None = None,
        yahoo_client: YahooFinanceClient | None = None,
        validator: MarketDataValidator | None = None,
        rsi_calculator: RSICalculator | None = None,
    ) -> None:
        self.cache_repository = cache_repository or MarketDataCacheRepository()
        self.yahoo_client = yahoo_client or YahooFinanceClient()
        self.validator = validator or MarketDataValidator()
        self.rsi_calculator = rsi_calculator or RSICalculator()

    def fetch_market_data_with_rsi(
        self,
        symbol: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
    ) -> pd.DataFrame:
        self._validate_symbol(symbol)
        self._validate_query_params(period, interval)
        interval_minutes = self._parse_interval_minutes(interval)

        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        from_ts, to_ts = self._resolve_range(now_kst, period)

        should_use_cache = interval == DEFAULT_INTERVAL
        cached_df = pd.DataFrame()
        if should_use_cache:
            cached_df = self.cache_repository.read_by_symbol_period_interval(symbol, from_ts, to_ts)

        if should_use_cache and not cached_df.empty and self.is_cache_fresh(symbol, period, interval, now_kst):
            self.validate_market_data(cached_df)
            return cached_df.reset_index()

        last_error: ExternalAPIError | None = None

        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                raw_df = self.yahoo_client.fetch_ohlcv(
                    symbol=symbol,
                    period=period,
                    interval=interval,
                    auto_adjust=True,
                    timeout_sec=DEFAULT_TIMEOUT_SEC,
                )

                normalized_df = self.validator.normalize_columns(raw_df)
                normalized_df = self.validator.normalize_timezone(normalized_df)
                filtered_df = self.validator.filter_trading_session(
                    normalized_df,
                    interval_minutes=interval_minutes,
                )
                self.validate_market_data(filtered_df)

                rsi_series = self.rsi_calculator.calculate_rsi(filtered_df, period=14)
                enriched_df = filtered_df.copy()
                enriched_df["rsi"] = rsi_series
                fetched_at = datetime.now(timezone.utc)
                enriched_df["fetched_at"] = fetched_at.isoformat()

                if should_use_cache:
                    self.upsert_market_data_cache(enriched_df, symbol, fetched_at)

                return enriched_df.reset_index()
            except ExternalAPIError as exc:
                if exc.code not in (ERROR_CODES["E_MD_006"], ERROR_CODES["E_MD_007"]):
                    raise
                last_error = exc
                if attempt < RETRY_MAX_ATTEMPTS:
                    time.sleep(RETRY_BACKOFF_SECONDS[attempt - 1])
                    continue
                raise ExternalAPIError(
                    ERROR_CODES["E_MD_008"],
                    "yahoo_api_retry_exhausted",
                    cause=last_error,
                ) from exc
            except (ValidationError, NoDataError, DataIntegrityError, CalculationError, StorageError):
                raise

        raise ExternalAPIError(
            ERROR_CODES["E_MD_008"],
            "yahoo_api_retry_exhausted",
            cause=last_error,
        )

    def validate_market_data(self, df: pd.DataFrame) -> None:
        required_columns = set(MARKETDATA_REQUIRED_COLUMNS)
        if isinstance(df, pd.DataFrame) and required_columns.issubset(df.columns):
            self.validator.validate_integrity(df)
            return

        normalized_df = self.validator.normalize_columns(df)
        normalized_df = self.validator.normalize_timezone(normalized_df)
        filtered_df = self.validator.filter_trading_session(normalized_df)
        self.validator.validate_integrity(filtered_df)

    def is_cache_fresh(self, symbol: str, period: str, interval: str, now_kst: datetime) -> bool:
        _ = period
        _ = interval
        return self.cache_repository.is_cache_fresh(
            symbol,
            now_kst,
            ttl_min=CACHE_TTL_MIN,
        )

    def upsert_market_data_cache(self, df: pd.DataFrame, symbol: str, fetched_at: datetime) -> int:
        if fetched_at.tzinfo is None:
            fetched_at_utc = fetched_at.replace(tzinfo=timezone.utc)
        else:
            fetched_at_utc = fetched_at.astimezone(timezone.utc)

        rows = self._to_cache_rows(df)
        return self.cache_repository.upsert_market_data_cache(
            symbol,
            rows,
            fetched_at_utc.isoformat(),
        )

    @staticmethod
    def _validate_symbol(symbol: str) -> None:
        if not re.match(SYMBOL_PATTERN, symbol):
            raise ValidationError(ERROR_CODES["E_MD_001"], "invalid_symbol_format")

    @staticmethod
    def _validate_query_params(period: str, interval: str) -> None:
        if period not in SUPPORTED_PERIODS or interval not in SUPPORTED_INTERVALS:
            raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval")

    @staticmethod
    def _parse_interval_minutes(interval: str) -> int:
        if not interval.endswith("m"):
            raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval")

        try:
            minutes = int(interval[:-1])
        except ValueError as exc:
            raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval") from exc

        if minutes <= 0:
            raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval")
        return minutes

    @staticmethod
    def _resolve_range(now_kst: datetime, period: str) -> tuple[datetime, datetime]:
        if period.endswith("d"):
            days = int(period[:-1])
            return now_kst - timedelta(days=days), now_kst
        raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval")

    @staticmethod
    def _to_cache_rows(df: pd.DataFrame) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for idx, row in df.iterrows():
            timestamp = str(idx)
            rows.append(
                {
                    "timestamp": timestamp,
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "rsi": row.get("rsi"),
                    "fetched_at": row.get("fetched_at"),
                }
            )
        return rows
