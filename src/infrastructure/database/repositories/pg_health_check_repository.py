from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import HealthCheckRepository
from src.domain.entities import HealthCheck
from src.domain.value_objects import HealthStatus
from src.infrastructure.database.models import HealthCheckModel


class PostgresHealthCheckRepository(HealthCheckRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, health_check: HealthCheck) -> HealthCheck:
        model = _to_model(health_check)
        self._session.add(model)
        await self._session.flush()
        return health_check

    async def get_latest_by_agent(self, agent_id: str) -> HealthCheck | None:
        stmt = (
            select(HealthCheckModel)
            .where(HealthCheckModel.agent_id == agent_id)
            .order_by(HealthCheckModel.checked_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_by_agent(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[HealthCheck]:
        stmt = (
            select(HealthCheckModel)
            .where(HealthCheckModel.agent_id == agent_id)
            .order_by(HealthCheckModel.checked_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]


def _to_model(check: HealthCheck) -> HealthCheckModel:
    return HealthCheckModel(
        id=check.id,
        agent_id=check.agent_id,
        status=check.status.value,
        checked_at=check.checked_at,
        response_time_ms=check.response_time_ms,
        message=check.message,
    )


def _to_entity(model: HealthCheckModel) -> HealthCheck:
    return HealthCheck(
        id=model.id,
        agent_id=model.agent_id,
        status=HealthStatus(model.status),
        checked_at=model.checked_at,
        response_time_ms=model.response_time_ms,
        message=model.message,
    )
