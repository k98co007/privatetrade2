from __future__ import annotations

import re
from typing import Any

import pandas as pd
import yfinance as yf

from .constants import (
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    DEFAULT_TIMEOUT_SEC,
    SUPPORTED_INTERVALS,
    SUPPORTED_PERIODS,
    SYMBOL_PATTERN,
)
from .errors import ERROR_CODES, ExternalAPIError, NoDataError, ValidationError


class YahooFinanceClient:
    def fetch_ohlcv(
        self,
        symbol: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
        auto_adjust: bool = True,
        timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    ) -> pd.DataFrame:
        if not re.match(SYMBOL_PATTERN, symbol):
            raise ValidationError(ERROR_CODES["E_MD_001"], "invalid_symbol_format")

        if period not in SUPPORTED_PERIODS or interval not in SUPPORTED_INTERVALS:
            raise ValidationError(ERROR_CODES["E_MD_002"], "invalid_period_or_interval")

        try:
            data = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                threads=False,
                progress=False,
                timeout=timeout_sec,
            )
        except Exception as exc:
            if self._is_temporary_failure(exc):
                raise ExternalAPIError(
                    ERROR_CODES["E_MD_006"],
                    "yahoo_api_temporary_failure",
                    cause=exc,
                ) from exc
            raise ExternalAPIError(
                ERROR_CODES["E_MD_007"],
                "yahoo_api_unexpected_payload",
                cause=exc,
            ) from exc

        if not isinstance(data, pd.DataFrame):
            raise ExternalAPIError(ERROR_CODES["E_MD_007"], "yahoo_api_unexpected_payload")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [
                col[0] if isinstance(col, tuple) else col for col in data.columns.to_list()
            ]

        expected = {"Open", "High", "Low", "Close", "Volume"}
        if not expected.issubset(set(data.columns)):
            raise ExternalAPIError(ERROR_CODES["E_MD_007"], "yahoo_api_unexpected_payload")

        if data.empty:
            raise NoDataError(ERROR_CODES["E_MD_005"], "no_market_data")

        return data

    @staticmethod
    def _is_temporary_failure(exc: Exception) -> bool:
        temporary_names = {"TimeoutError", "ConnectionError"}
        if exc.__class__.__name__ in temporary_names:
            return True
        message = str(exc).lower()
        keywords = ("timeout", "tempor", "connection", "reset", "network")
        return any(keyword in message for keyword in keywords)
