from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP
from typing import Any

from .constants import ERROR_CODES
from .errors import SimulationValidationError


def to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise SimulationValidationError(
            ERROR_CODES["E_SIM_001"],
            "invalid_decimal_value",
            cause=exc,
        ) from exc


def floor_to_won(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_DOWN)


def round_display_percent(value: Decimal, digits: int = 2) -> Decimal:
    if digits < 0:
        raise SimulationValidationError(
            ERROR_CODES["E_SIM_001"],
            "invalid_round_digits",
        )
    quant = Decimal("1").scaleb(-digits)
    return value.quantize(quant, rounding=ROUND_HALF_UP)
