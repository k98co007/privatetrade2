from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


ERROR_CODES = {
    "E_MD_001": "E-MD-001",
    "E_MD_002": "E-MD-002",
    "E_MD_003": "E-MD-003",
    "E_MD_004": "E-MD-004",
    "E_MD_005": "E-MD-005",
    "E_MD_006": "E-MD-006",
    "E_MD_007": "E-MD-007",
    "E_MD_008": "E-MD-008",
    "E_MD_009": "E-MD-009",
    "E_MD_010": "E-MD-010",
    "E_MD_011": "E-MD-011",
    "E_MD_012": "E-MD-012",
}


@dataclass
class MarketDataError(Exception):
    code: str
    message: str
    cause: Optional[BaseException] = None

    def __post_init__(self) -> None:
        super().__init__(f"[{self.code}] {self.message}")


class ValidationError(MarketDataError):
    pass


class NoDataError(MarketDataError):
    pass


class ExternalAPIError(MarketDataError):
    pass


class DataIntegrityError(MarketDataError):
    pass


class StorageError(MarketDataError):
    pass


class CalculationError(MarketDataError):
    pass
