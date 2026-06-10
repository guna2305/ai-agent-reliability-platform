from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.application.interfaces.repositories import AgentV2Repository, AgentVersionRepository
from src.domain.entities import AgentVersion
from src.domain.exceptions import DomainException


class AgentV2NotFoundError(DomainException):
    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent '{agent_id}' not found")


class AgentVersionNotFoundError(DomainException):
    def __init__(self, version_id: str) -> None:
        super().__init__(f"Agent version '{version_id}' not found")


@dataclass(frozen=True)
class CreateAgentV2DTO:
    org_id: str
    name: str
    created_by: str
    description: str | None = None
    agent_type: str = "custom"
    framework: str = "custom"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateAgentV2DTO:
    description: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    framework: str | None = None


@dataclass(frozen=True)
class CreateVersionDTO:
    agent_id: str
    version: str
    created_by: str
    config: dict[str, Any] = field(default_factory=dict)
    system_prompt: str | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    description: str | None = None


class CreateAgentV2UseCase:
    def __init__(self, agent_repo: AgentV2Repository) -> None:
        self._repo = agent_repo

    async def execute(self, dto: CreateAgentV2DTO) -> dict:
        now = datetime.now(timezone.utc)
        data = {
            "id": str(uuid.uuid4()),
            "org_id": dto.org_id,
            "name": dto.name,
            "description": dto.description,
            "agent_type": dto.agent_type,
            "framework": dto.framework,
            "status": "active",
            "created_by": dto.created_by,
            "tags": dto.tags,
            "metadata": dto.metadata,
            "created_at": now,
            "updated_at": now,
        }
        return await self._repo.save(data)


class ListAgentsV2UseCase:
    def __init__(self, agent_repo: AgentV2Repository) -> None:
        self._repo = agent_repo

    async def execute(
        self,
        org_id: str,
        status: str | None = None,
        agent_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        agents = await self._repo.list_by_org(
            org_id=org_id, status=status, agent_type=agent_type,
            limit=limit, offset=offset,
        )
        total = await self._repo.count(org_id=org_id, status=status)
        return agents, total


class GetAgentV2UseCase:
    def __init__(self, agent_repo: AgentV2Repository) -> None:
        self._repo = agent_repo

    async def execute(self, agent_id: str, org_id: str) -> dict:
        agent = await self._repo.get_by_id(agent_id, org_id)
        if not agent:
            raise AgentV2NotFoundError(agent_id)
        return agent


class UpdateAgentV2UseCase:
    def __init__(self, agent_repo: AgentV2Repository) -> None:
        self._repo = agent_repo

    async def execute(self, agent_id: str, org_id: str, dto: UpdateAgentV2DTO) -> dict:
        agent = await self._repo.get_by_id(agent_id, org_id)
        if not agent:
            raise AgentV2NotFoundError(agent_id)
        updates = {k: v for k, v in {
            "description": dto.description,
            "status": dto.status,
            "tags": dto.tags,
            "framework": dto.framework,
        }.items() if v is not None}
        result = await self._repo.update(agent_id, updates)
        return result or agent


class DeleteAgentV2UseCase:
    def __init__(self, agent_repo: AgentV2Repository) -> None:
        self._repo = agent_repo

    async def execute(self, agent_id: str, org_id: str) -> None:
        deleted = await self._repo.delete(agent_id, org_id)
        if not deleted:
            raise AgentV2NotFoundError(agent_id)


class CreateAgentVersionUseCase:
    def __init__(
        self,
        agent_repo: AgentV2Repository,
        version_repo: AgentVersionRepository,
    ) -> None:
        self._agent_repo = agent_repo
        self._version_repo = version_repo

    async def execute(self, org_id: str, dto: CreateVersionDTO) -> AgentVersion:
        agent = await self._agent_repo.get_by_id(dto.agent_id, org_id)
        if not agent:
            raise AgentV2NotFoundError(dto.agent_id)

        version_number = await self._version_repo.count_by_agent(dto.agent_id) + 1
        version = AgentVersion.create(
            agent_id=dto.agent_id,
            version=dto.version,
            version_number=version_number,
            created_by=dto.created_by,
            config=dto.config,
            system_prompt=dto.system_prompt,
            tools=dto.tools,
            description=dto.description,
        )
        return await self._version_repo.save(version)


class ListAgentVersionsUseCase:
    def __init__(self, version_repo: AgentVersionRepository) -> None:
        self._repo = version_repo

    async def execute(self, agent_id: str) -> list[AgentVersion]:
        return await self._repo.list_by_agent(agent_id)


class PromoteVersionUseCase:
    def __init__(
        self,
        agent_repo: AgentV2Repository,
        version_repo: AgentVersionRepository,
    ) -> None:
        self._agent_repo = agent_repo
        self._version_repo = version_repo

    async def execute(self, version_id: str, agent_id: str, org_id: str) -> AgentVersion:
        agent = await self._agent_repo.get_by_id(agent_id, org_id)
        if not agent:
            raise AgentV2NotFoundError(agent_id)

        version = await self._version_repo.get_by_id(version_id)
        if not version or version.agent_id != agent_id:
            raise AgentVersionNotFoundError(version_id)

        await self._version_repo.demote_all(agent_id)
        version.promote_to_production()
        return await self._version_repo.update(version)
