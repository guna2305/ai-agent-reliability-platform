from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import Organization, OrgMember


class OrganizationRepository(ABC):
    @abstractmethod
    async def save(self, org: Organization) -> Organization: ...

    @abstractmethod
    async def get_by_id(self, org_id: str) -> Organization | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Organization | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[Organization]: ...

    @abstractmethod
    async def update(self, org: Organization) -> Organization: ...


class OrgMemberRepository(ABC):
    @abstractmethod
    async def save(self, member: OrgMember) -> OrgMember: ...

    @abstractmethod
    async def get(self, org_id: str, user_id: str) -> OrgMember | None: ...

    @abstractmethod
    async def list_by_org(self, org_id: str) -> list[OrgMember]: ...

    @abstractmethod
    async def update_role(self, org_id: str, user_id: str, role: str) -> OrgMember | None: ...

    @abstractmethod
    async def delete(self, org_id: str, user_id: str) -> bool: ...
