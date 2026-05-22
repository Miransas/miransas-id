import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

import src.models  # noqa: F401 — register all SQLModel table classes
from src.core.config import settings
from src.database.session import get_db
from src.main import create_app


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch):
    """Disable rate limiting in all tests so existing tests don't hit 429."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)


@pytest.fixture(autouse=True)
def capture_emails():
    """Replace email backend with CapturingBackend for every test."""
    from src.services.email_service import (
        CapturingBackend,
        clear_captured_emails,
        override_email_backend,
        reset_email_backend,
    )
    clear_captured_emails()
    override_email_backend(CapturingBackend())
    yield
    reset_email_backend()
    clear_captured_emails()


@pytest.fixture
def captured_emails():
    """Returns a callable that gives the current list of captured emails."""
    from src.services.email_service import get_captured_emails
    return get_captured_emails


@pytest.fixture
async def fake_redis():
    """In-memory Redis for tests using fakeredis."""
    from fakeredis import aioredis as fake_aioredis
    redis = fake_aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.fixture(autouse=True)
async def override_redis(fake_redis, monkeypatch):
    """Inject fakeredis into the module-level singleton so every get_redis() call
    returns it without needing a real Redis server."""
    from src.core import redis_client
    # Patch the private singleton — get_redis() returns it directly when non-None.
    monkeypatch.setattr(redis_client, "_redis", fake_redis)


@pytest.fixture
async def _engine():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(_engine, fake_redis):
    app = create_app(init_database=False)
    _factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with _factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
async def db(_engine):
    """Direct async DB session sharing the same in-memory SQLite as the test client."""
    _factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _factory() as session:
        yield session
