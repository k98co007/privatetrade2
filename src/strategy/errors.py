from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategyError(Exception):
    code: str
    message: str
    cause: Optional[BaseException] = None

    def __post_init__(self) -> None:
        super().__init__(f"[{self.code}] {self.message}")


class StrategyNotFoundError(StrategyError):
    pass


class DuplicateStrategyError(StrategyError):
    pass


class StrategyInputError(StrategyError):
    pass


class RSIDataMissingError(StrategyInputError):
    pass


class InsufficientSeedMoneyError(StrategyInputError):
    pass


class StrategyExecutionError(StrategyError):
    pass
