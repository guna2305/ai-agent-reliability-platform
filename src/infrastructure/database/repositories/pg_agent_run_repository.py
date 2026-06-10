from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import AgentRunRepository
from src.domain.entities import AgentRun
from src.domain.value_objects import RunStatus
from src.infrastructure.database.models import AgentRunModel


class PostgresAgentRunRepository(AgentRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, run: AgentRun) -> AgentRun:
        model = _to_model(run)
        self._session.add(model)
        await self._session.flush()
        return run

    async def get_by_id(self, run_id: str) -> AgentRun | None:
        result = await self._session.get(AgentRunModel, run_id)
        return _to_entity(result) if result else None

    async def list_by_agent(
        self,
        agent_id: str,
        status: RunStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentRun]:
        stmt = (
            select(AgentRunModel)
            .where(AgentRunModel.agent_id == agent_id)
            .order_by(AgentRunModel.started_at.desc())
        )
        if status:
            stmt = stmt.where(AgentRunModel.status == status.value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def update(self, run: AgentRun) -> AgentRun:
        model = await self._session.get(AgentRunModel, run.id)
        if model:
            model.status = run.status.value
            model.completed_at = run.completed_at
            model.duration_ms = run.duration_ms
            model.input_tokens = run.input_tokens
            model.output_tokens = run.output_tokens
            model.error_message = run.error_message
            model.metadata_ = run.metadata
            await self._session.flush()
        return run

    async def count_by_agent(
        self,
        agent_id: str,
        status: RunStatus | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(AgentRunModel)
            .where(AgentRunModel.agent_id == agent_id)
        )
        if status:
            stmt = stmt.where(AgentRunModel.status == status.value)
        result = await self._session.execute(stmt)
        return result.scalar_one()


def _to_model(run: AgentRun) -> AgentRunModel:
    return AgentRunModel(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status.value,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        error_message=run.error_message,
        metadata_=run.metadata,
    )


def _to_entity(model: AgentRunModel) -> AgentRun:
    return AgentRun(
        id=model.id,
        agent_id=model.agent_id,
        status=RunStatus(model.status),
        started_at=model.started_at,
        completed_at=model.completed_at,
        duration_ms=model.duration_ms,
        input_tokens=model.input_tokens,
        output_tokens=model.output_tokens,
        error_message=model.error_message,
        metadata=model.metadata_ or {},
    )
