from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from webapi.constants import CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_OPEN_SECONDS, CIRCUIT_WINDOW_SECONDS
from webapi.errors import CircuitOpenError


@dataclass
class CircuitBreakerState:
    state: str = "closed"
    failures: list[datetime] = field(default_factory=list)
    open_until: datetime | None = None


class CircuitBreaker:
    def __init__(self, dependency_name: str) -> None:
        self.dependency_name = dependency_name
        self._state = CircuitBreakerState()
        self._lock = threading.Lock()

    def before_call(self) -> None:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        with self._lock:
            if self._state.state == "open":
                if self._state.open_until is not None and now >= self._state.open_until:
                    self._state.state = "half_open"
                else:
                    raise CircuitOpenError(
                        code="DEPENDENCY_CIRCUIT_OPEN",
                        message="일시적으로 요청을 처리할 수 없습니다",
                        details={"dependency": self.dependency_name},
                    )

    def after_success(self) -> None:
        with self._lock:
            self._state.state = "closed"
            self._state.failures.clear()
            self._state.open_until = None

    def after_failure(self) -> None:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        with self._lock:
            if self._state.state == "half_open":
                self._state.state = "open"
                self._state.open_until = now + timedelta(seconds=CIRCUIT_OPEN_SECONDS)
                return

            window_start = now - timedelta(seconds=CIRCUIT_WINDOW_SECONDS)
            self._state.failures = [failure for failure in self._state.failures if failure >= window_start]
            self._state.failures.append(now)

            if len(self._state.failures) >= CIRCUIT_FAILURE_THRESHOLD:
                self._state.state = "open"
                self._state.open_until = now + timedelta(seconds=CIRCUIT_OPEN_SECONDS)
