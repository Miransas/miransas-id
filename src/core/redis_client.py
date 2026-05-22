from redis.asyncio import Redis

from src.core.config import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    """FastAPI dependency. Async Redis client. Connection pooled."""
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
