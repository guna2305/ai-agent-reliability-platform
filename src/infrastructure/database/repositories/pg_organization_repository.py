from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import OrganizationRepository, OrgMemberRepository
from src.domain.entities import Organization, OrgMember
from src.infrastructure.database.models.organization_model import OrganizationModel
from src.infrastructure.database.models.user_model import OrgMemberModel


class PostgresOrganizationRepository(OrganizationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, org: Organization) -> Organization:
        self._session.add(_org_to_model(org))
        await self._session.flush()
        return org

    async def get_by_id(self, org_id: str) -> Organization | None:
        row = await self._session.get(OrganizationModel, org_id)
        return _org_to_entity(row) if row else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        stmt = select(OrganizationModel).where(OrganizationModel.slug == slug)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _org_to_entity(row) if row else None

    async def list_for_user(self, user_id: str) -> list[Organization]:
        stmt = (
            select(OrganizationModel)
            .join(OrgMemberModel, OrgMemberModel.org_id == OrganizationModel.id)
            .where(OrgMemberModel.user_id == user_id)
            .order_by(OrganizationModel.name)
        )
        result = await self._session.execute(stmt)
        return [_org_to_entity(r) for r in result.scalars().all()]

    async def update(self, org: Organization) -> Organization:
        row = await self._session.get(OrganizationModel, org.id)
        if row:
            row.name = org.name
            row.slug = org.slug
            row.description = org.description
            row.plan = org.plan
            row.updated_at = org.updated_at
            await self._session.flush()
        return org


class PostgresOrgMemberRepository(OrgMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, member: OrgMember) -> OrgMember:
        self._session.add(_member_to_model(member))
        await self._session.flush()
        return member

    async def get(self, org_id: str, user_id: str) -> OrgMember | None:
        stmt = select(OrgMemberModel).where(
            OrgMemberModel.org_id == org_id, OrgMemberModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _member_to_entity(row) if row else None

    async def list_by_org(self, org_id: str) -> list[OrgMember]:
        stmt = select(OrgMemberModel).where(OrgMemberModel.org_id == org_id)
        result = await self._session.execute(stmt)
        return [_member_to_entity(r) for r in result.scalars().all()]

    async def update_role(self, org_id: str, user_id: str, role: str) -> OrgMember | None:
        stmt = select(OrgMemberModel).where(
            OrgMemberModel.org_id == org_id, OrgMemberModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.role = role
            await self._session.flush()
            return _member_to_entity(row)
        return None

    async def delete(self, org_id: str, user_id: str) -> bool:
        stmt = select(OrgMemberModel).where(
            OrgMemberModel.org_id == org_id, OrgMemberModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


def _org_to_model(o: Organization) -> OrganizationModel:
    return OrganizationModel(
        id=o.id, name=o.name, slug=o.slug, description=o.description,
        plan=o.plan, metadata_=o.metadata, created_at=o.created_at, updated_at=o.updated_at,
    )


def _org_to_entity(m: OrganizationModel) -> Organization:
    return Organization(
        id=m.id, name=m.name, slug=m.slug, description=m.description,
        plan=m.plan, metadata=m.metadata_ or {}, created_at=m.created_at, updated_at=m.updated_at,
    )


def _member_to_model(m: OrgMember) -> OrgMemberModel:
    return OrgMemberModel(id=m.id, org_id=m.org_id, user_id=m.user_id, role=m.role, created_at=m.created_at)


def _member_to_entity(m: OrgMemberModel) -> OrgMember:
    return OrgMember(id=m.id, org_id=m.org_id, user_id=m.user_id, role=m.role, created_at=m.created_at)
