from datetime import datetime, timezone

from fastapi import HTTPException, status
from redis.asyncio import Redis

_USERNAME_THRESHOLDS = [
    (5, 15 * 60),        # 5 fails  → 15 min
    (10, 60 * 60),       # 10 fails → 1 hour
    (20, 24 * 60 * 60),  # 20 fails → 24 hours
]

_IP_THRESHOLDS = [
    (20, 60 * 60),        # 20 fails  → 1 hour
    (100, 24 * 60 * 60),  # 100 fails → 24 hours
]

_GENERIC_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
)


class LockoutService:
    @staticmethod
    async def check_locked(
        redis: Redis,
        username_or_email: str,
        ip: str,
    ) -> None:
        """Called BEFORE password verification. Raises generic 401 if locked.
        Uses identical error message as credential failure to prevent state disclosure.
        """
        now_ts = datetime.now(timezone.utc).timestamp()
        for key_type, identifier in [
            ("username", username_or_email.lower()),
            ("ip", ip),
        ]:
            until_key = f"lockout:{key_type}:{identifier}:until"
            until = await redis.get(until_key)
            if until and float(until) > now_ts:
                raise _GENERIC_401

    @staticmethod
    async def record_failure(
        redis: Redis,
        username_or_email: str,
        ip: str,
    ) -> None:
        """Called after a failed login attempt. Applies lockout when thresholds hit."""
        username = username_or_email.lower()

        username_count_key = f"lockout:username:{username}:count"
        username_count = await redis.incr(username_count_key)
        await redis.expire(username_count_key, 24 * 60 * 60)

        for threshold, lockout_seconds in _USERNAME_THRESHOLDS:
            if username_count == threshold:
                until = datetime.now(timezone.utc).timestamp() + lockout_seconds
                await redis.setex(
                    f"lockout:username:{username}:until",
                    lockout_seconds,
                    str(until),
                )

        ip_count_key = f"lockout:ip:{ip}:count"
        ip_count = await redis.incr(ip_count_key)
        await redis.expire(ip_count_key, 24 * 60 * 60)

        for threshold, lockout_seconds in _IP_THRESHOLDS:
            if ip_count == threshold:
                until = datetime.now(timezone.utc).timestamp() + lockout_seconds
                await redis.setex(
                    f"lockout:ip:{ip}:until",
                    lockout_seconds,
                    str(until),
                )

    @staticmethod
    async def reset_username(redis: Redis, username_or_email: str) -> None:
        """Called after a successful login. Clears the failure counter.
        The :until key is intentionally left intact — if an active lockout exists,
        check_locked would have rejected us before we ever reached this point.
        """
        username = username_or_email.lower()
        await redis.delete(f"lockout:username:{username}:count")

    @staticmethod
    async def admin_clear_lockout(
        redis: Redis,
        username_or_email: str | None = None,
        ip: str | None = None,
    ) -> None:
        """Admin-only: manually clear lockout state for a username or IP."""
        if username_or_email:
            username = username_or_email.lower()
            await redis.delete(
                f"lockout:username:{username}:count",
                f"lockout:username:{username}:until",
            )
        if ip:
            await redis.delete(
                f"lockout:ip:{ip}:count",
                f"lockout:ip:{ip}:until",
            )
