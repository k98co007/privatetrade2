from __future__ import annotations

from decimal import Decimal

from .constants import (
    AMOUNT_QUANTIZER,
    AMOUNT_ROUNDING,
    DEFAULT_SCHEMA_VERSION,
    ERROR_CODES,
    RATE_QUANTIZER,
    RATE_ROUNDING,
    SUPPORTED_SCHEMA_VERSIONS,
)
from .errors import SchemaVersionError
from .models import ComprehensiveReport


def validate_schema_version(schema_version: str | None) -> str:
    version = schema_version or DEFAULT_SCHEMA_VERSION
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise SchemaVersionError(ERROR_CODES["E_RP_006"], "schema_version_not_supported")
    return version


def decimal_amount_to_string(value: Decimal) -> str:
    quantized = value.quantize(AMOUNT_QUANTIZER, rounding=AMOUNT_ROUNDING)
    return format(quantized, "f")


def decimal_rate_to_string(value: Decimal) -> str:
    quantized = value.quantize(RATE_QUANTIZER, rounding=RATE_ROUNDING)
    return format(quantized, "f")


def serialize_comprehensive_report(report: ComprehensiveReport) -> dict:
    return {
        "schema_version": report.schema_version,
        "simulation_id": report.simulation_id,
        "symbol": report.symbol,
        "strategy": report.strategy,
        "period": report.period,
        "profit_summary": {
            "initial_seed": decimal_amount_to_string(report.profit_summary.initial_seed),
            "final_seed": decimal_amount_to_string(report.profit_summary.final_seed),
            "total_profit": decimal_amount_to_string(report.profit_summary.total_profit),
            "total_profit_rate": decimal_rate_to_string(report.profit_summary.total_profit_rate),
        },
        "summary": {
            "total_trades": report.summary.total_trades,
            "profit_trades": report.summary.profit_trades,
            "loss_trades": report.summary.loss_trades,
            "flat_trades": report.summary.flat_trades,
            "no_trade_days": report.summary.no_trade_days,
            "total_profit_amount": decimal_amount_to_string(report.summary.total_profit_amount),
            "total_loss_amount": decimal_amount_to_string(report.summary.total_loss_amount),
            "win_rate": decimal_rate_to_string(report.summary.win_rate),
        },
        "trades": [
            {
                "trade_id": trade.trade_id,
                "trade_date": trade.trade_date,
                "symbol_code": trade.symbol_code,
                "buy_datetime": trade.buy_datetime,
                "buy_price": None if trade.buy_price is None else decimal_amount_to_string(trade.buy_price),
                "buy_quantity": trade.buy_quantity,
                "buy_amount": decimal_amount_to_string(trade.buy_amount),
                "sell_datetime": trade.sell_datetime,
                "sell_price": None if trade.sell_price is None else decimal_amount_to_string(trade.sell_price),
                "sell_quantity": trade.sell_quantity,
                "sell_amount": decimal_amount_to_string(trade.sell_amount),
                "sell_reason": trade.sell_reason,
                "sell_reason_display": trade.sell_reason_display,
                "tax": decimal_amount_to_string(trade.tax),
                "fee": decimal_amount_to_string(trade.fee),
                "net_profit": decimal_amount_to_string(trade.net_profit),
                "profit_rate": decimal_rate_to_string(trade.profit_rate),
                "seed_money_after": decimal_amount_to_string(trade.seed_money_after),
            }
            for trade in report.trades
        ],
        "warnings": [
            {
                "code": warning.code,
                "message": warning.message,
                "trade_date": warning.trade_date,
            }
            for warning in report.warnings
        ],
    }
