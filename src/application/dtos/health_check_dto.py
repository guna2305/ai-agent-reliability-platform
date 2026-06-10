from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects import HealthStatus


@dataclass(frozen=True)
class RecordHealthCheckDTO:
    agent_id: str
    status: HealthStatus
    response_time_ms: int | None = None
    message: str | None = None


@dataclass(frozen=True)
class HealthCheckDTO:
    id: str
    agent_id: str
    status: HealthStatus
    checked_at: datetime
    response_time_ms: int | None
    message: str | None
