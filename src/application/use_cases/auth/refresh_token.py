from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import UserRepository
from src.domain.exceptions import DomainException
from src.infrastructure.security.jwt_service import (
    decode_token,
    create_access_token,
    TokenExpiredError,
    TokenInvalidError,
)
from src.infrastructure.cache.redis_client import get_redis


class InvalidRefreshTokenError(DomainException):
    def __init__(self) -> None:
        super().__init__("Refresh token is invalid or expired")


@dataclass(frozen=True)
class RefreshTokenDTO:
    access_token: str
    token_type: str = "bearer"


class RefreshTokenUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, refresh_token: str) -> RefreshTokenDTO:
        try:
            payload = decode_token(refresh_token)
        except (TokenExpiredError, TokenInvalidError):
            raise InvalidRefreshTokenError()

        if payload.token_type != "refresh":
            raise InvalidRefreshTokenError()

        # Verify JTI exists in Redis (not revoked)
        redis = get_redis()
        stored_user_id = await redis.get(f"auth:refresh:{payload.jti}")
        if not stored_user_id or stored_user_id != payload.user_id:
            raise InvalidRefreshTokenError()

        user = await self._user_repo.get_by_id(payload.user_id)
        if not user or not user.is_active:
            raise InvalidRefreshTokenError()

        access_token, _ = create_access_token(user.id, user.email, user.is_superuser)
        return RefreshTokenDTO(access_token=access_token)
