from __future__ import annotations

from dataclasses import dataclass

from src.application.dtos import AgentDTO
from src.application.interfaces.repositories import AgentRepository
from src.domain.entities import Agent
from src.domain.value_objects import AgentStatus


@dataclass(frozen=True)
class ListAgentsQuery:
    status: AgentStatus | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class AgentListResult:
    items: list[AgentDTO]
    total: int
    limit: int
    offset: int


class ListAgentsUseCase:
    def __init__(self, agent_repo: AgentRepository) -> None:
        self._agent_repo = agent_repo

    async def execute(self, query: ListAgentsQuery) -> AgentListResult:
        agents = await self._agent_repo.list_all(
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._agent_repo.count(status=query.status)
        return AgentListResult(
            items=[_to_dto(a) for a in agents],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )


def _to_dto(agent: Agent) -> AgentDTO:
    return AgentDTO(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        version=agent.version,
        status=agent.status,
        tags=agent.tags,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )
