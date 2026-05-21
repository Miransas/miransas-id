import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

import src.models  # noqa: F401 — register User and UserSession tables
from src.database.session import get_db
from src.main import create_app


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
async def client(_engine):
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
