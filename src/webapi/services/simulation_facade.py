from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from report.report_repository import ReportRepository
from simulation.constants import STATUS_COMPLETED, STATUS_ERROR
from simulation.models import SimulationRequest, SimulationResult
from simulation.simulation_engine import SimulationEngine

from webapi.constants import DEFAULT_INITIAL_SEED, IDEMPOTENCY_TTL
from webapi.errors import DuplicateRequestInFlightError, SimulationNotFoundError
from webapi.models import InternalSimulationState, SimulationStartResult
from webapi.services.stream_session_manager import StreamSessionManager


LOGGER = logging.getLogger("webapi.service.simulation")


@dataclass
class IdempotencyRecord:
    key: str
    created_at: datetime
    expires_at: datetime
    simulation_id: str | None
    in_flight: bool


class SimulationFacade:
    def __init__(
        self,
        stream_session_manager: StreamSessionManager,
        simulation_engine: SimulationEngine | None = None,
        repository: ReportRepository | None = None,
        max_workers: int = 2,
    ) -> None:
        self.stream_session_manager = stream_session_manager
        self.simulation_engine = simulation_engine or SimulationEngine()
        self.repository = repository or ReportRepository()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._status_store: dict[str, InternalSimulationState] = {}
        self._jobs: dict[str, Future] = {}
        self._idempotency_store: dict[str, IdempotencyRecord] = {}
        self._lock = threading.Lock()

    def start_simulation(
        self,
        symbol: str,
        strategy: str,
        idempotency_key: str | None,
        symbols: list[str] | None = None,
    ) -> SimulationStartResult:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        LOGGER.info(
            "simulation.enqueue.request symbol=%s strategy=%s idempotency=%s symbols_count=%s",
            symbol,
            strategy,
            "present" if idempotency_key else "none",
            0 if symbols is None else len(symbols),
        )
        if idempotency_key:
            with self._lock:
                self._cleanup_idempotency(now)
                existing = self._idempotency_store.get(idempotency_key)
                if existing is not None:
                    if existing.in_flight and existing.simulation_id is None:
                        LOGGER.warning("simulation.enqueue.duplicate_in_flight idempotency_key=%s", idempotency_key)
                        raise DuplicateRequestInFlightError(
                            code="DUPLICATE_REQUEST_IN_FLIGHT",
                            message="동일 요청이 처리 중입니다",
                        )
                    if existing.simulation_id is not None:
                        state = self._status_store.get(existing.simulation_id)
                        if state is not None:
                            LOGGER.info(
                                "simulation.enqueue.idempotent_hit idempotency_key=%s simulation_id=%s status=%s",
                                idempotency_key,
                                state.simulation_id,
                                state.status,
                            )
                            return SimulationStartResult(**state.model_dump())

                self._idempotency_store[idempotency_key] = IdempotencyRecord(
                    key=idempotency_key,
                    created_at=now,
                    expires_at=now + IDEMPOTENCY_TTL,
                    simulation_id=None,
                    in_flight=True,
                )

        simulation_id = f"SIM-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:12]}"
        created = datetime.now(ZoneInfo("Asia/Seoul"))
        status = InternalSimulationState(
            simulation_id=simulation_id,
            status="queued",
            symbol=symbol,
            strategy=strategy,
            created_at=created,
            updated_at=created,
        )

        with self._lock:
            self._status_store[simulation_id] = status
            if idempotency_key:
                self._idempotency_store[idempotency_key].simulation_id = simulation_id
        LOGGER.info(
            "simulation.enqueue.accepted simulation_id=%s symbol=%s strategy=%s",
            simulation_id,
            symbol,
            strategy,
        )

        future = self._executor.submit(
            self._run_simulation_job,
            simulation_id,
            symbol,
            strategy,
            idempotency_key,
            symbols,
        )
        with self._lock:
            self._jobs[simulation_id] = future

        return SimulationStartResult(**status.model_dump())

    def get_status(self, simulation_id: str) -> InternalSimulationState:
        with self._lock:
            state = self._status_store.get(simulation_id)
            if state is None:
                raise SimulationNotFoundError(
                    code="SIMULATION_NOT_FOUND",
                    message="시뮬레이션을 찾을 수 없습니다",
                )
            return state

    def list_status(self, status: str | None, offset: int, limit: int) -> list[InternalSimulationState]:
        with self._lock:
            states = list(self._status_store.values())
        states.sort(key=lambda item: item.created_at, reverse=True)
        if status:
            states = [item for item in states if item.status == status]
        return states[offset : offset + limit]

    def exists(self, simulation_id: str) -> bool:
        with self._lock:
            return simulation_id in self._status_store

    def _run_simulation_job(
        self,
        simulation_id: str,
        symbol: str,
        strategy: str,
        idempotency_key: str | None,
        symbols: list[str] | None,
    ) -> None:
        LOGGER.info(
            "simulation.job.start simulation_id=%s symbol=%s strategy=%s",
            simulation_id,
            symbol,
            strategy,
        )
        self._update_status(simulation_id, status="running")
        try:
            self.simulation_engine.event_emitter.dispatcher = self._build_dispatcher(simulation_id)
            request = SimulationRequest(
                symbol=symbol,
                strategy_name=strategy,
                initial_seed=Decimal(DEFAULT_INITIAL_SEED),
                symbols=symbols,
            )
            result = self.simulation_engine.run_simulation(request)
            result = self._replace_result_simulation_id(result, simulation_id)

            self.repository.create_simulation_result(result)
            self.repository.create_trade_records(simulation_id=simulation_id, trades=result.trades)
            LOGGER.info(
                "simulation.job.persisted simulation_id=%s trades=%s final_seed=%s total_profit_rate=%s",
                simulation_id,
                len(result.trades),
                format(result.final_seed, "f"),
                format(result.total_profit_rate, "f"),
            )

            self._update_status(simulation_id, status=STATUS_COMPLETED)
            self.stream_session_manager.append_event(
                simulation_id,
                "completed",
                {
                    "status": "completed",
                    "final_seed": format(result.final_seed, "f"),
                    "total_profit_rate": format(result.total_profit_rate, "f"),
                },
            )
            LOGGER.info("simulation.job.completed simulation_id=%s", simulation_id)
        except Exception as exc:
            self._update_status(
                simulation_id,
                status=STATUS_ERROR,
                error_code="SIMULATION_FAILED",
                error_message="시뮬레이션 실행 중 오류가 발생했습니다",
            )
            self.stream_session_manager.append_event(
                simulation_id,
                "error",
                {
                    "status": "error",
                    "code": "SIMULATION_FAILED",
                    "message": "시뮬레이션 실행 중 오류가 발생했습니다",
                    "detail": str(exc),
                },
            )
            LOGGER.exception("simulation.job.failed simulation_id=%s", simulation_id)
        finally:
            if idempotency_key:
                with self._lock:
                    record = self._idempotency_store.get(idempotency_key)
                    if record is not None:
                        record.in_flight = False
                        LOGGER.info(
                            "simulation.job.idempotency_released simulation_id=%s idempotency_key=%s",
                            simulation_id,
                            idempotency_key,
                        )

    def _build_dispatcher(self, simulation_id: str):
        def _dispatch(event_type: str, payload: dict) -> None:
            mapped_payload = dict(payload)
            if event_type == "progress":
                total_days = max(int(mapped_payload.get("total_days", 0)), 1)
                current_day = int(mapped_payload.get("current_day", 0))
                mapped_payload["progress_pct"] = round((current_day / total_days) * 100, 2)
            if event_type == "trade":
                mapped_payload.setdefault("trade_type", "sell")
                mapped_payload.setdefault("trade_datetime", mapped_payload.get("trade_date"))
                mapped_payload.setdefault("price", None)
                mapped_payload.setdefault("quantity", 0)
            self.stream_session_manager.append_event(simulation_id, event_type, mapped_payload)

        return _dispatch

    def _update_status(
        self,
        simulation_id: str,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._lock:
            state = self._status_store.get(simulation_id)
            if state is None:
                return
            previous_status = state.status
            state.status = status
            state.updated_at = datetime.now(ZoneInfo("Asia/Seoul"))
            state.error_code = error_code
            state.error_message = error_message
            LOGGER.info(
                "simulation.status.updated simulation_id=%s from=%s to=%s error_code=%s",
                simulation_id,
                previous_status,
                status,
                error_code,
            )

    def _cleanup_idempotency(self, now: datetime) -> None:
        stale_keys = [key for key, value in self._idempotency_store.items() if value.expires_at <= now]
        for key in stale_keys:
            self._idempotency_store.pop(key, None)

    @staticmethod
    def _replace_result_simulation_id(result: SimulationResult, simulation_id: str) -> SimulationResult:
        return SimulationResult(
            simulation_id=simulation_id,
            symbol=result.symbol,
            strategy=result.strategy,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_seed=result.initial_seed,
            final_seed=result.final_seed,
            total_profit=result.total_profit,
            total_profit_rate=result.total_profit_rate,
            total_trades=result.total_trades,
            no_trade_days=result.no_trade_days,
            error_skip_days=result.error_skip_days,
            status=result.status,
            trades=result.trades,
            meta=result.meta,
        )
