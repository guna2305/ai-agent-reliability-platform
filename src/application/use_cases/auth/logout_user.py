from __future__ import annotations

from src.infrastructure.cache.redis_client import get_redis, blacklist_token
from src.infrastructure.security.jwt_service import decode_token, TokenExpiredError, TokenInvalidError
from src.infrastructure.config.settings import get_settings


class LogoutUseCase:
    async def execute(self, access_token: str, refresh_token: str | None = None) -> None:
        settings = get_settings()
        redis = get_redis()

        try:
            payload = decode_token(access_token)
            remaining = int((payload.exp - __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            )).total_seconds())
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
