from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

from simulation.models import SimulationResult, TradeRecord

from .constants import ERROR_CODES, SORT_ASC, SORT_DESC, VALID_SORT_ORDERS
from .errors import DuplicateKeyError, NotFoundError, StorageError


class ReportRepository:
    def __init__(self, db_path: str = "report.db") -> None:
        self.db_path = Path(db_path)
        self._tx_connection: sqlite3.Connection | None = None
        self._ensure_tables()

    def begin_transaction(self) -> None:
        if self._tx_connection is not None:
            return
        try:
            self._tx_connection = sqlite3.connect(str(self.db_path))
            self._tx_connection.execute("BEGIN")
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "begin_transaction_failed", cause=exc) from exc

    def commit(self) -> None:
        if self._tx_connection is None:
            return
        try:
            self._tx_connection.commit()
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "commit_failed", cause=exc) from exc
        finally:
            self._tx_connection.close()
            self._tx_connection = None

    def rollback(self) -> None:
        if self._tx_connection is None:
            return
        try:
            self._tx_connection.rollback()
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "rollback_failed", cause=exc) from exc
        finally:
            self._tx_connection.close()
            self._tx_connection = None

    def create_simulation_result(self, result: SimulationResult) -> None:
        sql = """
        INSERT INTO simulations (
            simulation_id, symbol, strategy, start_date, end_date,
            initial_seed, final_seed, total_profit, total_profit_rate,
            total_trades, no_trade_days, error_skip_days, status,
            created_at, updated_at, deleted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL);
        """
        payload = (
            result.simulation_id,
            result.symbol,
            result.strategy,
            result.start_date.isoformat(),
            result.end_date.isoformat(),
            str(result.initial_seed),
            str(result.final_seed),
            str(result.total_profit),
            str(result.total_profit_rate),
            int(result.total_trades),
            int(result.no_trade_days),
            int(result.error_skip_days),
            result.status,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
        )
        try:
            with self._cursor() as cursor:
                cursor.execute(sql, payload)
        except sqlite3.IntegrityError as exc:
            raise DuplicateKeyError(ERROR_CODES["E_RP_011"], "duplicate_simulation_id", cause=exc) from exc
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "create_simulation_result_failed", cause=exc) from exc

    def create_trade_records(self, simulation_id: str, trades: list[TradeRecord]) -> int:
        if not simulation_id:
            raise StorageError(ERROR_CODES["E_RP_011"], "simulation_id_required")
        if not trades:
            return 0

        sql = """
        INSERT INTO trades (
            simulation_id, trade_date, buy_datetime, buy_price, buy_quantity, buy_amount,
            sell_datetime, sell_price, sell_quantity, sell_amount,
            sell_reason, tax, fee, net_profit, profit_rate, seed_money_after, symbol_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        rows = [
            (
                simulation_id,
                trade.trade_date.isoformat(),
                None if trade.buy_datetime is None else trade.buy_datetime.isoformat(),
                None if trade.buy_price is None else str(trade.buy_price),
                trade.buy_quantity,
                str(trade.buy_amount),
                None if trade.sell_datetime is None else trade.sell_datetime.isoformat(),
                None if trade.sell_price is None else str(trade.sell_price),
                trade.sell_quantity,
                str(trade.sell_amount),
                str(trade.sell_reason).lower(),
                str(trade.tax),
                str(trade.fee),
                str(trade.net_profit),
                str(trade.profit_rate),
                str(trade.seed_money_after),
                trade.symbol_code,
            )
            for trade in trades
        ]

        try:
            with self._cursor() as cursor:
                cursor.executemany(sql, rows)
                return cursor.rowcount if cursor.rowcount is not None else len(rows)
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "create_trade_records_failed", cause=exc) from exc

    def read_simulation_result(self, simulation_id: str) -> SimulationResult | None:
        if not simulation_id:
            raise StorageError(ERROR_CODES["E_RP_011"], "simulation_id_required")

        sql = """
        SELECT
            simulation_id, symbol, strategy, start_date, end_date,
            initial_seed, final_seed, total_profit, total_profit_rate,
            total_trades, no_trade_days, error_skip_days, status
        FROM simulations
        WHERE simulation_id = ?
          AND deleted_at IS NULL
        LIMIT 1;
        """

        try:
            with self._cursor() as cursor:
                row = cursor.execute(sql, (simulation_id,)).fetchone()
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "read_simulation_result_failed", cause=exc) from exc

        if row is None:
            return None

        return SimulationResult(
            simulation_id=row["simulation_id"],
            symbol=row["symbol"],
            strategy=row["strategy"],
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]),
            initial_seed=Decimal(row["initial_seed"]),
            final_seed=Decimal(row["final_seed"]),
            total_profit=Decimal(row["total_profit"]),
            total_profit_rate=Decimal(row["total_profit_rate"]),
            total_trades=int(row["total_trades"]),
            no_trade_days=int(row["no_trade_days"]),
            error_skip_days=int(row["error_skip_days"]),
            status=row["status"],
            trades=[],
            meta={},
        )

    def read_trade_records(
        self,
        simulation_id: str,
        include_no_trade: bool = True,
        from_date: date | None = None,
        to_date: date | None = None,
        sort_order: str = SORT_ASC,
    ) -> list[TradeRecord]:
        if not simulation_id:
            raise StorageError(ERROR_CODES["E_RP_011"], "simulation_id_required")
        if sort_order not in VALID_SORT_ORDERS:
            raise StorageError(ERROR_CODES["E_RP_011"], "invalid_sort_order")

        sql = """
        SELECT
            trade_id, trade_date,
            buy_datetime, buy_price, buy_quantity, buy_amount,
            sell_datetime, sell_price, sell_quantity, sell_amount,
            sell_reason, tax, fee, net_profit, profit_rate, seed_money_after, symbol_code
        FROM trades
        WHERE simulation_id = ?
          AND (? = 1 OR sell_reason NOT IN ('no_trade', 'error_skip'))
          AND (? IS NULL OR trade_date >= ?)
          AND (? IS NULL OR trade_date <= ?)
        ORDER BY
          CASE WHEN buy_datetime IS NULL THEN 1 ELSE 0 END ASC,
          CASE WHEN ? = 'asc' THEN buy_datetime END ASC,
          CASE WHEN ? = 'desc' THEN buy_datetime END DESC,
          trade_date ASC,
          trade_id ASC;
        """
        params = (
            simulation_id,
            1 if include_no_trade else 0,
            None if from_date is None else from_date.isoformat(),
            None if from_date is None else from_date.isoformat(),
            None if to_date is None else to_date.isoformat(),
            None if to_date is None else to_date.isoformat(),
            sort_order,
            sort_order,
        )
        try:
            with self._cursor() as cursor:
                rows = cursor.execute(sql, params).fetchall()
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "read_trade_records_failed", cause=exc) from exc

        records: list[TradeRecord] = []
        for row in rows:
            records.append(
                TradeRecord(
                    trade_date=date.fromisoformat(row["trade_date"]),
                    buy_datetime=None if row["buy_datetime"] is None else datetime.fromisoformat(row["buy_datetime"]),
                    buy_price=None if row["buy_price"] is None else Decimal(row["buy_price"]),
                    buy_quantity=int(row["buy_quantity"]),
                    buy_amount=Decimal(row["buy_amount"]),
                    sell_datetime=None if row["sell_datetime"] is None else datetime.fromisoformat(row["sell_datetime"]),
                    sell_price=None if row["sell_price"] is None else Decimal(row["sell_price"]),
                    sell_quantity=int(row["sell_quantity"]),
                    sell_amount=Decimal(row["sell_amount"]),
                    tax=Decimal(row["tax"]),
                    fee=Decimal(row["fee"]),
                    net_profit=Decimal(row["net_profit"]),
                    profit_rate=Decimal(row["profit_rate"]),
                    sell_reason=row["sell_reason"],
                    seed_money_after=Decimal(row["seed_money_after"]),
                    symbol_code=row["symbol_code"],
                )
            )
        return records

    def update_simulation_summary(self, simulation_id: str, summary_fields: dict[str, Any]) -> None:
        if not simulation_id:
            raise StorageError(ERROR_CODES["E_RP_011"], "simulation_id_required")
        if not summary_fields:
            return

        allowed = {
            "final_seed",
            "total_profit",
            "total_profit_rate",
            "total_trades",
            "no_trade_days",
            "error_skip_days",
            "status",
        }
        keys = [key for key in summary_fields.keys() if key in allowed]
        if not keys:
            return

        set_clause = ", ".join([f"{key} = ?" for key in keys] + ["updated_at = ?"])
        sql = f"UPDATE simulations SET {set_clause} WHERE simulation_id = ? AND deleted_at IS NULL;"
        params = [self._normalize_summary_value(summary_fields[key]) for key in keys]
        params.append(datetime.utcnow().isoformat())
        params.append(simulation_id)

        try:
            with self._cursor() as cursor:
                cursor.execute(sql, tuple(params))
                if cursor.rowcount == 0:
                    raise NotFoundError(ERROR_CODES["E_RP_012"], "simulation_not_found_for_update")
        except NotFoundError:
            raise
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "update_simulation_summary_failed", cause=exc) from exc

    def delete_simulation(self, simulation_id: str, hard_delete: bool = False) -> int:
        if not simulation_id:
            raise StorageError(ERROR_CODES["E_RP_011"], "simulation_id_required")
        try:
            with self._cursor() as cursor:
                if hard_delete:
                    cursor.execute("DELETE FROM trades WHERE simulation_id = ?", (simulation_id,))
                    row = cursor.execute("DELETE FROM simulations WHERE simulation_id = ?", (simulation_id,))
                    return row.rowcount if row.rowcount is not None else 0

                row = cursor.execute(
                    "UPDATE simulations SET deleted_at = ?, updated_at = ? WHERE simulation_id = ? AND deleted_at IS NULL",
                    (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), simulation_id),
                )
                return row.rowcount if row.rowcount is not None else 0
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "delete_simulation_failed", cause=exc) from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        connection = self._tx_connection or self._connect()
        own_connection = self._tx_connection is None
        try:
            cursor = connection.cursor()
            yield cursor
            if own_connection:
                connection.commit()
        except Exception:
            if own_connection:
                connection.rollback()
            raise
        finally:
            if own_connection:
                connection.close()

    def _ensure_tables(self) -> None:
        simulations_sql = """
        CREATE TABLE IF NOT EXISTS simulations (
            simulation_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            strategy TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            initial_seed TEXT NOT NULL,
            final_seed TEXT NOT NULL,
            total_profit TEXT NOT NULL,
            total_profit_rate TEXT NOT NULL,
            total_trades INTEGER NOT NULL,
            no_trade_days INTEGER NOT NULL,
            error_skip_days INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT NULL
        );
        """
        trades_sql = """
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            buy_datetime TEXT NULL,
            buy_price TEXT NULL,
            buy_quantity INTEGER NOT NULL,
            buy_amount TEXT NOT NULL,
            sell_datetime TEXT NULL,
            sell_price TEXT NULL,
            sell_quantity INTEGER NOT NULL,
            sell_amount TEXT NOT NULL,
            sell_reason TEXT NOT NULL,
            tax TEXT NOT NULL,
            fee TEXT NOT NULL,
            net_profit TEXT NOT NULL,
            profit_rate TEXT NOT NULL,
            seed_money_after TEXT NOT NULL,
            symbol_code TEXT NULL,
            FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
        );
        """
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trades_simulation_id ON trades(simulation_id);",
            "CREATE INDEX IF NOT EXISTS idx_trades_sim_date ON trades(simulation_id, trade_date);",
            "CREATE INDEX IF NOT EXISTS idx_trades_sim_buydt ON trades(simulation_id, buy_datetime);",
            "CREATE INDEX IF NOT EXISTS idx_simulations_status ON simulations(status);",
        ]

        try:
            with self._cursor() as cursor:
                cursor.execute(simulations_sql)
                cursor.execute(trades_sql)
                trade_columns = {
                    str(row[1]).lower()
                    for row in cursor.execute("PRAGMA table_info(trades)").fetchall()
                }
                if "symbol_code" not in trade_columns:
                    cursor.execute("ALTER TABLE trades ADD COLUMN symbol_code TEXT NULL")
                for sql in indexes:
                    cursor.execute(sql)
        except Exception as exc:
            raise StorageError(ERROR_CODES["E_RP_011"], "ensure_tables_failed", cause=exc) from exc

    @staticmethod
    def _normalize_summary_value(value: Any) -> Any:
        if isinstance(value, Decimal):
            return str(value)
        return value
