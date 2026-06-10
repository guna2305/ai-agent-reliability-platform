from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import AgentRepository
from src.domain.entities import Agent
from src.domain.value_objects import AgentStatus
from src.infrastructure.database.models import AgentModel


class PostgresAgentRepository(AgentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, agent: Agent) -> Agent:
        model = _to_model(agent)
        self._session.add(model)
        await self._session.flush()
        return agent

    async def get_by_id(self, agent_id: str) -> Agent | None:
        result = await self._session.get(AgentModel, agent_id)
        return _to_entity(result) if result else None

    async def get_by_name(self, name: str) -> Agent | None:
        stmt = select(AgentModel).where(AgentModel.name == name)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_all(
        self,
        status: AgentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Agent]:
        stmt = select(AgentModel).order_by(AgentModel.created_at.desc())
        if status:
            stmt = stmt.where(AgentModel.status == status.value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def update(self, agent: Agent) -> Agent:
        model = await self._session.get(AgentModel, agent.id)
        if model:
            model.name = agent.name
            model.description = agent.description
            model.version = agent.version
            model.status = agent.status.value
            model.tags = agent.tags
            model.updated_at = agent.updated_at
            await self._session.flush()
        return agent

    async def delete(self, agent_id: str) -> bool:
        model = await self._session.get(AgentModel, agent_id)
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self, status: AgentStatus | None = None) -> int:
        stmt = select(func.count()).select_from(AgentModel)
        if status:
            stmt = stmt.where(AgentModel.status == status.value)
        result = await self._session.execute(stmt)
        return result.scalar_one()


def _to_model(agent: Agent) -> AgentModel:
    return AgentModel(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        version=agent.version,
        status=agent.status.value,
        tags=agent.tags,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


def _to_entity(model: AgentModel) -> Agent:
    return Agent(
        id=model.id,
        name=model.name,
        description=model.description,
        version=model.version,
        status=AgentStatus(model.status),
        tags=model.tags or [],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
