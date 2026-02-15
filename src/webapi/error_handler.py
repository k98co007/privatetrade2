from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from report.errors import ReportCalculationError, ReportNotFoundError, SchemaVersionError
from simulation.errors import SimulationFatalError, SimulationValidationError

from .errors import (
    CircuitOpenError,
    DependencyTimeoutError,
    DuplicateRequestInFlightError,
    InvalidStrategyError,
    InvalidSymbolError,
    ReportNotReadyError,
    RequestValidationError,
    SimulationNotFoundError,
    WebApiError,
)
from .response_formatter import ResponseFormatter


class ErrorHandler:
    @staticmethod
    def to_http_error(exc: Exception, request_id: str) -> tuple[int, dict]:
        if isinstance(exc, InvalidSymbolError):
            return 400, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, InvalidStrategyError):
            return 400, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, RequestValidationError):
            return 400, ResponseFormatter.error("INVALID_REQUEST", "요청 형식이 올바르지 않습니다", request_id, exc.details)
        if isinstance(exc, DuplicateRequestInFlightError):
            return 409, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, SimulationNotFoundError):
            return 404, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, ReportNotReadyError):
            return 409, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, SchemaVersionError):
            return 406, ResponseFormatter.error("REPORT_SCHEMA_NOT_SUPPORTED", "지원하지 않는 스키마 버전입니다", request_id)
        if isinstance(exc, CircuitOpenError):
            return 503, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, DependencyTimeoutError):
            return 504, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        if isinstance(exc, ReportNotFoundError):
            return 404, ResponseFormatter.error("SIMULATION_NOT_FOUND", "시뮬레이션을 찾을 수 없습니다", request_id)
        if isinstance(exc, ReportCalculationError):
            return 500, ResponseFormatter.error("INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다", request_id)
        if isinstance(exc, SimulationValidationError):
            return 400, ResponseFormatter.error("INVALID_REQUEST", "요청 형식이 올바르지 않습니다", request_id)
        if isinstance(exc, SimulationFatalError):
            return 500, ResponseFormatter.error("INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다", request_id)
        if isinstance(exc, WebApiError):
            return 500, ResponseFormatter.error(exc.code, exc.message, request_id, exc.details)
        return 500, ResponseFormatter.error("INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다", request_id)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def _handle_exception(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "REQ-UNKNOWN")
        status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
        return JSONResponse(status_code=status_code, content=envelope)
