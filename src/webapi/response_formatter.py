from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .models import ApiEnvelope, ApiErrorBody, ApiMeta


def _now_seoul() -> datetime:
    return datetime.now(ZoneInfo("Asia/Seoul"))


class ResponseFormatter:
    @staticmethod
    def ok(data: dict[str, Any] | list[dict[str, Any]] | None, request_id: str) -> dict[str, Any]:
        envelope = ApiEnvelope(
            success=True,
            data=data,
            meta=ApiMeta(request_id=request_id, timestamp=_now_seoul()),
        )
        return envelope.model_dump(mode="json")

    @staticmethod
    def error(code: str, message: str, request_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        envelope = ApiEnvelope(
            success=False,
            error=ApiErrorBody(code=code, message=message, details=details),
            meta=ApiMeta(request_id=request_id, timestamp=_now_seoul()),
        )
        return envelope.model_dump(mode="json")
