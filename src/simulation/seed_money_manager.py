from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo

from .constants import DEFAULT_INITIAL_SEED, ERROR_CODES
from .errors import InsufficientSeedError, SeedUpdateError, SimulationValidationError
from .models import SeedState
from .precision import floor_to_won, to_decimal


class SeedMoneyManager:
    def initialize(self, initial_seed: Decimal = DEFAULT_INITIAL_SEED) -> SeedState:
        seed = floor_to_won(to_decimal(initial_seed))
        if seed <= Decimal("0"):
            raise SimulationValidationError(
                ERROR_CODES["E_SIM_002"],
                "initial_seed_must_be_positive",
            )

        now = datetime.now(ZoneInfo("Asia/Seoul"))
        return SeedState(balance=seed, initial=seed, last_updated=now)

    def calculate_buy_quantity(self, seed_balance: Decimal, buy_price: Decimal) -> int:
        balance = to_decimal(seed_balance)
        price = to_decimal(buy_price)
        if balance < Decimal("0") or price <= Decimal("0"):
            raise SeedUpdateError(
                ERROR_CODES["E_SIM_012"],
                "invalid_seed_or_price",
            )

        quantity = int((balance / price).to_integral_value(rounding=ROUND_DOWN))
        if quantity == 0:
            raise InsufficientSeedError(
                ERROR_CODES["E_SIM_010"],
                "insufficient_seed_to_buy_single_share",
            )
        return quantity

    def apply_trade_result(self, seed_state: SeedState, net_profit: Decimal) -> SeedState:
        profit = floor_to_won(to_decimal(net_profit))
        updated_balance = floor_to_won(seed_state.balance + profit)
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        return SeedState(
            balance=updated_balance,
            initial=seed_state.initial,
            last_updated=now,
        )
