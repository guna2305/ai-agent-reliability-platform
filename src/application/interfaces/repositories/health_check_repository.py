from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import HealthCheck


class HealthCheckRepository(ABC):
    @abstractmethod
    async def save(self, health_check: HealthCheck) -> HealthCheck:
        ...

    @abstractmethod
    async def get_latest_by_agent(self, agent_id: str) -> HealthCheck | None:
        ...

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[HealthCheck]:
        ...
