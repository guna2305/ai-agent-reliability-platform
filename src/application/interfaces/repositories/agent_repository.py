from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import Agent
from src.domain.value_objects import AgentStatus


class AgentRepository(ABC):
    @abstractmethod
    async def save(self, agent: Agent) -> Agent:
        ...

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Agent | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Agent | None:
        ...

    @abstractmethod
    async def list_all(
        self,
        status: AgentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Agent]:
        ...

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        ...

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        ...

    @abstractmethod
    async def count(self, status: AgentStatus | None = None) -> int:
        ...
