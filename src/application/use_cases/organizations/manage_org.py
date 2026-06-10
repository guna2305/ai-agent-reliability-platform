from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import (
    OrganizationRepository,
    OrgMemberRepository,
    UserRepository,
)
from src.domain.entities import Organization, OrgMember
from src.domain.exceptions import DomainException


class OrgNotFoundError(DomainException):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Organization '{slug}' not found")


class NotOrgMemberError(DomainException):
    def __init__(self) -> None:
        super().__init__("You are not a member of this organization")


class InsufficientPermissionError(DomainException):
    def __init__(self, required: str) -> None:
        super().__init__(f"Role '{required}' or higher is required")


@dataclass(frozen=True)
class CreateOrgDTO:
    name: str
    description: str | None
    user_id: str


@dataclass(frozen=True)
class InviteMemberDTO:
    org_id: str
    email: str
    role: str
    inviter_id: str


class CreateOrganizationUseCase:
    def __init__(
        self,
        org_repo: OrganizationRepository,
        member_repo: OrgMemberRepository,
    ) -> None:
        self._org_repo = org_repo
        self._member_repo = member_repo

    async def execute(self, dto: CreateOrgDTO) -> Organization:
        org = Organization.create(name=dto.name, description=dto.description)
        await self._org_repo.save(org)
        member = OrgMember.create(org_id=org.id, user_id=dto.user_id, role="owner")
        await self._member_repo.save(member)
        return org


class GetOrganizationUseCase:
    def __init__(
        self,
        org_repo: OrganizationRepository,
        member_repo: OrgMemberRepository,
    ) -> None:
        self._org_repo = org_repo
        self._member_repo = member_repo

    async def execute(self, slug: str, user_id: str) -> tuple[Organization, OrgMember]:
        org = await self._org_repo.get_by_slug(slug)
        if not org:
            raise OrgNotFoundError(slug)
        member = await self._member_repo.get(org.id, user_id)
        if not member:
            raise NotOrgMemberError()
        return org, member


class ListOrganizationsUseCase:
    def __init__(self, org_repo: OrganizationRepository) -> None:
        self._org_repo = org_repo

    async def execute(self, user_id: str) -> list[Organization]:
        return await self._org_repo.list_for_user(user_id)


class InviteMemberUseCase:
    def __init__(
        self,
        org_repo: OrganizationRepository,
        member_repo: OrgMemberRepository,
        user_repo: UserRepository,
    ) -> None:
        self._org_repo = org_repo
        self._member_repo = member_repo
        self._user_repo = user_repo

    async def execute(self, dto: InviteMemberDTO) -> OrgMember:
        inviter = await self._member_repo.get(dto.org_id, dto.inviter_id)
        if not inviter or inviter.role not in ("owner", "admin"):
            raise InsufficientPermissionError("admin")

        user = await self._user_repo.get_by_email(dto.email)
        if not user:
            raise DomainException(f"No user with email '{dto.email}'")

        existing = await self._member_repo.get(dto.org_id, user.id)
        if existing:
            raise DomainException(f"User is already a member")

        member = OrgMember.create(org_id=dto.org_id, user_id=user.id, role=dto.role)
        return await self._member_repo.save(member)
