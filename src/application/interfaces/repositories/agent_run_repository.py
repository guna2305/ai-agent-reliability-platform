from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import AgentRun
from src.domain.value_objects import RunStatus


class AgentRunRepository(ABC):
    @abstractmethod
    async def save(self, run: AgentRun) -> AgentRun:
        ...

    @abstractmethod
    async def get_by_id(self, run_id: str) -> AgentRun | None:
        ...

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: str,
        status: RunStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentRun]:
        ...

    @abstractmethod
    async def update(self, run: AgentRun) -> AgentRun:
        ...

    @abstractmethod
    async def count_by_agent(
        self,
        agent_id: str,
        status: RunStatus | None = None,
    ) -> int:
        ...
