"""Rate limiting tests. fakeredis is injected via conftest override_redis fixture."""
import pytest
from httpx import AsyncClient

from src.core.config import settings

_USERNAME = "ratelimituser"
_EMAIL = "ratelimit@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"


async def _register(client: AsyncClient, username: str = _USERNAME, email: str = _EMAIL) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": _STRONG_PASSWORD},
    )


async def _login_attempt(
    client: AsyncClient,
    username_or_email: str = _USERNAME,
    password: str = _STRONG_PASSWORD,
    ip: str = "1.2.3.4",
) -> int:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password},
        headers={"X-Forwarded-For": ip},
    )
    return resp.status_code


async def test_login_rate_limit_per_ip(client: AsyncClient, monkeypatch) -> None:
    """11th login attempt from the same IP within 60s should get 429."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    await _register(client)

    for _ in range(10):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": "10.0.0.1"},
    )
    assert resp.status_code == 429


async def test_register_rate_limit_strict(client: AsyncClient, monkeypatch) -> None:
    """6th register attempt within 10 minutes from the same IP → 429."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    for i in range(5):
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": f"user{i}reg",
                "email": f"user{i}reg@example.com",
                "password": _STRONG_PASSWORD,
            },
            headers={"X-Forwarded-For": "10.0.0.2"},
        )

    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "user5reg",
            "email": "user5reg@example.com",
            "password": _STRONG_PASSWORD,
        },
        headers={"X-Forwarded-For": "10.0.0.2"},
    )
    assert resp.status_code == 429


async def test_refresh_rate_limit(client: AsyncClient, monkeypatch) -> None:
    """31st refresh attempt from the same IP within 60s → 429."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    await _register(client)

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": "10.0.0.3"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    for _ in range(30):
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            headers={"X-Forwarded-For": "10.0.0.3"},
        )

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"X-Forwarded-For": "10.0.0.3"},
    )
    assert resp.status_code == 429


async def test_rate_limit_per_ip_isolated(client: AsyncClient, monkeypatch) -> None:
    """IP A hitting rate limit must not block IP B."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    await _register(client)

    for _ in range(10):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
            headers={"X-Forwarded-For": "10.0.1.1"},
        )
    # IP A is now at limit — next request should be 429
    resp_a = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": "10.0.1.1"},
    )
    assert resp_a.status_code == 429

    # IP B should still work fine
    resp_b = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": "10.0.1.2"},
    )
    assert resp_b.status_code == 200


async def test_rate_limit_returns_retry_after_header(client: AsyncClient, monkeypatch) -> None:
    """429 response must include a Retry-After header."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    await _register(client)

    for _ in range(10):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
            headers={"X-Forwarded-For": "10.0.2.1"},
        )

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"X-Forwarded-For": "10.0.2.1"},
    )
    assert resp.status_code == 429
    assert "retry-after" in resp.headers


async def test_rate_limit_disabled_setting(client: AsyncClient, monkeypatch) -> None:
    """With RATE_LIMIT_ENABLED=False, many requests must not be blocked."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    await _register(client)

    for _ in range(20):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
            headers={"X-Forwarded-For": "10.0.3.1"},
        )
        assert resp.status_code == 200
