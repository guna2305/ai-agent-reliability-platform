from __future__ import annotations

from datetime import UTC, datetime

from src.infrastructure.cache.redis_client import blacklist_token, get_redis
from src.infrastructure.security.jwt_service import (
    TokenExpiredError,
    TokenInvalidError,
    decode_token,
)


class LogoutUseCase:
    async def execute(self, access_token: str, refresh_token: str | None = None) -> None:
        redis = get_redis()

        try:
            payload = decode_token(access_token)
            remaining = int((payload.exp - datetime.now(UTC)).total_seconds())
            if remaining > 0:
                await blacklist_token(payload.jti, remaining)
        except (TokenExpiredError, TokenInvalidError):
            pass  # Already expired — nothing to blacklist

        if refresh_token:
            try:
                ref_payload = decode_token(refresh_token)
                await redis.delete(f"auth:refresh:{ref_payload.jti}")
            except (TokenExpiredError, TokenInvalidError):
                pass
