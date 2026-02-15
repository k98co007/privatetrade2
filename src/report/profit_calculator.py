from __future__ import annotations

from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

from .constants import (
    AMOUNT_QUANTIZER,
    AMOUNT_ROUNDING,
    DECIMAL_PRECISION,
    ERROR_CODES,
    RATE_QUANTIZER,
    RATE_ROUNDING,
)
from .errors import ReportCalculationError, ReportValidationError
from .models import ProfitSummary


class ProfitCalculator:
    def calculate_profit_summary(self, initial_seed: Decimal, final_seed: Decimal) -> ProfitSummary:
        self.validate_seed_values(initial_seed, final_seed)
        total_profit = self.calculate_total_profit(initial_seed, final_seed)
        total_profit_rate = self.calculate_total_profit_rate(initial_seed, final_seed)
        return ProfitSummary(
            initial_seed=initial_seed.quantize(AMOUNT_QUANTIZER, rounding=AMOUNT_ROUNDING),
            final_seed=final_seed.quantize(AMOUNT_QUANTIZER, rounding=AMOUNT_ROUNDING),
            total_profit=total_profit,
            total_profit_rate=total_profit_rate,
        )

    def calculate_total_profit(self, initial_seed: Decimal, final_seed: Decimal) -> Decimal:
        self.validate_seed_values(initial_seed, final_seed)
        return (final_seed - initial_seed).quantize(AMOUNT_QUANTIZER, rounding=AMOUNT_ROUNDING)

    def calculate_total_profit_rate(self, initial_seed: Decimal, final_seed: Decimal) -> Decimal:
        self.validate_seed_values(initial_seed, final_seed)
        try:
            with localcontext() as ctx:
                ctx.prec = DECIMAL_PRECISION
                value = ((final_seed - initial_seed) / initial_seed) * Decimal("100")
                return value.quantize(RATE_QUANTIZER, rounding=RATE_ROUNDING)
        except (DivisionByZero, InvalidOperation) as exc:
            raise ReportCalculationError(ERROR_CODES["E_RP_004"], "total_profit_rate_calculation_failed", cause=exc) from exc

    def validate_seed_values(self, initial_seed: Decimal, final_seed: Decimal) -> None:
        if initial_seed is None or final_seed is None:
            raise ReportValidationError(ERROR_CODES["E_RP_001"], "seed_value_required")
        if initial_seed <= Decimal("0"):
            raise ReportValidationError(ERROR_CODES["E_RP_001"], "initial_seed_must_be_positive")
        if final_seed < Decimal("0"):
            raise ReportValidationError(ERROR_CODES["E_RP_001"], "final_seed_must_be_non_negative")
