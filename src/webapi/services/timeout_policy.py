from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import TypeVar

from webapi.errors import DependencyTimeoutError


T = TypeVar("T")
LOGGER = logging.getLogger("webapi.timeout")


async def run_with_timeout(awaitable: Awaitable[T], timeout_seconds: float, operation: str) -> T:
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        LOGGER.warning(
            "dependency.timeout operation=%s timeout_seconds=%s",
            operation,
            timeout_seconds,
        )
        raise DependencyTimeoutError(
            code="DEPENDENCY_TIMEOUT",
            message="의존 모듈 응답이 지연되었습니다",
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        ) from exc
