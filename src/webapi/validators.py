from __future__ import annotations

import re
from typing import Any

from .constants import (
    DEFAULT_INCLUDE_NO_TRADE,
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    DEFAULT_SCHEMA_VERSION,
    DEFAULT_SORT_ORDER,
    IDEMPOTENCY_KEY_REGEX,
    MAX_LIMIT,
    MAX_OFFSET,
    SCHEMA_VERSION_REGEX,
    SIMULATION_ID_REGEX,
    SYMBOL_REGEX,
    VALID_SIMULATION_STATUSES,
    VALID_SORT_ORDERS,
    VALID_STRATEGIES,
)
from .errors import InvalidStrategyError, InvalidSymbolError, RequestValidationError
from .models import ReportQuery, SimulationListQuery, SimulationStartRequest


STRATEGY_D_ID = "two_minute_multi_symbol_buy_trailing_then_sell_trailing"
STRATEGY_D_MAX_SYMBOLS = 20


def validate_start_request(payload: dict[str, Any]) -> SimulationStartRequest:
    symbol = str(payload.get("symbol", "")).strip()
    strategy = str(payload.get("strategy", "")).strip()
    symbols_payload = payload.get("symbols")
    idempotency_key = payload.get("idempotency_key")

    if strategy not in VALID_STRATEGIES:
        raise InvalidStrategyError(
            code="INVALID_STRATEGY",
            message="유효하지 않은 전략입니다",
            details={"field": "strategy", "allowed": list(VALID_STRATEGIES)},
        )

    symbols: list[str] | None = None
    if strategy == STRATEGY_D_ID:
        if not isinstance(symbols_payload, list):
            raise RequestValidationError(
                code="INVALID_REQUEST",
                message="요청 형식이 올바르지 않습니다",
                details={"field": "symbols", "rule": "array[1..20]"},
            )

        symbols = [str(value).strip().upper() for value in symbols_payload if str(value).strip()]
        if not symbols or len(symbols) > STRATEGY_D_MAX_SYMBOLS:
            raise RequestValidationError(
                code="INVALID_REQUEST",
                message="요청 형식이 올바르지 않습니다",
                details={"field": "symbols", "rule": "array[1..20]"},
            )

        invalid_symbols = [item for item in symbols if not re.match(SYMBOL_REGEX, item)]
        if invalid_symbols:
            raise InvalidSymbolError(
                code="INVALID_SYMBOL",
                message="유효하지 않은 종목 심볼입니다",
                details={"field": "symbols", "rule": SYMBOL_REGEX},
            )

        if not symbol:
            symbol = symbols[0]
    else:
        if not symbol or not re.match(SYMBOL_REGEX, symbol):
            raise InvalidSymbolError(
                code="INVALID_SYMBOL",
                message="유효하지 않은 종목 심볼입니다",
                details={"field": "symbol", "rule": SYMBOL_REGEX},
            )

    if idempotency_key is not None:
        normalized = str(idempotency_key).strip()
        if not re.match(IDEMPOTENCY_KEY_REGEX, normalized):
            raise RequestValidationError(
                code="INVALID_REQUEST",
                message="요청 형식이 올바르지 않습니다",
                details={"field": "idempotency_key", "rule": IDEMPOTENCY_KEY_REGEX},
            )
        idempotency_key = normalized

    return SimulationStartRequest(symbol=symbol, strategy=strategy, symbols=symbols, idempotency_key=idempotency_key)


def validate_simulation_id(simulation_id: str) -> str:
    normalized = str(simulation_id).strip()
    if not re.match(SIMULATION_ID_REGEX, normalized):
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "simulation_id", "rule": SIMULATION_ID_REGEX},
        )
    return normalized


def validate_list_query(query: dict[str, Any]) -> SimulationListQuery:
    status = query.get("status")
    offset_raw = query.get("offset", DEFAULT_OFFSET)
    limit_raw = query.get("limit", DEFAULT_LIMIT)

    try:
        offset = int(offset_raw)
        limit = int(limit_raw)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "offset|limit", "rule": "integer"},
        ) from exc

    if offset < 0 or offset > MAX_OFFSET:
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "offset", "rule": f"0<=offset<={MAX_OFFSET}"},
        )
    if limit < 1 or limit > MAX_LIMIT:
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "limit", "rule": f"1<=limit<={MAX_LIMIT}"},
        )

    normalized_status = None
    if status is not None and str(status).strip() != "":
        normalized_status = str(status).strip()
        if normalized_status not in VALID_SIMULATION_STATUSES:
            raise RequestValidationError(
                code="INVALID_REQUEST",
                message="요청 형식이 올바르지 않습니다",
                details={"field": "status", "allowed": list(VALID_SIMULATION_STATUSES)},
            )

    return SimulationListQuery(status=normalized_status, offset=offset, limit=limit)


def validate_report_query(query: dict[str, Any]) -> ReportQuery:
    schema_version = str(query.get("schema_version", DEFAULT_SCHEMA_VERSION)).strip()
    include_no_trade_raw = query.get("include_no_trade", DEFAULT_INCLUDE_NO_TRADE)
    sort_order = str(query.get("sort_order", DEFAULT_SORT_ORDER)).strip().lower()

    if not re.match(SCHEMA_VERSION_REGEX, schema_version):
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "schema_version", "rule": SCHEMA_VERSION_REGEX},
        )
    if sort_order not in VALID_SORT_ORDERS:
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "sort_order", "allowed": list(VALID_SORT_ORDERS)},
        )

    if isinstance(include_no_trade_raw, bool):
        include_no_trade = include_no_trade_raw
    elif str(include_no_trade_raw).strip().lower() in ("true", "1", "yes"):
        include_no_trade = True
    elif str(include_no_trade_raw).strip().lower() in ("false", "0", "no"):
        include_no_trade = False
    else:
        raise RequestValidationError(
            code="INVALID_REQUEST",
            message="요청 형식이 올바르지 않습니다",
            details={"field": "include_no_trade", "rule": "boolean"},
        )

    return ReportQuery(
        schema_version=schema_version,
        include_no_trade=include_no_trade,
        sort_order=sort_order,
    )
