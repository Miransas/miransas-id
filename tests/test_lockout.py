"""Brute-force lockout tests. Uses fakeredis via conftest override_redis."""
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.security import get_password_hash
from src.models.login_attempt import LoginAttempt
from src.models.user import User

_USERNAME = "lockoutuser"
_EMAIL = "lockout@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"
_WRONG_PASSWORD = "Wr0ng!Pass#00"
_IP = "5.5.5.5"


async def _register(client: AsyncClient, username: str = _USERNAME, email: str = _EMAIL) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": _STRONG_PASSWORD},
    )
    assert resp.status_code == 201


async def _login(
    client: AsyncClient,
    password: str = _STRONG_PASSWORD,
    username: str = _USERNAME,
    ip: str = _IP,
) -> int:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": password},
        headers={"X-Forwarded-For": ip},
    )
    return resp.status_code


async def test_5_failed_logins_locks_username_for_15min(
    client: AsyncClient, fake_redis
) -> None:
    """After 5 bad passwords, correct password also returns 401."""
    await _register(client)

    for _ in range(5):
        assert await _login(client, password=_WRONG_PASSWORD) == 401

    # Correct password still blocked — lockout active
    assert await _login(client, password=_STRONG_PASSWORD) == 401


async def test_lockout_resets_after_window(client: AsyncClient, fake_redis) -> None:
    """After lockout expires (simulated by deleting Redis key), login works again."""
    await _register(client)

    for _ in range(5):
        await _login(client, password=_WRONG_PASSWORD)

    # Simulate lockout expiry by deleting the until key
    await fake_redis.delete(f"lockout:username:{_USERNAME}:until")

    assert await _login(client, password=_STRONG_PASSWORD) == 200


async def test_successful_login_resets_counter(client: AsyncClient, fake_redis) -> None:
    """4 fails then 1 success resets the counter; next 4 fails don't lock."""
    await _register(client)

    for _ in range(4):
        await _login(client, password=_WRONG_PASSWORD)

    assert await _login(client, password=_STRONG_PASSWORD) == 200

    # Counter was reset; 4 more failures should not trigger lockout (threshold is 5)
    for _ in range(4):
        await _login(client, password=_WRONG_PASSWORD)

    assert await _login(client, password=_STRONG_PASSWORD) == 200


async def test_lockout_message_is_generic(client: AsyncClient, fake_redis) -> None:
    """Lockout response must say 'Invalid credentials', not 'locked' or 'blocked'."""
    await _register(client)

    for _ in range(5):
        await _login(client, password=_WRONG_PASSWORD)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": _IP},
    )
    assert resp.status_code == 401
    detail = resp.json()["detail"].lower()
    assert "lock" not in detail
    assert "block" not in detail
    assert detail == "invalid credentials"


async def test_ip_lockout_after_20_failures(client: AsyncClient, fake_redis) -> None:
    """20 failed logins from one IP (different users) trigger IP lockout."""
    # Create 20 users so we can target different usernames
    for i in range(20):
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": f"ipvic{i}",
                "email": f"ipvic{i}@example.com",
                "password": _STRONG_PASSWORD,
            },
        )

    attack_ip = "6.6.6.6"
    for i in range(20):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": f"ipvic{i}", "password": _WRONG_PASSWORD},
            headers={"X-Forwarded-For": attack_ip},
        )

    # Now that IP should be locked
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "ipvic0", "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": attack_ip},
    )
    assert resp.status_code == 401


async def test_ip_lockout_blocks_all_logins_from_that_ip(
    client: AsyncClient, fake_redis
) -> None:
    """After IP lockout, even valid credentials from that IP are rejected."""
    await _register(client)

    attack_ip = "7.7.7.7"
    # Manually set IP lockout
    until = datetime.now(timezone.utc).timestamp() + 3600
    await fake_redis.setex(f"lockout:ip:{attack_ip}:until", 3600, str(until))

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": attack_ip},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


async def test_lockout_does_not_affect_other_users(
    client: AsyncClient, fake_redis
) -> None:
    """User A being locked out must not prevent User B from logging in."""
    await _register(client, username="usera", email="usera@example.com")
    await _register(client, username="userb", email="userb@example.com")

    # Lock user A
    for _ in range(5):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "usera", "password": _WRONG_PASSWORD},
            headers={"X-Forwarded-For": "8.8.8.1"},
        )

    # User B from a different IP should still work
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "userb", "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": "8.8.8.2"},
    )
    assert resp.status_code == 200


async def test_login_attempt_recorded_on_failure(
    client: AsyncClient, db: AsyncSession
) -> None:
    """A failed login must be persisted as a LoginAttempt with success=False."""
    await _register(client)
    await _login(client, password=_WRONG_PASSWORD)

    result = await db.execute(
        select(LoginAttempt).where(
            LoginAttempt.username_or_email == _USERNAME,
            LoginAttempt.success == False,  # noqa: E712
        )
    )
    attempt = result.scalars().first()
    assert attempt is not None
    assert attempt.failure_reason == "invalid_credentials"


async def test_login_attempt_recorded_on_success(
    client: AsyncClient, db: AsyncSession
) -> None:
    """A successful login must be persisted as a LoginAttempt with success=True."""
    await _register(client)
    await _login(client, password=_STRONG_PASSWORD)

    result = await db.execute(
        select(LoginAttempt).where(
            LoginAttempt.username_or_email == _USERNAME,
            LoginAttempt.success == True,  # noqa: E712
        )
    )
    attempt = result.scalars().first()
    assert attempt is not None
    assert attempt.failure_reason is None
