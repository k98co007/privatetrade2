from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse

from webapi.constants import (
    API_PREFIX,
    HEADER_LAST_EVENT_ID,
    SIMULATION_STREAM_PATH,
    SSE_HEARTBEAT_SECONDS,
    SSE_POLL_TIMEOUT_SECONDS,
    SSE_WARMUP_SECONDS,
)
from webapi.error_handler import ErrorHandler
from webapi.errors import SimulationNotFoundError
from webapi.services.simulation_facade import SimulationFacade
from webapi.services.stream_session_manager import StreamSessionManager
from webapi.validators import validate_simulation_id


LOGGER = logging.getLogger("webapi.router.sse")


def create_sse_router(simulation_facade: SimulationFacade, stream_session_manager: StreamSessionManager) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX)

    @router.get(SIMULATION_STREAM_PATH)
    async def get_simulation_stream(request: Request, simulation_id: str):
        request_id = request.state.request_id
        try:
            valid_simulation_id = validate_simulation_id(simulation_id)
            LOGGER.info(
                "sse.connect.request request_id=%s simulation_id=%s",
                request_id,
                valid_simulation_id,
            )
            if not simulation_facade.exists(valid_simulation_id):
                LOGGER.warning(
                    "sse.connect.not_found request_id=%s simulation_id=%s",
                    request_id,
                    valid_simulation_id,
                )
                raise SimulationNotFoundError(
                    code="SIMULATION_NOT_FOUND",
                    message="시뮬레이션을 찾을 수 없습니다",
                )

            last_event_id_raw = request.headers.get(HEADER_LAST_EVENT_ID)
            last_event_id = int(last_event_id_raw) if last_event_id_raw and last_event_id_raw.isdigit() else None
            session = stream_session_manager.open(
                simulation_id=valid_simulation_id,
                session_id=str(uuid.uuid4()),
                last_event_id=last_event_id,
            )
            LOGGER.info(
                "sse.connect.opened request_id=%s simulation_id=%s session_id=%s last_event_id=%s",
                request_id,
                valid_simulation_id,
                session.session_id,
                last_event_id,
            )

            async def _stream_generator():
                warmup_deadline = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(seconds=SSE_WARMUP_SECONDS)
                next_heartbeat = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(seconds=SSE_HEARTBEAT_SECONDS)

                if last_event_id is not None and stream_session_manager.has_replay_gap(valid_simulation_id, last_event_id):
                    LOGGER.warning(
                        "sse.connect.replay_gap request_id=%s simulation_id=%s session_id=%s last_event_id=%s",
                        request_id,
                        valid_simulation_id,
                        session.session_id,
                        last_event_id,
                    )
                    warning_event = stream_session_manager.append_event(
                        valid_simulation_id,
                        "warning",
                        {
                            "code": "STREAM_REPLAY_GAP",
                            "message": "이벤트 버퍼 만료로 최신 상태부터 재동기화합니다",
                        },
                    )
                    yield stream_session_manager.to_sse_frame(warning_event)

                try:
                    while True:
                        event = stream_session_manager.poll(session)
                        if event is not None:
                            yield stream_session_manager.to_sse_frame(event)
                            if event.event in ("completed", "error"):
                                break
                            next_heartbeat = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(seconds=SSE_HEARTBEAT_SECONDS)
                            continue

                        now = datetime.now(ZoneInfo("Asia/Seoul"))
                        if now <= warmup_deadline:
                            heartbeat = stream_session_manager.make_heartbeat(valid_simulation_id)
                            yield stream_session_manager.to_sse_frame(heartbeat)
                            warmup_deadline = now
                            continue

                        if now >= next_heartbeat:
                            heartbeat = stream_session_manager.make_heartbeat(valid_simulation_id)
                            yield stream_session_manager.to_sse_frame(heartbeat)
                            next_heartbeat = now + timedelta(seconds=SSE_HEARTBEAT_SECONDS)

                        await asyncio.sleep(SSE_POLL_TIMEOUT_SECONDS)
                finally:
                    stream_session_manager.close(session)
                    LOGGER.info(
                        "sse.connect.closed request_id=%s simulation_id=%s session_id=%s",
                        request_id,
                        valid_simulation_id,
                        session.session_id,
                    )

            return StreamingResponse(
                _stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "X-Request-Id": request_id,
                },
            )
        except Exception as exc:
            status_code, envelope = ErrorHandler.to_http_error(exc, request_id)
            log_fn = LOGGER.exception if status_code >= 500 else LOGGER.warning
            log_fn(
                "sse.connect.error request_id=%s simulation_id=%s status=%s code=%s message=%s",
                request_id,
                simulation_id,
                status_code,
                envelope.get("error", {}).get("code"),
                envelope.get("error", {}).get("message"),
            )
            return JSONResponse(status_code=status_code, content=envelope)

    return router
