from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import AgentVersion
from src.domain.entities.agent import Agent  # legacy simple agent
# For org-scoped agents we import from the extended model path
# The AgentOrg entity reuses the existing Agent dataclass with extra fields
# handled in the DTO layer. Repos deal with domain entities only.


class AgentV2Repository(ABC):
    """Repository for org-scoped, versioned agents (agents_v2 table)."""

    @abstractmethod
    async def save(self, agent_data: dict) -> dict: ...

    @abstractmethod
    async def get_by_id(self, agent_id: str, org_id: str) -> dict | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str, org_id: str) -> dict | None: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: str,
        status: str | None = None,
        agent_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]: ...

    @abstractmethod
    async def update(self, agent_id: str, updates: dict) -> dict | None: ...

    @abstractmethod
    async def delete(self, agent_id: str, org_id: str) -> bool: ...

    @abstractmethod
    async def count(self, org_id: str, status: str | None = None) -> int: ...


class AgentVersionRepository(ABC):
    @abstractmethod
    async def save(self, version: AgentVersion) -> AgentVersion: ...

    @abstractmethod
    async def get_by_id(self, version_id: str) -> AgentVersion | None: ...

    @abstractmethod
    async def list_by_agent(self, agent_id: str) -> list[AgentVersion]: ...

    @abstractmethod
    async def get_production_version(self, agent_id: str) -> AgentVersion | None: ...

    @abstractmethod
    async def demote_all(self, agent_id: str) -> None:
        """Remove is_production from all versions for this agent."""
        ...

    @abstractmethod
    async def update(self, version: AgentVersion) -> AgentVersion: ...

    @abstractmethod
    async def count_by_agent(self, agent_id: str) -> int: ...
