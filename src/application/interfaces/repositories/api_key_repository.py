from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import ApiKey


class ApiKeyRepository(ABC):
    @abstractmethod
    async def save(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> ApiKey | None: ...

    @abstractmethod
    async def list_by_org(self, org_id: str) -> list[ApiKey]: ...

    @abstractmethod
    async def delete(self, key_id: str, org_id: str) -> bool: ...

    @abstractmethod
    async def update_last_used(self, key_id: str) -> None: ...
