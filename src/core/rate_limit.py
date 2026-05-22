from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from src.core.config import settings
from src.core.redis_client import get_redis


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )


async def check_rate_limit(
    redis: Redis,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    """Sliding window log algorithm using a sorted set.
    Raises RateLimitExceeded if request count in window exceeds limit.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    window_start_ms = now_ms - (window_seconds * 1000)

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start_ms)
    pipe.zcard(key)
    pipe.zadd(key, {f"{now_ms}-{id(object())}": now_ms})
    pipe.expire(key, window_seconds + 10)

    results = await pipe.execute()
    current_count = results[1]

    if current_count >= limit:
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = max(1, int((oldest[0][1] + window_seconds * 1000 - now_ms) / 1000))
        else:
            retry_after = window_seconds
        raise RateLimitExceeded(retry_after=retry_after)


def _get_client_ip(request: Request) -> str:
    from src.core.http import get_client_ip
    return get_client_ip(request) or "unknown"


def rate_limit(limit: int, window_seconds: int, key_prefix: str = "ratelimit"):
    """FastAPI dependency factory for IP-based rate limiting.

    Usage:
        @router.post("/login", dependencies=[Depends(rate_limit(10, 60, "auth:login:ip"))])
    """
    async def dependency(request: Request) -> None:
        redis = await get_redis()
        ip = _get_client_ip(request)
        key = f"{key_prefix}:{ip}"
        await check_rate_limit(redis, key, limit, window_seconds)

    return dependency
