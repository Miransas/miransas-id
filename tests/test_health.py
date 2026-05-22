import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from unittest.mock import AsyncMock

from src.core.config import Settings
from src.core.observability import scrub_sensitive_data
from src.database.session import get_db


async def test_health_returns_200(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_health_detailed_returns_200_when_all_ok(client):
    r = await client.get("/api/v1/health/detailed")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "ok"


async def test_health_detailed_returns_503_when_db_unavailable(fake_redis):
    from src.core import redis_client
    from src.main import create_app

    app = create_app(init_database=False)

    async def broken_db():
        mock = AsyncMock()
        mock.execute.side_effect = Exception("DB unavailable")
        yield mock

    app.dependency_overrides[get_db] = broken_db

    original = redis_client._redis
    redis_client._redis = fake_redis
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/api/v1/health/detailed")
    finally:
        redis_client._redis = original
        app.dependency_overrides.clear()

    assert r.status_code == 503
    data = r.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"]["status"] == "error"


def test_sensitive_fields_are_scrubbed_from_sentry():
    event = {
        "request": {
            "data": {
                "username": "alice",
                "password": "s3cr3t",
                "new_password": "n3ws3cr3t",
            },
            "headers": {
                "authorization": "Bearer tok123",
                "content-type": "application/json",
            },
        }
    }
    scrubbed = scrub_sensitive_data(event, None)
    req = scrubbed["request"]
    assert req["data"]["password"] == "[REDACTED]"
    assert req["data"]["new_password"] == "[REDACTED]"
    assert req["data"]["username"] == "alice"
    assert req["headers"]["authorization"] == "[REDACTED]"
    assert req["headers"]["content-type"] == "application/json"


def test_default_secret_key_rejected_in_production():
    with pytest.raises(ValidationError, match="SECRET_KEY must not be the default"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="change_me_in_production_environment",
            CORS_ORIGINS=["https://app.miransas.com"],
            RESEND_API_KEY="re_abc123",
            EMAIL_FROM="noreply@miransas.com",
            APP_FRONTEND_URL="https://console.miransas.com",
        )


def test_wildcard_cors_rejected_in_production():
    with pytest.raises(ValidationError, match="CORS_ORIGINS must not contain"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6ab",
            CORS_ORIGINS=["*"],
            RESEND_API_KEY="re_abc123",
            EMAIL_FROM="noreply@miransas.com",
            APP_FRONTEND_URL="https://console.miransas.com",
        )
