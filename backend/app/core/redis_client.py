"""Async Redis client — singleton pool managed in lifespan."""
from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


async def init_redis() -> None:
    """Call once at application startup."""
    global _redis
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    # Validate connectivity
    await _redis.ping()


async def close_redis() -> None:
    """Call once at application shutdown."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis:
    """Return the active Redis client. Raises RuntimeError if not initialised."""
    if _redis is None:
        raise RuntimeError(
            "Redis client is not initialised. "
            "Call init_redis() during application startup."
        )
    return _redis


# ─── Token blacklist helpers ───────────────────────────────────────────────────
BLACKLIST_PREFIX = "blacklist:token:"


async def blacklist_token(jti_or_token: str, ttl_seconds: int) -> None:
    """Store a token (or its jti) in the Redis blacklist until it expires."""
    redis = get_redis()
    key = f"{BLACKLIST_PREFIX}{jti_or_token}"
    await redis.set(key, "1", ex=ttl_seconds)


async def is_token_blacklisted(jti_or_token: str) -> bool:
    """Return True if the token is in the blacklist."""
    redis = get_redis()
    key = f"{BLACKLIST_PREFIX}{jti_or_token}"
    return await redis.exists(key) == 1
