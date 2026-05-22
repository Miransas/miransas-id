"""Admin lockout management tests."""
import json
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.constants import AuditAction
from src.core.security import get_password_hash
from src.models.audit_log import AuditLog
from src.models.login_attempt import LoginAttempt
from src.models.user import MiransasRank, User

_STRONG_PASSWORD = "Str0ng!Pass#99"
_CD_PASSWORD = "CoreDev!Pass#99"
_WRONG_PASSWORD = "Wr0ng!Pass#00"


@pytest.fixture
async def core_dev(db: AsyncSession) -> User:
    user = User(
        username="coredevlk",
        email="coredevlk@test.com",
        hashed_password=get_password_hash(_CD_PASSWORD),
        rank=MiransasRank.CORE_DEVELOPER,
        badges=[],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def core_dev_headers(core_dev: User, client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "coredevlk", "password": _CD_PASSWORD},
    )
    assert resp.status_code == 200, resp.json()
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def regular_user(db: AsyncSession) -> User:
    user = User(
        username="regularlk",
        email="regularlk@test.com",
        hashed_password=get_password_hash(_STRONG_PASSWORD),
        rank=MiransasRank.NOVICE,
        badges=[],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_admin_clear_username_lockout(
    client: AsyncClient, core_dev: User, core_dev_headers: dict, fake_redis
) -> None:
    """Admin can clear a username lockout so the user can login again."""
    # Manually set lockout
    username = "regularlk"
    until = datetime.now(timezone.utc).timestamp() + 3600
    await fake_redis.setex(f"lockout:username:{username}:until", 3600, str(until))
    await fake_redis.set(f"lockout:username:{username}:count", "5")

    # Direct login blocked
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": _WRONG_PASSWORD},
        headers={"X-Forwarded-For": "9.9.9.1"},
    )
    assert resp.status_code == 401

    # Admin clears lockout
    resp = await client.post(
        "/api/v1/admin/lockouts/clear",
        json={"username_or_email": username},
        headers=core_dev_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cleared"

    # User can now authenticate (key gone)
    until_val = await fake_redis.get(f"lockout:username:{username}:until")
    assert until_val is None


async def test_admin_clear_ip_lockout(
    client: AsyncClient, core_dev: User, core_dev_headers: dict, fake_redis
) -> None:
    """Admin can clear an IP-based lockout."""
    ip = "9.9.9.2"
    until = datetime.now(timezone.utc).timestamp() + 3600
    await fake_redis.setex(f"lockout:ip:{ip}:until", 3600, str(until))

    resp = await client.post(
        "/api/v1/admin/lockouts/clear",
        json={"ip": ip},
        headers=core_dev_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cleared"

    until_val = await fake_redis.get(f"lockout:ip:{ip}:until")
    assert until_val is None


async def test_admin_clear_lockout_requires_core_developer(
    client: AsyncClient, regular_user: User
) -> None:
    """Non-core-developer users must not clear lockouts."""
    resp_login = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "regularlk", "password": _STRONG_PASSWORD},
    )
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/admin/lockouts/clear",
        json={"username_or_email": "someone"},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_admin_clear_lockout_creates_audit_entry(
    client: AsyncClient,
    db: AsyncSession,
    core_dev: User,
    core_dev_headers: dict,
    fake_redis,
) -> None:
    """Clearing a lockout must create an audit log entry."""
    resp = await client.post(
        "/api/v1/admin/lockouts/clear",
        json={"username_or_email": "someuser"},
        headers=core_dev_headers,
    )
    assert resp.status_code == 200

    result = await db.execute(
        select(AuditLog).where(AuditLog.action == AuditAction.LOCKOUT_CLEARED)
    )
    entry = result.scalars().first()
    assert entry is not None
    assert entry.actor_id == core_dev.id
    detail = json.loads(entry.detail)
    assert detail["username_or_email"] == "someuser"


async def test_admin_clear_lockout_missing_fields(
    client: AsyncClient, core_dev: User, core_dev_headers: dict
) -> None:
    """Request without username_or_email or ip must return 400."""
    resp = await client.post(
        "/api/v1/admin/lockouts/clear",
        json={},
        headers=core_dev_headers,
    )
    assert resp.status_code == 400


async def test_admin_list_login_attempts_filters(
    client: AsyncClient,
    db: AsyncSession,
    core_dev: User,
    core_dev_headers: dict,
) -> None:
    """Login attempts endpoint supports filtering by success flag."""
    # Insert some attempts directly
    db.add(LoginAttempt(
        username_or_email="testfilter",
        ip_address="1.2.3.4",
        success=False,
        failure_reason="invalid_credentials",
    ))
    db.add(LoginAttempt(
        username_or_email="testfilter",
        ip_address="1.2.3.4",
        success=True,
    ))
    await db.commit()

    resp = await client.get(
        "/api/v1/admin/login-attempts?username=testfilter&success=false",
        headers=core_dev_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(not a["success"] for a in data)
    assert len(data) == 1

    resp2 = await client.get(
        "/api/v1/admin/login-attempts?username=testfilter&success=true",
        headers=core_dev_headers,
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert all(a["success"] for a in data2)
    assert len(data2) == 1
