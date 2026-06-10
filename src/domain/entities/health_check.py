from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from src.domain.value_objects import HealthStatus


@dataclass
class HealthCheck:
    id: str
    agent_id: str
    status: HealthStatus
    checked_at: datetime
    response_time_ms: int | None
    message: str | None

    @classmethod
    def create(
        cls,
        agent_id: str,
        status: HealthStatus,
        response_time_ms: int | None = None,
        message: str | None = None,
    ) -> HealthCheck:
        return cls(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            status=status,
            checked_at=datetime.now(timezone.utc),
            response_time_ms=response_time_ms,
            message=message,
        )

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY
