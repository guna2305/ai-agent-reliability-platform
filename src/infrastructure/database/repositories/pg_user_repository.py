from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import UserRepository
from src.domain.entities import User
from src.infrastructure.database.models.user_model import UserModel


class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> User:
        self._session.add(_to_model(user))
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        row = await self._session.get(UserModel, user_id)
        return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def update(self, user: User) -> User:
        row = await self._session.get(UserModel, user.id)
        if row:
            row.email = user.email
            row.hashed_password = user.hashed_password
            row.full_name = user.full_name
            row.is_active = user.is_active
            row.updated_at = user.updated_at
            await self._session.flush()
        return user


def _to_model(u: User) -> UserModel:
    return UserModel(
        id=u.id, email=u.email, hashed_password=u.hashed_password,
        full_name=u.full_name, is_active=u.is_active, is_superuser=u.is_superuser,
        created_at=u.created_at, updated_at=u.updated_at,
    )


def _to_entity(m: UserModel) -> User:
    return User(
        id=m.id, email=m.email, hashed_password=m.hashed_password,
        full_name=m.full_name, is_active=m.is_active, is_superuser=m.is_superuser,
        created_at=m.created_at, updated_at=m.updated_at,
    )
