from __future__ import annotations

import itertools
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request

from webapi.constants import HEADER_REQUEST_ID


_request_sequence = itertools.count(1)


def _build_request_id() -> str:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    return f"REQ-{now.strftime('%Y%m%d')}-{next(_request_sequence):06d}"


def configure_request_context(app: FastAPI) -> None:
    @app.middleware("http")
    async def _request_context_middleware(request: Request, call_next):
        incoming = request.headers.get(HEADER_REQUEST_ID)
        request_id = incoming.strip() if incoming and incoming.strip() else _build_request_id()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[HEADER_REQUEST_ID] = request_id
        return response
