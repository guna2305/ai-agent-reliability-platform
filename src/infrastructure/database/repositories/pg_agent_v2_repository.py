from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import AgentV2Repository, AgentVersionRepository
from src.domain.entities import AgentVersion
from src.infrastructure.database.models.agent_extended_model import AgentOrgModel, AgentVersionModel


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return f"{slug[:50]}-{str(uuid.uuid4())[:8]}"


class PostgresAgentV2Repository(AgentV2Repository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, agent_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        model = AgentOrgModel(
            id=agent_data["id"],
            org_id=agent_data["org_id"],
            name=agent_data["name"],
            slug=agent_data.get("slug") or _slugify(agent_data["name"]),
            description=agent_data.get("description"),
            agent_type=agent_data.get("agent_type", "custom"),
            framework=agent_data.get("framework", "custom"),
            status=agent_data.get("status", "active"),
            created_by=agent_data["created_by"],
            tags=agent_data.get("tags", []),
            metadata_=agent_data.get("metadata", {}),
            created_at=agent_data.get("created_at", now),
            updated_at=agent_data.get("updated_at", now),
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_dict(model)

    async def get_by_id(self, agent_id: str, org_id: str) -> dict | None:
        stmt = select(AgentOrgModel).where(
            AgentOrgModel.id == agent_id, AgentOrgModel.org_id == org_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_dict(row) if row else None

    async def get_by_slug(self, slug: str, org_id: str) -> dict | None:
        stmt = select(AgentOrgModel).where(
            AgentOrgModel.slug == slug, AgentOrgModel.org_id == org_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_dict(row) if row else None

    async def list_by_org(
        self,
        org_id: str,
        status: str | None = None,
        agent_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        stmt = (
            select(AgentOrgModel)
            .where(AgentOrgModel.org_id == org_id)
            .order_by(AgentOrgModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(AgentOrgModel.status == status)
        if agent_type:
            stmt = stmt.where(AgentOrgModel.agent_type == agent_type)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_model_to_dict(r) for r in result.scalars().all()]

    async def update(self, agent_id: str, updates: dict) -> dict | None:
        row = await self._session.get(AgentOrgModel, agent_id)
        if not row:
            return None
        for key, value in updates.items():
            if hasattr(row, key):
                setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return _model_to_dict(row)

    async def delete(self, agent_id: str, org_id: str) -> bool:
        stmt = select(AgentOrgModel).where(
            AgentOrgModel.id == agent_id, AgentOrgModel.org_id == org_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def count(self, org_id: str, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(AgentOrgModel).where(AgentOrgModel.org_id == org_id)
        if status:
            stmt = stmt.where(AgentOrgModel.status == status)
        result = await self._session.execute(stmt)
        return result.scalar_one()


class PostgresAgentVersionRepository(AgentVersionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, version: AgentVersion) -> AgentVersion:
        self._session.add(_ver_to_model(version))
        await self._session.flush()
        return version

    async def get_by_id(self, version_id: str) -> AgentVersion | None:
        row = await self._session.get(AgentVersionModel, version_id)
        return _ver_to_entity(row) if row else None

    async def list_by_agent(self, agent_id: str) -> list[AgentVersion]:
        stmt = (
            select(AgentVersionModel)
            .where(AgentVersionModel.agent_id == agent_id)
            .order_by(AgentVersionModel.version_number.desc())
        )
        result = await self._session.execute(stmt)
        return [_ver_to_entity(r) for r in result.scalars().all()]

    async def get_production_version(self, agent_id: str) -> AgentVersion | None:
        stmt = select(AgentVersionModel).where(
            AgentVersionModel.agent_id == agent_id,
            AgentVersionModel.is_production.is_(True),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _ver_to_entity(row) if row else None

    async def demote_all(self, agent_id: str) -> None:
        stmt = (
            update(AgentVersionModel)
            .where(AgentVersionModel.agent_id == agent_id)
            .values(is_production=False)
        )
        await self._session.execute(stmt)

    async def update(self, version: AgentVersion) -> AgentVersion:
        row = await self._session.get(AgentVersionModel, version.id)
        if row:
            row.is_production = version.is_production
            row.description = version.description
            await self._session.flush()
        return version

    async def count_by_agent(self, agent_id: str) -> int:
        stmt = select(func.count()).select_from(AgentVersionModel).where(
            AgentVersionModel.agent_id == agent_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


def _model_to_dict(m: AgentOrgModel) -> dict:
    return {
        "id": m.id, "org_id": m.org_id, "name": m.name, "slug": m.slug,
        "description": m.description, "agent_type": m.agent_type, "framework": m.framework,
        "status": m.status, "created_by": m.created_by, "tags": m.tags or [],
        "metadata": m.metadata_ or {}, "created_at": m.created_at, "updated_at": m.updated_at,
    }


def _ver_to_model(v: AgentVersion) -> AgentVersionModel:
    return AgentVersionModel(
        id=v.id, agent_id=v.agent_id, version=v.version, version_number=v.version_number,
        description=v.description, config=v.config, system_prompt=v.system_prompt,
        tools=v.tools, is_production=v.is_production, created_by=v.created_by,
        metadata_=v.metadata, created_at=v.created_at,
    )


def _ver_to_entity(m: AgentVersionModel) -> AgentVersion:
    return AgentVersion(
        id=m.id, agent_id=m.agent_id, version=m.version, version_number=m.version_number,
        description=m.description, config=m.config or {}, system_prompt=m.system_prompt,
        tools=m.tools or [], is_production=m.is_production, created_by=m.created_by,
        metadata=m.metadata_ or {}, created_at=m.created_at,
    )
