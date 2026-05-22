import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.constants import AuditAction
from src.core.security import get_password_hash
from src.models.audit_log import AuditLog
from src.models.user import MiransasRank, User

_STRONG_PASSWORD = "Str0ng!Pass#99"
_CD_PASSWORD = "CoreDev!Pass#99"


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
async def core_dev(db: AsyncSession) -> User:
    """A Core Developer user created directly in the DB."""
    user = User(
        username="coredev",
        email="coredev@test.com",
        hashed_password=get_password_hash(_CD_PASSWORD),
        rank=MiransasRank.CORE_DEVELOPER,
        badges=[],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def core_dev_token(core_dev: User, client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "coredev", "password": _CD_PASSWORD},
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


@pytest.fixture
async def core_dev_headers(core_dev_token: str) -> dict:
    return {"Authorization": f"Bearer {core_dev_token}"}


@pytest.fixture
async def regular_user(db: AsyncSession) -> User:
    """A Novice user created directly in the DB."""
    user = User(
        username="regular",
        email="regular@test.com",
        hashed_password=get_password_hash(_STRONG_PASSWORD),
        rank=MiransasRank.NOVICE,
        badges=[],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ── Access control ─────────────────────────────────────────────────────────────

async def test_admin_users_requires_core_developer(client: AsyncClient, regular_user: User) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "regular", "password": _STRONG_PASSWORD},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


async def test_admin_users_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code == 401


async def test_admin_audit_log_requires_core_developer(
    client: AsyncClient, regular_user: User
) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "regular", "password": _STRONG_PASSWORD},
    )
    token = resp.json()["access_token"]
    resp = await client.get(
        "/api/v1/admin/audit-log", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


# ── Admin user listing ─────────────────────────────────────────────────────────

async def test_admin_list_users_returns_all_users(
    client: AsyncClient,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    resp = await client.get("/api/v1/admin/users", headers=core_dev_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_admin_list_users_includes_full_profile(
    client: AsyncClient, core_dev: User, core_dev_headers: dict
) -> None:
    resp = await client.get("/api/v1/admin/users", headers=core_dev_headers)
    body = resp.json()
    assert len(body) == 1
    user = body[0]
    assert "email" in user
    assert "is_active" in user
    assert "created_at" in user


# ── Admin update ───────────────────────────────────────────────────────────────

async def test_admin_update_user_rank(
    client: AsyncClient,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    resp = await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"rank": "Architect"},
    )
    assert resp.status_code == 200
    assert resp.json()["rank"] == "Architect"


async def test_admin_update_user_badges(
    client: AsyncClient,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    resp = await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"badges": ["founder", "beta_tester"]},
    )
    assert resp.status_code == 200
    assert set(resp.json()["badges"]) == {"founder", "beta_tester"}


async def test_admin_self_modification_blocked(
    client: AsyncClient, core_dev: User, core_dev_headers: dict
) -> None:
    resp = await client.patch(
        f"/api/v1/admin/users/{core_dev.id}",
        headers=core_dev_headers,
        json={"rank": "Novice"},
    )
    assert resp.status_code == 403


async def test_admin_disable_user_revokes_sessions(
    client: AsyncClient,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    # Regular user logs in (creates a session)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "regular", "password": _STRONG_PASSWORD},
    )
    regular_refresh = login_resp.json()["refresh_token"]
    regular_access = login_resp.json()["access_token"]

    # Confirm /me works before disable
    me_before = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {regular_access}"}
    )
    assert me_before.status_code == 200

    # Admin disables the user
    resp = await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # /me must fail (is_active=False checked against DB)
    me_after = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {regular_access}"}
    )
    assert me_after.status_code == 401

    # Refresh must fail (session revoked)
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": regular_refresh}
    )
    assert refresh_resp.status_code == 401


async def test_admin_enable_user(
    client: AsyncClient,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    # Disable first
    await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"is_active": False},
    )
    # Then re-enable
    resp = await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"is_active": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


# ── Core Developer invariant ───────────────────────────────────────────────────

async def test_admin_cannot_disable_last_core_developer(
    db: AsyncSession, core_dev: User
) -> None:
    """Service-level test: demoting core_dev would leave 0 active Core Devs → 400."""
    from fastapi import HTTPException
    from src.schemas.user import AdminUserUpdate
    from src.services.admin_service import AdminService

    # Create a second user to act as the admin (different from core_dev)
    actor = User(
        username="actor2",
        email="actor2@test.com",
        hashed_password=get_password_hash(_STRONG_PASSWORD),
        rank=MiransasRank.CORE_DEVELOPER,
        badges=[],
    )
    db.add(actor)
    await db.commit()
    await db.refresh(actor)

    # Demote actor in DB so count(CoreDev excluding core_dev) = 0
    from sqlalchemy import update as sa_update
    await db.execute(
        sa_update(User).where(User.id == actor.id).values(rank=MiransasRank.NOVICE)
    )
    await db.commit()

    # Now only core_dev is a CoreDev; trying to disable them should fail
    with pytest.raises(HTTPException) as exc_info:
        await AdminService.update_user(
            db, actor, core_dev.id, AdminUserUpdate(is_active=False), None
        )
    assert exc_info.value.status_code == 400


