from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReportError(Exception):
    code: str
    message: str
    cause: Optional[BaseException] = None

    def __post_init__(self) -> None:
        super().__init__(f"[{self.code}] {self.message}")


class ReportValidationError(ReportError):
    pass


class ReportCalculationError(ReportError):
    pass


class ReportNotFoundError(ReportError):
    pass


class SchemaVersionError(ReportError):
    pass


class StorageError(ReportError):
    pass


class DuplicateKeyError(StorageError):
    pass


class NotFoundError(StorageError):
    pass


def map_exception_to_api_error(exc: ReportError) -> tuple[str, int, str]:
    if isinstance(exc, ReportNotFoundError):
        return ("SIMULATION_NOT_FOUND", 404, "시뮬레이션 결과를 찾을 수 없습니다")
    if isinstance(exc, ReportValidationError):
        return ("REPORT_VALIDATION_ERROR", 422, "보고서 입력 데이터가 유효하지 않습니다")
    if isinstance(exc, ReportCalculationError):
        return ("REPORT_CALCULATION_ERROR", 500, "보고서 계산 중 오류가 발생했습니다")
    if isinstance(exc, SchemaVersionError):
        return ("REPORT_SCHEMA_NOT_SUPPORTED", 406, "지원하지 않는 스키마 버전입니다")
    if isinstance(exc, StorageError):
        return ("STORAGE_ERROR", 500, "저장소 처리 중 오류가 발생했습니다")
    return ("REPORT_INTERNAL_ERROR", 500, "보고서 처리 중 오류가 발생했습니다")
