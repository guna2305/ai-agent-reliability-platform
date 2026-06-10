from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.value_objects import RunStatus


@dataclass(frozen=True)
class StartRunDTO:
    agent_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompleteRunDTO:
    run_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class FailRunDTO:
    run_id: str
    error_message: str


@dataclass(frozen=True)
class AgentRunDTO:
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
