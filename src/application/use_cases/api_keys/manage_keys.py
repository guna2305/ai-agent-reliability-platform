from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import ApiKeyRepository, OrgMemberRepository
from src.domain.entities import ApiKey
from src.domain.exceptions import DomainException


class ApiKeyNotFoundError(DomainException):
    def __init__(self) -> None:
        super().__init__("API key not found")


@dataclass(frozen=True)
class CreateApiKeyDTO:
    org_id: str
    user_id: str
    name: str
    scopes: list[str]


@dataclass(frozen=True)
class CreatedApiKeyDTO:
    api_key: ApiKey
    raw_key: str  # shown only once


class CreateApiKeyUseCase:
    def __init__(self, key_repo: ApiKeyRepository, member_repo: OrgMemberRepository) -> None:
        self._key_repo = key_repo
        self._member_repo = member_repo

    async def execute(self, dto: CreateApiKeyDTO) -> CreatedApiKeyDTO:
        member = await self._member_repo.get(dto.org_id, dto.user_id)
        if not member or member.role not in ("owner", "admin"):
            raise DomainException("Only owners and admins can create API keys")

        api_key, raw_key = ApiKey.create(
            org_id=dto.org_id,
            user_id=dto.user_id,
            name=dto.name,
            scopes=dto.scopes,
        )
        saved = await self._key_repo.save(api_key)
        return CreatedApiKeyDTO(api_key=saved, raw_key=raw_key)


class ListApiKeysUseCase:
    def __init__(self, key_repo: ApiKeyRepository) -> None:
        self._key_repo = key_repo

    async def execute(self, org_id: str) -> list[ApiKey]:
        return await self._key_repo.list_by_org(org_id)


class RevokeApiKeyUseCase:
    def __init__(self, key_repo: ApiKeyRepository, member_repo: OrgMemberRepository) -> None:
        self._key_repo = key_repo
        self._member_repo = member_repo

    async def execute(self, key_id: str, org_id: str, user_id: str) -> None:
        member = await self._member_repo.get(org_id, user_id)
        if not member or member.role not in ("owner", "admin"):
            raise DomainException("Only owners and admins can revoke API keys")
        deleted = await self._key_repo.delete(key_id, org_id)
        if not deleted:
            raise ApiKeyNotFoundError()
