from __future__ import annotations

from dataclasses import dataclass

from src.application.dtos import AgentRunDTO
from src.application.interfaces.repositories import AgentRunRepository
from src.domain.entities import AgentRun
from src.domain.value_objects import RunStatus


@dataclass(frozen=True)
class ListRunsQuery:
    agent_id: str
    status: RunStatus | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class RunListResult:
    items: list[AgentRunDTO]
    total: int
    limit: int
    offset: int


class ListRunsUseCase:
    def __init__(self, run_repo: AgentRunRepository) -> None:
        self._run_repo = run_repo

    async def execute(self, query: ListRunsQuery) -> RunListResult:
        runs = await self._run_repo.list_by_agent(
            agent_id=query.agent_id,
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._run_repo.count_by_agent(
            agent_id=query.agent_id,
            status=query.status,
        )
        return RunListResult(
            items=[_to_dto(r) for r in runs],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )


def _to_dto(run: AgentRun) -> AgentRunDTO:
    return AgentRunDTO(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        error_message=run.error_message,
        metadata=run.metadata,
    )
