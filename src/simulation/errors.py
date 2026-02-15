from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationError(Exception):
    code: str
    message: str
    cause: Optional[BaseException] = None

    def __post_init__(self) -> None:
        super().__init__(f"[{self.code}] {self.message}")


class SimulationValidationError(SimulationError):
    pass


class DataUnavailableError(SimulationError):
    pass


class DataIntegrityError(SimulationError):
    pass


class StrategyNotFoundError(SimulationError):
    pass


class StrategyExecutionError(SimulationError):
    pass


class DayProcessingError(SimulationError):
    pass


class EventDispatchError(SimulationError):
    pass


class MissingMandatoryCandleError(SimulationError):
    pass


class InsufficientSeedError(SimulationError):
    pass


class CostCalculationError(SimulationError):
    pass


class SeedUpdateError(SimulationError):
    pass


class TradeExecutionError(SimulationError):
    pass


class SimulationFatalError(SimulationError):
    pass
