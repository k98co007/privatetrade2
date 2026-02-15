from __future__ import annotations

from decimal import Decimal

from .constants import ERROR_CODES, SELL_FEE_RATE, SELL_TAX_RATE
from .errors import CostCalculationError
from .models import ProfitResult, SellCosts
from .precision import floor_to_won, to_decimal


class CostCalculator:
    def calculate_sell_costs(self, sell_amount: Decimal) -> SellCosts:
        normalized_sell_amount = to_decimal(sell_amount)
        if normalized_sell_amount < Decimal("0"):
            raise CostCalculationError(
                ERROR_CODES["E_SIM_011"],
                "sell_amount_must_be_non_negative",
            )

        tax = floor_to_won(normalized_sell_amount * SELL_TAX_RATE)
        fee = floor_to_won(normalized_sell_amount * SELL_FEE_RATE)
        net_sell_amount = normalized_sell_amount - tax - fee
        return SellCosts(tax=tax, fee=fee, net_sell_amount=net_sell_amount)

    def calculate_net_profit(self, buy_amount: Decimal, sell_amount: Decimal) -> ProfitResult:
        normalized_buy_amount = to_decimal(buy_amount)
        normalized_sell_amount = to_decimal(sell_amount)
        if normalized_buy_amount < Decimal("0") or normalized_sell_amount < Decimal("0"):
            raise CostCalculationError(
                ERROR_CODES["E_SIM_011"],
                "amount_must_be_non_negative",
            )

        sell_costs = self.calculate_sell_costs(normalized_sell_amount)
        net_profit = sell_costs.net_sell_amount - normalized_buy_amount

        if normalized_buy_amount == Decimal("0"):
            profit_rate = Decimal("0")
        else:
            profit_rate = (net_profit / normalized_buy_amount) * Decimal("100")

        return ProfitResult(
            tax=sell_costs.tax,
            fee=sell_costs.fee,
            net_sell_amount=sell_costs.net_sell_amount,
            net_profit=net_profit,
            profit_rate=profit_rate,
        )