async def test_admin_cannot_demote_last_core_developer(
    db: AsyncSession, core_dev: User
) -> None:
    """Service-level test: disabling core_dev when they are the last → 400."""
    from fastapi import HTTPException
    from src.schemas.user import AdminUserUpdate
    from src.services.admin_service import AdminService

    actor = User(
        username="actor3",
        email="actor3@test.com",
        hashed_password=get_password_hash(_STRONG_PASSWORD),
        rank=MiransasRank.NOVICE,
        badges=[],
    )
    db.add(actor)
    await db.commit()
    await db.refresh(actor)

    with pytest.raises(HTTPException) as exc_info:
        await AdminService.update_user(
            db, actor, core_dev.id, AdminUserUpdate(rank=MiransasRank.NOVICE), None
        )
    assert exc_info.value.status_code == 400


# ── Audit log ──────────────────────────────────────────────────────────────────

async def test_audit_log_records_rank_change(
    client: AsyncClient,
    db: AsyncSession,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"rank": "Architect"},
    )

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.target_user_id == regular_user.id,
            AuditLog.action == AuditAction.RANK_CHANGED,
        )
    )
    entry = result.scalars().first()
    assert entry is not None
    assert entry.actor_id == core_dev.id


async def test_audit_log_records_disable(
    client: AsyncClient,
    db: AsyncSession,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"is_active": False},
    )

    result = await db.execute(
        select(AuditLog).where(
            AuditLog.target_user_id == regular_user.id,
            AuditLog.action == AuditAction.USER_DISABLED,
        )
    )
    entry = result.scalars().first()
    assert entry is not None


async def test_audit_log_api_returns_entries(
    client: AsyncClient,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"rank": "Elite"},
    )
    await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"badges": ["founder"]},
    )

    resp = await client.get("/api/v1/admin/audit-log", headers=core_dev_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_audit_log_does_not_record_no_op(
    client: AsyncClient,
    db: AsyncSession,
    core_dev: User,
    regular_user: User,
    core_dev_headers: dict,
) -> None:
    # Sending the SAME rank that the user already has → no audit entry
    await client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        headers=core_dev_headers,
        json={"rank": "Novice"},  # regular_user is already Novice
    )
    result = await db.execute(select(AuditLog))
    entries = result.scalars().all()
    assert len(entries) == 0


# ── Atomicity ──────────────────────────────────────────────────────────────────

async def test_admin_disable_atomicity(
    db: AsyncSession, core_dev: User, regular_user: User
) -> None:
    """Session revoke and field update must be part of the same transaction.

    We verify this by calling revoke_all_user_sessions(auto_commit=False) and
    then rolling back explicitly. Both the session status and the user field
    must revert — confirming they were never committed as separate operations.
    """
    from sqlalchemy import select as sa_select

    from src.models.session import UserSession
    from src.services.session_service import SessionService

    # Capture IDs before any transaction manipulation to avoid lazy-load after rollback.
    user_id = regular_user.id

    _, session = await SessionService.create_session(
        db, regular_user, user_agent="test", ip_address="1.1.1.1"
    )
    session_id = session.id
    assert session.is_active is True

    # Revoke without committing — simulates being inside a larger transaction.
    await SessionService.revoke_all_user_sessions(db, user_id, auto_commit=False)

    # Mutate user field (also not committed).
    await db.execute(
        sa_select(User).where(User.id == user_id)  # ensure object is in session
    )
    from sqlalchemy import update as sa_update
    await db.execute(sa_update(User).where(User.id == user_id).values(is_active=False))

    # Roll back the whole transaction — neither change should persist.
    await db.rollback()

    result = await db.execute(sa_select(User).where(User.id == user_id))
    refreshed_user = result.scalars().first()
    assert refreshed_user is not None
    assert refreshed_user.is_active is True, "is_active must have reverted after rollback"

    result = await db.execute(sa_select(UserSession).where(UserSession.id == session_id))
    refreshed_session = result.scalars().first()
    assert refreshed_session is not None
    assert refreshed_session.is_active is True, "session revoke must have reverted after rollback"
