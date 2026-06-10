from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DomainEvent:
    occurred_at: datetime

    @classmethod
    def now(cls) -> datetime:
        return datetime.now(timezone.utc)


@dataclass
class AgentCreated(DomainEvent):
    agent_id: str
    name: str


@dataclass
class AgentStatusChanged(DomainEvent):
    agent_id: str
    old_status: str
    new_status: str


@dataclass
class AgentRunCompleted(DomainEvent):
    run_id: str
    agent_id: str
    status: str
    duration_ms: int | None


@dataclass
class AgentRunFailed(DomainEvent):
    run_id: str
    agent_id: str
    error_message: str
