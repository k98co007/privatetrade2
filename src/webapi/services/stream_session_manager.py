from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from webapi.constants import SSE_BUFFER_SIZE, SSE_RETRY_MS
from webapi.models import SseEvent


@dataclass
class StreamSession:
    session_id: str
    simulation_id: str
    cursor_event_id: int


class StreamSessionManager:
    def __init__(self, buffer_size: int = SSE_BUFFER_SIZE) -> None:
        self.buffer_size = buffer_size
        self._lock = threading.Lock()
        self._events: dict[str, deque[SseEvent]] = {}
        self._next_id: dict[str, int] = {}

    def open(self, simulation_id: str, session_id: str, last_event_id: int | None = None) -> StreamSession:
        with self._lock:
            if simulation_id not in self._events:
                self._events[simulation_id] = deque(maxlen=self.buffer_size)
                self._next_id[simulation_id] = 1

            cursor = last_event_id or 0
            return StreamSession(session_id=session_id, simulation_id=simulation_id, cursor_event_id=cursor)

    def close(self, session: StreamSession) -> None:
        return

    def append_event(self, simulation_id: str, event: str, data: dict[str, Any]) -> SseEvent:
        with self._lock:
            if simulation_id not in self._events:
                self._events[simulation_id] = deque(maxlen=self.buffer_size)
                self._next_id[simulation_id] = 1

            event_id = self._next_id[simulation_id]
            self._next_id[simulation_id] = event_id + 1
            payload = dict(data)
            payload["simulation_id"] = simulation_id
            sse_event = SseEvent(id=event_id, event=event, retry=SSE_RETRY_MS, data=payload)
            self._events[simulation_id].append(sse_event)
            return sse_event

    def poll(self, session: StreamSession) -> SseEvent | None:
        with self._lock:
            events = self._events.get(session.simulation_id)
            if not events:
                return None

            for event in events:
                if event.id > session.cursor_event_id:
                    session.cursor_event_id = event.id
                    return event
            return None

    def has_replay_gap(self, simulation_id: str, last_event_id: int) -> bool:
        with self._lock:
            events = self._events.get(simulation_id)
            if not events:
                return False
            oldest = events[0].id
            return last_event_id < oldest - 1

    def latest_event(self, simulation_id: str) -> SseEvent | None:
        with self._lock:
            events = self._events.get(simulation_id)
            if not events:
                return None
            return events[-1]

    def make_heartbeat(self, simulation_id: str) -> SseEvent:
        return self.append_event(
            simulation_id=simulation_id,
            event="heartbeat",
            data={"server_time": datetime.now(ZoneInfo("Asia/Seoul")).isoformat()},
        )

    @staticmethod
    def to_sse_frame(event: SseEvent) -> str:
        payload = json.dumps(event.data, ensure_ascii=False)
        return f"id: {event.id}\\nevent: {event.event}\\nretry: {event.retry}\\ndata: {payload}\\n\\n"
