from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.value_objects import AgentStatus
from src.domain.exceptions import InvalidAgentStateError


_VALID_STATUS_TRANSITIONS: dict[AgentStatus, set[AgentStatus]] = {
    AgentStatus.ACTIVE: {AgentStatus.INACTIVE, AgentStatus.DEPRECATED},
    AgentStatus.INACTIVE: {AgentStatus.ACTIVE, AgentStatus.DEPRECATED},
    AgentStatus.DEPRECATED: set(),
}


@dataclass
class Agent:
    id: str
    name: str
    description: str
    version: str
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    tags: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        version: str = "1.0.0",
        tags: list[str] | None = None,
    ) -> Agent:
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            version=version,
            status=AgentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            tags=tags or [],
        )

    def transition_status(self, new_status: AgentStatus) -> None:
        allowed = _VALID_STATUS_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidAgentStateError(self.id, self.status.value, new_status.value)
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.transition_status(AgentStatus.INACTIVE)

    def activate(self) -> None:
        self.transition_status(AgentStatus.ACTIVE)

    def deprecate(self) -> None:
        self.transition_status(AgentStatus.DEPRECATED)

    @property
    def is_operational(self) -> bool:
        return self.status == AgentStatus.ACTIVE
