from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .constants import (
    ERROR_CODES,
    EVENT_COMPLETED,
    EVENT_ERROR,
    EVENT_PROGRESS,
    EVENT_TRADE,
    EVENT_WARNING,
)


EventDispatcher = Callable[[str, dict[str, Any]], None]


class SimulationEventEmitter:
    def __init__(self, dispatcher: EventDispatcher | None = None) -> None:
        self.dispatcher = dispatcher
        self.events: list[dict[str, Any]] = []

    def emit_progress(
        self,
        current_day: int,
        total_days: int,
        trading_date: date,
        status: str,
    ) -> None:
        payload = {
            "current_day": current_day,
            "total_days": total_days,
            "trading_date": trading_date.isoformat(),
            "status": status,
        }
        self._emit_with_retry(EVENT_PROGRESS, payload)

    def emit_trade(self, trade_record: Any) -> None:
        payload = {
            "trade_date": trade_record.trade_date.isoformat(),
            "sell_reason": trade_record.sell_reason,
            "net_profit": str(trade_record.net_profit),
            "seed_money_after": str(trade_record.seed_money_after),
        }
        self._emit_with_retry(EVENT_TRADE, payload)

    def emit_warning(self, code: str, message: str, trading_date: date) -> None:
        payload = {
            "code": code,
            "message": message,
            "trading_date": trading_date.isoformat(),
        }
        self._emit_with_retry(EVENT_WARNING, payload)

    def emit_error(self, code: str, message: str, detail: str | None = None) -> None:
        payload = {
            "code": code,
            "message": message,
        }
        if detail is not None:
            payload["detail"] = detail
        self._emit_with_retry(EVENT_ERROR, payload)

    def emit_completed(self, simulation_id: str, final_seed: Decimal, summary: dict[str, Any]) -> None:
        payload = {
            "simulation_id": simulation_id,
            "final_seed": str(final_seed),
            "summary": summary,
        }
        self._emit_with_retry(EVENT_COMPLETED, payload)

    def _emit_with_retry(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "type": event_type,
            "timestamp": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            "payload": payload,
        }
        self.events.append(event)

        if self.dispatcher is None:
            return

        try:
            self.dispatcher(event_type, payload)
        except Exception:
            try:
                self.dispatcher(event_type, payload)
            except Exception as exc:
                warning_event = {
                    "type": EVENT_WARNING,
                    "timestamp": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                    "payload": {
                        "code": ERROR_CODES["E_SIM_008"],
                        "message": "event_dispatch_failed",
                        "event_type": event_type,
                        "detail": str(exc),
                    },
                }
                self.events.append(warning_event)
