from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    request_id: str
    timestamp: datetime


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ApiEnvelope(BaseModel):
    success: bool
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    error: ApiErrorBody | None = None
    meta: ApiMeta


class SimulationStartRequest(BaseModel):
    symbol: str
    strategy: str
    symbols: list[str] | None = None
    idempotency_key: str | None = None


class SimulationStartResponse(BaseModel):
    simulation_id: str
    status: Literal["queued", "running", "completed", "error"]
    symbol: str
    strategy: str
    created_at: datetime
    updated_at: datetime


class SimulationStatusResponse(BaseModel):
    simulation_id: str
    status: Literal["queued", "running", "completed", "error"]
    symbol: str
    strategy: str
    created_at: datetime
    updated_at: datetime
    error_code: str | None = None
    error_message: str | None = None


class SimulationListQuery(BaseModel):
    status: str | None = None
    offset: int = Field(default=0, ge=0, le=100000)
    limit: int = Field(default=20, ge=1, le=100)


class ReportQuery(BaseModel):
    schema_version: str = "1.0"
    include_no_trade: bool = True
    sort_order: Literal["asc", "desc"] = "asc"


class SseEvent(BaseModel):
    id: int
    event: str
    retry: int = 3000
    data: dict[str, Any]


class SimulationStartResult(BaseModel):
    simulation_id: str
    status: str
    symbol: str
    strategy: str
    created_at: datetime
    updated_at: datetime


class InternalSimulationState(BaseModel):
    simulation_id: str
    status: str
    symbol: str
    strategy: str
    created_at: datetime
    updated_at: datetime
    error_code: str | None = None
    error_message: str | None = None


class ReportFacadeQuery(BaseModel):
    schema_version: str
    include_no_trade: bool
    sort_order: str


def decimal_to_string(value: Decimal) -> str:
    return format(value, "f")
