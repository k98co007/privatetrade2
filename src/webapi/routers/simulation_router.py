from __future__ import annotations

import asyncio
import logging
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


LOGGER = logging.getLogger("webapi.router.simulation")


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
            LOGGER.info(
                "simulation.start.request request_id=%s symbol=%s strategy=%s idempotency=%s",
                request_id,
                body.symbol,
                body.strategy,
                "present" if idempotency_key else "none",
            )

            simulation_circuit.before_call()
            try:
                result = await run_with_timeout(
                    asyncio.to_thread(
                        simulation_facade.start_simulation,
                        body.symbol,
                        body.strategy,
                        idempotency_key,
                        body.symbols,
                    ),
                    timeout_seconds=DEPENDENCY_TIMEOUT_SIM_START_SECONDS,
                    operation="simulation.start",
                )
                simulation_circuit.after_success()
            except Exception:
                simulation_circuit.after_failure()
                raise

            result_payload: dict[str, Any]
            if hasattr(result, "model_dump") and callable(getattr(result, "model_dump")):
                result_payload = result.model_dump(mode="json")
            elif isinstance(result, dict):
                result_payload = result
            elif hasattr(result, "dict") and callable(getattr(result, "dict")):
                result_payload = result.dict()
            else:
                result_payload = dict(getattr(result, "__dict__", {}))

            simulation_id = result_payload.get("simulation_id")
            simulation_status = result_payload.get("status")

            LOGGER.info(
                "simulation.start.accepted request_id=%s simulation_id=%s status=%s",
                request_id,
                simulation_id,
                simulation_status,
            )

            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=ResponseFormatter.ok(result_payload, request_id),
            )
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            log_fn = LOGGER.exception if status_code >= 500 else LOGGER.warning
            log_fn(
                "simulation.start.error request_id=%s status=%s code=%s message=%s",
                request_id,
                status_code,
                envelope.get("error", {}).get("code"),
                envelope.get("error", {}).get("message"),
            )
            return JSONResponse(status_code=status_code, content=envelope)

    @router.get(SIMULATIONS_PATH)
    async def list_simulations(request: Request) -> JSONResponse:
        request_id = request.state.request_id
        try:
            query = validate_list_query(dict(request.query_params.items()))
            LOGGER.info(
                "simulation.list.request request_id=%s status=%s offset=%s limit=%s",
                request_id,
                query.status,
                query.offset,
                query.limit,
            )

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
            LOGGER.info(
                "simulation.list.success request_id=%s count=%s",
                request_id,
                len(data),
            )
            return JSONResponse(status_code=200, content=ResponseFormatter.ok(data, request_id))
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            log_fn = LOGGER.exception if status_code >= 500 else LOGGER.warning
            log_fn(
                "simulation.list.error request_id=%s status=%s code=%s message=%s",
                request_id,
                status_code,
                envelope.get("error", {}).get("code"),
                envelope.get("error", {}).get("message"),
            )
            return JSONResponse(status_code=status_code, content=envelope)

    @router.get(SIMULATION_BY_ID_PATH)
    async def get_simulation(request: Request, simulation_id: str) -> JSONResponse:
        request_id = request.state.request_id
        try:
            valid_simulation_id = validate_simulation_id(simulation_id)
            LOGGER.info(
                "simulation.get.request request_id=%s simulation_id=%s",
                request_id,
                valid_simulation_id,
            )

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

            LOGGER.info(
                "simulation.get.success request_id=%s simulation_id=%s status=%s",
                request_id,
                row.simulation_id,
                row.status,
            )
            return JSONResponse(status_code=200, content=ResponseFormatter.ok(row.model_dump(mode="json"), request_id))
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            log_fn = LOGGER.exception if status_code >= 500 else LOGGER.warning
            log_fn(
                "simulation.get.error request_id=%s simulation_id=%s status=%s code=%s message=%s",
                request_id,
                simulation_id,
                status_code,
                envelope.get("error", {}).get("code"),
                envelope.get("error", {}).get("message"),
            )
            return JSONResponse(status_code=status_code, content=envelope)

    @router.get(SIMULATION_REPORT_PATH)
    async def get_report(request: Request, simulation_id: str) -> JSONResponse:
        request_id = request.state.request_id
        try:
            valid_simulation_id = validate_simulation_id(simulation_id)
            query = validate_report_query(dict(request.query_params.items()))
            LOGGER.info(
                "report.get.request request_id=%s simulation_id=%s schema_version=%s include_no_trade=%s sort_order=%s",
                request_id,
                valid_simulation_id,
                query.schema_version,
                query.include_no_trade,
                query.sort_order,
            )

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

            LOGGER.info(
                "report.get.success request_id=%s simulation_id=%s",
                request_id,
                valid_simulation_id,
            )
            return JSONResponse(status_code=200, content=ResponseFormatter.ok(report, request_id))
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            log_fn = LOGGER.exception if status_code >= 500 else LOGGER.warning
            log_fn(
                "report.get.error request_id=%s simulation_id=%s status=%s code=%s message=%s",
                request_id,
                simulation_id,
                status_code,
                envelope.get("error", {}).get("code"),
                envelope.get("error", {}).get("message"),
            )
            return JSONResponse(status_code=status_code, content=envelope)

    return router
