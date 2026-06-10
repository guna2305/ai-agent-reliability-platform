from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects import AgentStatus


@dataclass(frozen=True)
class CreateAgentDTO:
    name: str
    description: str
    version: str = "1.0.0"
    tags: list[str] | None = None


@dataclass(frozen=True)
class UpdateAgentDTO:
    agent_id: str
    description: str | None = None
    version: str | None = None
    tags: list[str] | None = None


@dataclass(frozen=True)
class AgentDTO:
    id: str
    name: str
    description: str
    version: str
    status: AgentStatus
    tags: list[str]
    created_at: datetime
    updated_at: datetime
