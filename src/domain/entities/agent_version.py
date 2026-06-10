from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AgentVersion:
    id: str
    agent_id: str
    version: str           # e.g. "1.2.0"
    version_number: int    # auto-increment per agent
    description: str | None
    config: dict[str, Any]          # model params, temperature, etc.
    system_prompt: str | None
    tools: list[dict[str, Any]]     # tool definitions
    is_production: bool
    created_by: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        agent_id: str,
        version: str,
        version_number: int,
        created_by: str,
        config: dict[str, Any] | None = None,
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        description: str | None = None,
    ) -> AgentVersion:
        return cls(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            version=version,
            version_number=version_number,
            description=description,
            config=config or {},
            system_prompt=system_prompt,
            tools=tools or [],
            is_production=False,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )

    def promote_to_production(self) -> None:
        self.is_production = True
