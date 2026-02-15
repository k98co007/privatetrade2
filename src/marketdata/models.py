from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class MarketDataRequest:
    symbol: str
    period: str = "60d"
    interval: str = "5m"


@dataclass(frozen=True)
class CacheFreshness:
    symbol: str
    latest_timestamp: datetime | None
    now_kst: datetime
    ttl_minutes: int

    @property
    def is_fresh(self) -> bool:
        if self.latest_timestamp is None:
            return False
        return self.latest_timestamp >= self.now_kst - timedelta(minutes=self.ttl_minutes)
