from __future__ import annotations

from decimal import Decimal

DEFAULT_INITIAL_SEED = Decimal("10000000")
DEFAULT_PERIOD = "60d"
DEFAULT_INTERVAL = "5m"
MAX_TRADING_DAYS = 60

SELL_TAX_RATE = Decimal("0.002")
SELL_FEE_RATE = Decimal("0.00011")

SYMBOL_PATTERN = r"^[0-9]{6}\.KS$"
MANDATORY_CANDLE_TIMES = ("09:05", "15:00")

STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"

SELL_REASON_PROFIT_PRESERVE = "profit_preserve"
SELL_REASON_STOP_LOSS = "stop_loss"
SELL_REASON_NO_TRADE = "no_trade"
SELL_REASON_ERROR_SKIP = "error_skip"

EVENT_PROGRESS = "progress"
EVENT_TRADE = "trade"
EVENT_WARNING = "warning"
EVENT_ERROR = "error"
EVENT_COMPLETED = "completed"

ERROR_CODES = {
    "E_SIM_001": "E-SIM-001",
    "E_SIM_002": "E-SIM-002",
    "E_SIM_003": "E-SIM-003",
    "E_SIM_004": "E-SIM-004",
    "E_SIM_005": "E-SIM-005",
    "E_SIM_006": "E-SIM-006",
    "E_SIM_007": "E-SIM-007",
    "E_SIM_008": "E-SIM-008",
    "E_SIM_009": "E-SIM-009",
    "E_SIM_010": "E-SIM-010",
    "E_SIM_011": "E-SIM-011",
    "E_SIM_012": "E-SIM-012",
    "E_SIM_013": "E-SIM-013",
    "E_SIM_014": "E-SIM-014",
}
