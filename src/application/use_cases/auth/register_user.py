from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import (
    OrganizationRepository,
    OrgMemberRepository,
    UserRepository,
)
from src.domain.entities import Organization, OrgMember, User
from src.domain.exceptions import DomainException
from src.infrastructure.security.jwt_service import create_access_token, create_refresh_token
from src.infrastructure.security.password_service import hash_password


class EmailAlreadyRegisteredError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email '{email}' is already registered")


@dataclass(frozen=True)
class RegisterUserDTO:
    email: str
    password: str
    full_name: str
    org_name: str | None = None


@dataclass(frozen=True)
class AuthTokensDTO:
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str
    email: str
    full_name: str


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        member_repo: OrgMemberRepository,
    ) -> None:
        self._user_repo = user_repo
        self._org_repo = org_repo
        self._member_repo = member_repo

    async def execute(self, dto: RegisterUserDTO) -> AuthTokensDTO:
        existing = await self._user_repo.get_by_email(dto.email)
        if existing:
            raise EmailAlreadyRegisteredError(dto.email)

        user = User.create(
            email=dto.email,
            hashed_password=hash_password(dto.password),
            full_name=dto.full_name,
        )
        await self._user_repo.save(user)

        # Auto-create a personal org for the new user
        org_name = dto.org_name or f"{dto.full_name}'s Organization"
        org = Organization.create(name=org_name)
        await self._org_repo.save(org)

        member = OrgMember.create(org_id=org.id, user_id=user.id, role="owner")
        await self._member_repo.save(member)

        access_token, _ = create_access_token(user.id, user.email, user.is_superuser)
        refresh_token, _ = create_refresh_token(user.id)

        return AuthTokensDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
        )
