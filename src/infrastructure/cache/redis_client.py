from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from src.infrastructure.config.settings import get_settings

_redis_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _redis_pool


async def cache_get(key: str) -> Any | None:
    redis = get_redis()
    value = await redis.get(key)
    if value is None:
        return None
    return json.loads(value)


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    settings = get_settings()
    redis = get_redis()
    ttl = ttl or settings.redis_cache_ttl
    await redis.setex(key, ttl, json.dumps(value, default=str))


async def cache_delete(key: str) -> None:
    redis = get_redis()
    await redis.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    redis = get_redis()
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


async def rate_limit_check(key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
    """Returns (is_allowed, current_count)."""
    redis = get_redis()
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    results = await pipe.execute()
    count: int = results[0]
    return count <= max_requests, count


async def blacklist_token(jti: str, expire_seconds: int) -> None:
    redis = get_redis()
    await redis.setex(f"jwt:blacklist:{jti}", expire_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    redis = get_redis()
    return bool(await redis.exists(f"jwt:blacklist:{jti}"))
