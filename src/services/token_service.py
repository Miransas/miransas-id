import json
import secrets

from redis.asyncio import Redis

from src.core.security import hash_token


class TokenService:
    """Short-lived single-use token service for email verification and password reset.
    Tokens are stored as SHA-256 hashes in Redis. The plain token only appears in emails.
    """

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    async def store_token(
        redis: Redis,
        token_type: str,
        token: str,
        payload: dict,
        ttl_seconds: int,
    ) -> None:
        key = f"{token_type}:{hash_token(token)}"
        await redis.setex(key, ttl_seconds, json.dumps(payload))

    @staticmethod
    async def consume_token(
        redis: Redis,
        token_type: str,
        token: str,
    ) -> dict | None:
        """Atomically retrieve and delete. Single-use: a token can only be consumed once."""
        key = f"{token_type}:{hash_token(token)}"
        pipe = redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        results = await pipe.execute()
        raw = results[0]
        if not raw:
            return None
        return json.loads(raw)

    @staticmethod
    async def revoke_all_user_tokens(
        redis: Redis,
        token_type: str,
        user_id: int,
    ) -> int:
        """Revoke all outstanding tokens of a given type for a user.
        O(N) scan — acceptable for low-frequency operations like password reset.
        """
        pattern = f"{token_type}:*"
        revoked = 0
        async for key in redis.scan_iter(match=pattern, count=100):
            raw = await redis.get(key)
            if raw:
                try:
                    payload = json.loads(raw)
                    if payload.get("user_id") == user_id:
                        await redis.delete(key)
                        revoked += 1
                except (json.JSONDecodeError, AttributeError):
                    pass
        return revoked
