from __future__ import annotations

import os
from datetime import timedelta

API_PREFIX = "/api"
SIMULATIONS_PATH = "/simulations"
SIMULATION_BY_ID_PATH = "/simulations/{simulation_id}"
SIMULATION_REPORT_PATH = "/simulations/{simulation_id}/report"
SIMULATION_STREAM_PATH = "/simulations/{simulation_id}/stream"

HEADER_IDEMPOTENCY_KEY = "Idempotency-Key"
HEADER_LAST_EVENT_ID = "Last-Event-ID"
HEADER_REQUEST_ID = "X-Request-Id"

DEFAULT_INITIAL_SEED = "10000000"

DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_OFFSET = 100000

DEFAULT_SCHEMA_VERSION = "1.0"
DEFAULT_INCLUDE_NO_TRADE = True
DEFAULT_SORT_ORDER = "asc"

VALID_SIMULATION_STATUSES = ("queued", "running", "completed", "error")
VALID_SORT_ORDERS = ("asc", "desc")
VALID_STRATEGIES = (
    "sell_trailing_stop",
    "buy_sell_trailing_stop",
    "rsi_buy_sell_trailing_stop",
    "rsi_only_trailing_stop",
    "buy_trailing_then_sell_trailing",
)

SYMBOL_REGEX = r"^[0-9]{6}\.KS$"
SIMULATION_ID_REGEX = r"^[A-Za-z0-9:_-]{1,64}$"
IDEMPOTENCY_KEY_REGEX = r"^[A-Za-z0-9_-]{8,64}$"
SCHEMA_VERSION_REGEX = r"^1\.[0-9]+$"

REQUEST_TIMEOUT_POST_SIMULATION_SECONDS = 2.0
REQUEST_TIMEOUT_GET_SIMULATION_SECONDS = 1.2
REQUEST_TIMEOUT_GET_SIMULATION_LIST_SECONDS = 1.5
REQUEST_TIMEOUT_GET_REPORT_SECONDS = 2.5

DEPENDENCY_TIMEOUT_SIM_START_SECONDS = 1.5
DEPENDENCY_TIMEOUT_SIM_GET_SECONDS = 1.0
DEPENDENCY_TIMEOUT_SIM_LIST_SECONDS = 1.2
DEPENDENCY_TIMEOUT_REPORT_SECONDS = 2.0

SSE_POLL_TIMEOUT_SECONDS = 1.0
SSE_HEARTBEAT_SECONDS = 5.0
SSE_RETRY_MS = 3000
SSE_WARMUP_SECONDS = 1.0
SSE_BUFFER_SIZE = 1000

IDEMPOTENCY_TTL = timedelta(minutes=10)

CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_WINDOW_SECONDS = 30
CIRCUIT_OPEN_SECONDS = 30

CORS_ALLOW_ORIGINS_ENV = "WEBAPI_CORS_ALLOW_ORIGINS"
CORS_DEFAULT_ALLOW_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]


def _parse_cors_allow_origins() -> list[str]:
    raw = os.getenv(CORS_ALLOW_ORIGINS_ENV, "")
    if not raw.strip():
        return list(CORS_DEFAULT_ALLOW_ORIGINS)

    parsed = [origin.strip() for origin in raw.split(",") if origin.strip() and origin.strip() != "*"]
    if parsed:
        return parsed
    return list(CORS_DEFAULT_ALLOW_ORIGINS)


CORS_ALLOW_ORIGINS = _parse_cors_allow_origins()
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type", "Last-Event-ID"]
