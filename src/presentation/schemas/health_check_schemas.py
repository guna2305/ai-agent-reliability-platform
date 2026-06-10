from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.domain.value_objects import HealthStatus


class RecordHealthCheckRequest(BaseModel):
    agent_id: str
    status: HealthStatus
    response_time_ms: int | None = None
    message: str | None = None


class HealthCheckResponse(BaseModel):
    id: str
    agent_id: str
    status: HealthStatus
    checked_at: datetime
    response_time_ms: int | None
    message: str | None

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
