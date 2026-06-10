from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.value_objects import AgentStatus


class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    tags: list[str] = Field(default_factory=list)


class UpdateAgentStatusRequest(BaseModel):
    status: AgentStatus


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    status: AgentStatus
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total: int
    limit: int
    offset: int
