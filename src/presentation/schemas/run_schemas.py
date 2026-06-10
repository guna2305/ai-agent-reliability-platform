from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.value_objects import RunStatus


class StartRunRequest(BaseModel):
    agent_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompleteRunRequest(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None


class FailRunRequest(BaseModel):
    error_message: str = Field(..., min_length=1)


class AgentRunResponse(BaseModel):
    id: str
    agent_id: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    error_message: str | None
    metadata: dict[str, Any]

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    items: list[AgentRunResponse]
    total: int
    limit: int
    offset: int
