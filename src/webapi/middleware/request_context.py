from __future__ import annotations

import itertools
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request

from webapi.constants import HEADER_REQUEST_ID


_request_sequence = itertools.count(1)
LOGGER = logging.getLogger("webapi.request")


def _build_request_id() -> str:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    return f"REQ-{now.strftime('%Y%m%d')}-{next(_request_sequence):06d}"


def configure_request_context(app: FastAPI) -> None:
    @app.middleware("http")
    async def _request_context_middleware(request: Request, call_next):
        incoming = request.headers.get(HEADER_REQUEST_ID)
        request_id = incoming.strip() if incoming and incoming.strip() else _build_request_id()
        request.state.request_id = request_id
        started = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        LOGGER.info(
            "request.start request_id=%s method=%s path=%s client=%s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            LOGGER.exception(
                "request.error request_id=%s method=%s path=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers[HEADER_REQUEST_ID] = request_id
        LOGGER.info(
            "request.end request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
