from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from simulation.models import TradeRecord

from .constants import ERROR_CODES, NO_TRADE_REASON_CODES, SELL_REASON_KO_MAP, SORT_ASC, SORT_DESC, VALID_SORT_ORDERS
from .errors import ReportValidationError
from .models import TradeDetail


class TradeHistoryFormatter:
    def format_trade_history(
        self,
        trades: list[TradeRecord],
        include_no_trade: bool = True,
        sort_order: str = SORT_ASC,
    ) -> list[TradeDetail]:
        sorted_records = self.sort_trade_records(trades, sort_order=sort_order)
        sequenced_records = self.assign_trade_sequence(sorted_records)

        details: list[TradeDetail] = []
        for sequence, record in sequenced_records:
            normalized = self.normalize_trade_record(record)
            if not include_no_trade and normalized.sell_reason in NO_TRADE_REASON_CODES:
                continue

            details.append(
                TradeDetail(
                    trade_id=sequence,
                    trade_date=self._format_date(normalized.trade_date),
                    symbol_code=normalized.symbol_code,
                    buy_datetime=self._format_datetime(normalized.buy_datetime),
                    buy_price=normalized.buy_price,
                    buy_quantity=normalized.buy_quantity,
                    buy_amount=normalized.buy_amount,
                    sell_datetime=self._format_datetime(normalized.sell_datetime),
                    sell_price=normalized.sell_price,
                    sell_quantity=normalized.sell_quantity,
                    sell_amount=normalized.sell_amount,
                    sell_reason=normalized.sell_reason,
                    sell_reason_display=self.map_sell_reason(normalized.sell_reason),
                    tax=normalized.tax,
                    fee=normalized.fee,
                    net_profit=normalized.net_profit,
                    profit_rate=normalized.profit_rate,
                    seed_money_after=normalized.seed_money_after,
                )
            )
        return details

    def sort_trade_records(self, records: list[TradeRecord], sort_order: str = SORT_ASC) -> list[TradeRecord]:
        if sort_order not in VALID_SORT_ORDERS:
            raise ReportValidationError(ERROR_CODES["E_RP_003"], "invalid_sort_order")

        enumerated = list(enumerate(records, start=1))

        def key(item: tuple[int, TradeRecord]) -> tuple:
            index, record = item
            buy_datetime = record.buy_datetime
            is_null = buy_datetime is None
            trade_date = record.trade_date
            trade_id = self._extract_trade_id(record, fallback=index)
            return (is_null, buy_datetime, trade_date, trade_id)

        sorted_enumerated = sorted(enumerated, key=key)
        if sort_order == SORT_DESC:
            non_null = [pair for pair in sorted_enumerated if pair[1].buy_datetime is not None]
            nulls = [pair for pair in sorted_enumerated if pair[1].buy_datetime is None]
            non_null = list(reversed(non_null))
            sorted_enumerated = non_null + nulls

        return [record for _, record in sorted_enumerated]

    def assign_trade_sequence(self, sorted_records: list[TradeRecord]) -> list[tuple[int, TradeRecord]]:
        return list(enumerate(sorted_records, start=1))

    def map_sell_reason(self, reason_code: str) -> str:
        code = str(reason_code).lower()
        if code not in SELL_REASON_KO_MAP:
            raise ReportValidationError(ERROR_CODES["E_RP_002"], "invalid_sell_reason")
        return SELL_REASON_KO_MAP[code]

    def normalize_trade_record(self, record: TradeRecord) -> TradeRecord:
        if record.trade_date is None:
            raise ReportValidationError(ERROR_CODES["E_RP_002"], "trade_date_required")
        if record.sell_reason is None:
            raise ReportValidationError(ERROR_CODES["E_RP_002"], "sell_reason_required")

        numeric_fields = [
            record.buy_amount,
            record.sell_amount,
            record.tax,
            record.fee,
            record.net_profit,
            record.profit_rate,
            record.seed_money_after,
        ]
        if any(value is None for value in numeric_fields):
            raise ReportValidationError(ERROR_CODES["E_RP_002"], "trade_numeric_field_required")
        if any(not isinstance(value, Decimal) for value in numeric_fields):
            raise ReportValidationError(ERROR_CODES["E_RP_002"], "trade_numeric_field_must_be_decimal")

        return record

    @staticmethod
    def _format_date(value: date) -> str:
        return value.strftime("%Y-%m-%d")

    @staticmethod
    def _format_datetime(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _extract_trade_id(record: TradeRecord, fallback: int) -> int:
        trade_id = getattr(record, "trade_id", None)
        if isinstance(trade_id, int):
            return trade_id
        return fallback
