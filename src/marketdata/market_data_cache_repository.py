from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd

from .constants import CACHE_TTL_MIN
from .errors import ERROR_CODES, StorageError


class MarketDataCacheRepository:
    def __init__(self, db_path: str = "market_data_cache.db") -> None:
        self.db_path = Path(db_path)
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _ensure_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS market_data_cache (
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            rsi REAL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, timestamp)
        );
        """
        try:
            with self._connect() as conn:
                conn.execute(sql)
                conn.commit()
        except Exception as exc:
            raise StorageError(
                ERROR_CODES["E_MD_011"],
                "market_data_cache_storage_failed",
                cause=exc,
            ) from exc

    def read_by_symbol_period_interval(
        self,
        symbol: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> pd.DataFrame:
        query = """
        SELECT symbol, timestamp, open, high, low, close, volume, rsi, fetched_at
        FROM market_data_cache
        WHERE symbol = ?
          AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC;
        """
        try:
            with self._connect() as conn:
                df = pd.read_sql_query(
                    query,
                    conn,
                    params=(symbol, from_ts.isoformat(), to_ts.isoformat()),
                )
        except Exception as exc:
            raise StorageError(
                ERROR_CODES["E_MD_011"],
                "market_data_cache_storage_failed",
                cause=exc,
            ) from exc

        if df.empty:
            return df

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], errors="coerce", utc=True)
        df = df.set_index("timestamp")
        df.index.name = "timestamp"
        return df

    def get_latest_timestamp(self, symbol: str) -> datetime | None:
        query = """
        SELECT MAX(timestamp) AS max_ts
        FROM market_data_cache
        WHERE symbol = ?;
        """
        try:
            with self._connect() as conn:
                row = conn.execute(query, (symbol,)).fetchone()
        except Exception as exc:
            raise StorageError(
                ERROR_CODES["E_MD_011"],
                "market_data_cache_storage_failed",
                cause=exc,
            ) from exc

        if row is None or row[0] is None:
            return None

        latest = pd.to_datetime(row[0], errors="coerce")
        if pd.isna(latest):
            return None
        if latest.tzinfo is None:
            latest = latest.tz_localize(ZoneInfo("Asia/Seoul"))
        return latest.to_pydatetime()

    def is_cache_fresh(
        self,
        symbol: str,
        now_kst: datetime,
        ttl_min: int = CACHE_TTL_MIN,
    ) -> bool:
        latest = self.get_latest_timestamp(symbol)
        if latest is None:
            return False

        if now_kst.tzinfo is None:
            now_kst = now_kst.replace(tzinfo=ZoneInfo("Asia/Seoul"))

        freshness_threshold = now_kst - timedelta(minutes=ttl_min)
        return latest >= freshness_threshold

    def upsert_market_data_cache(
        self,
        symbol: str,
        rows: Iterable[dict[str, Any]],
        fetched_at_utc: str,
    ) -> int:
        sql = """
        INSERT INTO market_data_cache (
            symbol, timestamp, open, high, low, close, volume, rsi, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, timestamp) DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            volume = excluded.volume,
            rsi = excluded.rsi,
            fetched_at = excluded.fetched_at;
        """

        prepared_rows = []
        for row in rows:
            rsi_value = row.get("rsi")
            if rsi_value is None or pd.isna(rsi_value):
                normalized_rsi = None
            else:
                normalized_rsi = float(rsi_value)

            prepared_rows.append(
                (
                    symbol,
                    str(row["timestamp"]),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    int(row["volume"]),
                    normalized_rsi,
                    str(row.get("fetched_at", fetched_at_utc)),
                )
            )

        if not prepared_rows:
            return 0

        for attempt in (1, 2):
            connection = None
            try:
                connection = self._connect()
                cursor = connection.executemany(sql, prepared_rows)
                connection.commit()
                return cursor.rowcount if cursor.rowcount is not None else len(prepared_rows)
            except Exception as exc:
                if connection is not None:
                    try:
                        connection.rollback()
                    except Exception:
                        pass
                if attempt == 2:
                    raise StorageError(
                        ERROR_CODES["E_MD_011"],
                        "market_data_cache_storage_failed",
                        cause=exc,
                    ) from exc
            finally:
                if connection is not None:
                    connection.close()

        return 0
