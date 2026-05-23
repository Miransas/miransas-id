"""Tests for create_app lifespan behaviour — specifically that create_all is only
called in development/test environments and is skipped in production.

Note: httpx ASGITransport (httpx 0.28+) does not trigger the ASGI lifespan.
We invoke app.router.lifespan_context(app) directly instead.
"""
from unittest.mock import patch

import pytest
from sqlmodel import SQLModel

from src.core.config import settings
from src.main import create_app


async def test_lifespan_skips_create_all_in_production(monkeypatch) -> None:
    """Production must never run create_all — Alembic owns schema in prod."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "a-secure-production-secret-for-tests-xyz-123")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://miransas.com"])

    with patch.object(SQLModel.metadata, "create_all") as mock_ca:
        app = create_app(init_database=True)
        async with app.router.lifespan_context(app):
            pass

    mock_ca.assert_not_called()


async def test_lifespan_runs_create_all_in_development(monkeypatch) -> None:
    """Development must run create_all on startup."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    with patch.object(SQLModel.metadata, "create_all") as mock_ca:
        app = create_app(init_database=True)
        async with app.router.lifespan_context(app):
            pass

    mock_ca.assert_called_once()
