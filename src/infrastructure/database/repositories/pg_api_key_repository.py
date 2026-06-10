from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import ApiKeyRepository
from src.domain.entities import ApiKey
from src.infrastructure.database.models.user_model import ApiKeyModel


class PostgresApiKeyRepository(ApiKeyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, api_key: ApiKey) -> ApiKey:
        self._session.add(_to_model(api_key))
        await self._session.flush()
        return api_key

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        stmt = select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_by_org(self, org_id: str) -> list[ApiKey]:
        stmt = select(ApiKeyModel).where(ApiKeyModel.org_id == org_id).order_by(
            ApiKeyModel.created_at.desc()
        )
        result = await self._session.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]

    async def delete(self, key_id: str, org_id: str) -> bool:
        stmt = select(ApiKeyModel).where(
            ApiKeyModel.id == key_id, ApiKeyModel.org_id == org_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def update_last_used(self, key_id: str) -> None:
        row = await self._session.get(ApiKeyModel, key_id)
        if row:
            row.last_used_at = datetime.now(timezone.utc)
            await self._session.flush()


def _to_model(k: ApiKey) -> ApiKeyModel:
    return ApiKeyModel(
        id=k.id, org_id=k.org_id, user_id=k.user_id, name=k.name,
        key_hash=k.key_hash, key_prefix=k.key_prefix, scopes=k.scopes,
        last_used_at=k.last_used_at, expires_at=k.expires_at, created_at=k.created_at,
    )


def _to_entity(m: ApiKeyModel) -> ApiKey:
    return ApiKey(
        id=m.id, org_id=m.org_id, user_id=m.user_id, name=m.name,
        key_hash=m.key_hash, key_prefix=m.key_prefix, scopes=m.scopes or [],
        last_used_at=m.last_used_at, expires_at=m.expires_at, created_at=m.created_at,
    )
