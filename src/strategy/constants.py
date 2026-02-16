from __future__ import annotations

from decimal import Decimal

SELL_TRAILING_STOP = "sell_trailing_stop"
BUY_SELL_TRAILING_STOP = "buy_sell_trailing_stop"
RSI_BUY_SELL_TRAILING_STOP = "rsi_buy_sell_trailing_stop"
RSI_ONLY_TRAILING_STOP = "rsi_only_trailing_stop"
BUY_TRAILING_THEN_SELL_TRAILING = "buy_trailing_then_sell_trailing"

TIME_0905 = "09:05"
TIME_1500 = "14:55"
TIME_1505 = "14:55"

PROFIT_TRIGGER_RATE = Decimal("1.0")
PRESERVE_RATIO_THRESHOLD = Decimal("80")
ENTRY_DROP_RATE = Decimal("1.0")
REBOUND_RATE = Decimal("0.2")
RSI_BUY_THRESHOLD = Decimal("30")

STRATEGY_REQUIRED_CANDLE_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
RSI_REQUIRED_COLUMNS = ("timestamp", "rsi")

ERROR_CODES = {
    "E_ST_001": "E-ST-001",
    "E_ST_002": "E-ST-002",
    "E_ST_003": "E-ST-003",
    "E_ST_004": "E-ST-004",
    "E_ST_005": "E-ST-005",
    "E_ST_006": "E-ST-006",
    "E_ST_007": "E-ST-007",
    "E_ST_008": "E-ST-008",
}
