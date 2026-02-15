from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WebApiError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        super().__init__(f"[{self.code}] {self.message}")


class RequestValidationError(WebApiError):
    pass


class InvalidSymbolError(RequestValidationError):
    pass


class InvalidStrategyError(RequestValidationError):
    pass


class SimulationNotFoundError(WebApiError):
    pass


class ReportNotReadyError(WebApiError):
    pass


class DuplicateRequestInFlightError(WebApiError):
    pass


class DependencyTimeoutError(WebApiError):
    pass


class CircuitOpenError(WebApiError):
    pass


class StreamUnavailableError(WebApiError):
    pass


class InternalServerError(WebApiError):
    pass
