from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from webapi.constants import (
    API_PREFIX,
    DEPENDENCY_TIMEOUT_REPORT_SECONDS,
    DEPENDENCY_TIMEOUT_SIM_GET_SECONDS,
    DEPENDENCY_TIMEOUT_SIM_LIST_SECONDS,
    DEPENDENCY_TIMEOUT_SIM_START_SECONDS,
    HEADER_IDEMPOTENCY_KEY,
    SIMULATIONS_PATH,
    SIMULATION_BY_ID_PATH,
    SIMULATION_REPORT_PATH,
)
from webapi.error_handler import ErrorHandler
from webapi.errors import ReportNotReadyError
from webapi.models import ReportFacadeQuery
from webapi.response_formatter import ResponseFormatter
from webapi.services.circuit_breaker import CircuitBreaker
from webapi.services.report_facade import ReportFacade
from webapi.services.simulation_facade import SimulationFacade
from webapi.services.timeout_policy import run_with_timeout
from webapi.validators import (
    validate_list_query,
    validate_report_query,
    validate_simulation_id,
    validate_start_request,
)


def create_simulation_router(simulation_facade: SimulationFacade, report_facade: ReportFacade) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX)
    simulation_circuit = CircuitBreaker("simulation")
    report_circuit = CircuitBreaker("report")

    @router.post(SIMULATIONS_PATH)
    async def start_simulation(request: Request) -> JSONResponse:
        request_id = request.state.request_id
        try:
            payload = await request.json()
            body = validate_start_request(payload)
            header_idempotency_key = request.headers.get(HEADER_IDEMPOTENCY_KEY)
            idempotency_key = header_idempotency_key or body.idempotency_key

            simulation_circuit.before_call()
            try:
                result = await run_with_timeout(
                    asyncio.to_thread(
                        simulation_facade.start_simulation,
                        body.symbol,
                        body.strategy,
                        idempotency_key,
                    ),
                    timeout_seconds=DEPENDENCY_TIMEOUT_SIM_START_SECONDS,
                    operation="simulation.start",
                )
                simulation_circuit.after_success()
            except Exception:
                simulation_circuit.after_failure()
                raise

            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=ResponseFormatter.ok(result.model_dump(mode="json"), request_id),
            )
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            return JSONResponse(status_code=status_code, content=envelope)

    @router.get(SIMULATIONS_PATH)
    async def list_simulations(request: Request) -> JSONResponse:
        request_id = request.state.request_id
        try:
            query = validate_list_query(dict(request.query_params.items()))

            simulation_circuit.before_call()
            try:
                rows = await run_with_timeout(
                    asyncio.to_thread(
                        simulation_facade.list_status,
                        query.status,
                        query.offset,
                        query.limit,
                    ),
                    timeout_seconds=DEPENDENCY_TIMEOUT_SIM_LIST_SECONDS,
                    operation="simulation.list",
                )
                simulation_circuit.after_success()
            except Exception:
                simulation_circuit.after_failure()
                raise

            data: list[dict[str, Any]] = [row.model_dump(mode="json") for row in rows]
            return JSONResponse(status_code=200, content=ResponseFormatter.ok(data, request_id))
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            return JSONResponse(status_code=status_code, content=envelope)

    @router.get(SIMULATION_BY_ID_PATH)
    async def get_simulation(request: Request, simulation_id: str) -> JSONResponse:
        request_id = request.state.request_id
        try:
            valid_simulation_id = validate_simulation_id(simulation_id)

            simulation_circuit.before_call()
            try:
                row = await run_with_timeout(
                    asyncio.to_thread(simulation_facade.get_status, valid_simulation_id),
                    timeout_seconds=DEPENDENCY_TIMEOUT_SIM_GET_SECONDS,
                    operation="simulation.get_status",
                )
                simulation_circuit.after_success()
            except Exception:
                simulation_circuit.after_failure()
                raise

            return JSONResponse(status_code=200, content=ResponseFormatter.ok(row.model_dump(mode="json"), request_id))
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            return JSONResponse(status_code=status_code, content=envelope)

    @router.get(SIMULATION_REPORT_PATH)
    async def get_report(request: Request, simulation_id: str) -> JSONResponse:
        request_id = request.state.request_id
        try:
            valid_simulation_id = validate_simulation_id(simulation_id)
            query = validate_report_query(dict(request.query_params.items()))

            simulation_circuit.before_call()
            try:
                simulation = await run_with_timeout(
                    asyncio.to_thread(simulation_facade.get_status, valid_simulation_id),
                    timeout_seconds=DEPENDENCY_TIMEOUT_SIM_GET_SECONDS,
                    operation="simulation.get_status_for_report",
                )
                simulation_circuit.after_success()
            except Exception:
                simulation_circuit.after_failure()
                raise

            if simulation.status != "completed":
                raise ReportNotReadyError(
                    code="REPORT_NOT_READY",
                    message="시뮬레이션이 아직 완료되지 않았습니다",
                )

            report_circuit.before_call()
            try:
                report = await run_with_timeout(
                    asyncio.to_thread(
                        report_facade.generate_report,
                        valid_simulation_id,
                        ReportFacadeQuery(
                            schema_version=query.schema_version,
                            include_no_trade=query.include_no_trade,
                            sort_order=query.sort_order,
                        ),
                    ),
                    timeout_seconds=DEPENDENCY_TIMEOUT_REPORT_SECONDS,
                    operation="report.generate",
                )
                report_circuit.after_success()
            except Exception:
                report_circuit.after_failure()
                raise

            return JSONResponse(status_code=200, content=ResponseFormatter.ok(report, request_id))
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            return JSONResponse(status_code=status_code, content=envelope)

    return router
