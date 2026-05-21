from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.config import settings
from src.core.constants import SessionRevocationReason
from src.models.session import UserSession

_USERNAME = "charlie"
_EMAIL = "charlie@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"


async def _register(
    client: AsyncClient,
    username: str = _USERNAME,
    email: str = _EMAIL,
    password: str = _STRONG_PASSWORD,
) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert resp.status_code == 201, resp.json()


async def _login(
    client: AsyncClient,
    username_or_email: str = _USERNAME,
    password: str = _STRONG_PASSWORD,
) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password},
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Refresh rotation ───────────────────────────────────────────────────────────

async def test_refresh_returns_new_token_pair(client: AsyncClient) -> None:
    await _register(client)
    data = await _login(client)
    refresh_1 = data["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    body = resp.json()

    assert resp.status_code == 200
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["refresh_token"] != refresh_1


async def test_refresh_invalidates_old_refresh_token(client: AsyncClient) -> None:
    await _register(client)
    data = await _login(client)
    refresh_1 = data["refresh_token"]

    rotate_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert rotate_resp.status_code == 200

    # Old token must be rejected
    reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert reuse_resp.status_code == 401


async def test_refresh_with_access_token_rejected(client: AsyncClient) -> None:
    await _register(client)
    data = await _login(client)
    access_token = data["access_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


async def test_refresh_with_tampered_token_rejected(client: AsyncClient) -> None:
    await _register(client)
    data = await _login(client)
    refresh_token = data["refresh_token"]

    parts = refresh_token.split(".")
    parts[1] = parts[1][:-4] + "XXXX"
    tampered = ".".join(parts)

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tampered})
    assert resp.status_code == 401


async def test_refresh_with_expired_token_rejected(client: AsyncClient) -> None:
    now = datetime.now(timezone.utc)
    expired_token = jose_jwt.encode(
        {
            "sub": "1",
            "iat": now - timedelta(hours=10),
            "nbf": now - timedelta(hours=10),
            "exp": now - timedelta(hours=9),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "refresh",
            "jti": "fakejti00000000000000000000000000",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": expired_token})
    assert resp.status_code == 401


# ── Reuse detection ────────────────────────────────────────────────────────────

async def test_reused_refresh_token_invalidates_family(
    client: AsyncClient, db: AsyncSession
) -> None:
    await _register(client)
    data = await _login(client)
    refresh_1 = data["refresh_token"]

    # Rotate: refresh_1 → refresh_2
    rotate_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert rotate_resp.status_code == 200
    refresh_2 = rotate_resp.json()["refresh_token"]

    # Reuse: present the already-rotated refresh_1 → triggers family invalidation
    reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert reuse_resp.status_code == 401

    # refresh_2 must also be dead (same family was invalidated)
    family_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_2})
    assert family_resp.status_code == 401

    # Verify DB: all sessions have reuse_detected reason
    result = await db.execute(select(UserSession))
    sessions = list(result.scalars().all())

    reuse_sessions = [s for s in sessions if s.revocation_reason == SessionRevocationReason.REUSE_DETECTED]
    assert len(reuse_sessions) > 0, "Expected at least one session with reuse_detected reason"

    # No session in this family should be active
    active = [s for s in sessions if s.is_active]
    assert len(active) == 0, "All sessions should be inactive after reuse attack"


async def test_reuse_detection_does_not_affect_other_users(client: AsyncClient) -> None:
    # Register two separate users
    await _register(client, username="charlie", email="charlie@example.com")
    await _register(
        client,
        username="devuser",
        email="devuser@example.com",
        password="Str0ng!Pass#99",
    )

    data_a = await _login(client, username_or_email="charlie")
    data_b = await _login(client, username_or_email="devuser")

    refresh_a1 = data_a["refresh_token"]
    refresh_b = data_b["refresh_token"]

    # Rotate A's token
    rot = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a1})
    assert rot.status_code == 200

    # Trigger reuse on A's family
    await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a1})

    # B's refresh token must still be valid
    resp_b = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b})
    assert resp_b.status_code == 200


# ── Logout ─────────────────────────────────────────────────────────────────────

async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    await _register(client)
    data = await _login(client)
    refresh_token = data["refresh_token"]

    logout_resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 204

    refresh_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401


async def test_logout_is_idempotent(client: AsyncClient) -> None:
    # Completely unknown / invalid token → still 204
    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "this.is.not.a.valid.token"},
    )
    assert resp.status_code == 204


async def test_logout_all_revokes_all_sessions(client: AsyncClient) -> None:
    await _register(client)

    # Create 3 separate sessions
    sessions_data = [await _login(client) for _ in range(3)]
    refresh_tokens = [d["refresh_token"] for d in sessions_data]
    access_token = sessions_data[0]["access_token"]

    # logout-all (uses access token, NOT refresh)
    resp = await client.post(
        "/api/v1/auth/logout-all",
        headers=_auth_headers(access_token),
    )
    assert resp.status_code == 204

    # Every refresh token must be dead
    for rt in refresh_tokens:
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 401


async def test_logout_all_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/logout-all")
    assert resp.status_code == 401


async def test_logout_all_does_not_affect_other_users(client: AsyncClient) -> None:
    await _register(client, username="charlie", email="charlie@example.com")
    await _register(
        client,
        username="devuser",
        email="devuser@example.com",
        password="Str0ng!Pass#99",
    )

    data_a = await _login(client, username_or_email="charlie")
    data_b = await _login(client, username_or_email="devuser")

    # A logs out of all devices
    await client.post(
        "/api/v1/auth/logout-all",
        headers=_auth_headers(data_a["access_token"]),
    )

    # B's refresh token must still work
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": data_b["refresh_token"]},
    )
    assert resp.status_code == 200


# ── Sessions list ──────────────────────────────────────────────────────────────

async def test_list_sessions_returns_own_sessions(client: AsyncClient) -> None:
    await _register(client)

    data_1 = await _login(client)
    data_2 = await _login(client)

    resp = await client.get(
        "/api/v1/auth/sessions",
        headers=_auth_headers(data_1["access_token"]),
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_sessions_excludes_revoked(client: AsyncClient) -> None:
    await _register(client)

    data_1 = await _login(client)
    data_2 = await _login(client)

    # Revoke session 1
    await client.post("/api/v1/auth/logout", json={"refresh_token": data_1["refresh_token"]})

    # Using session 2's access token — should see only 1 active session
    resp = await client.get(
        "/api/v1/auth/sessions",
        headers=_auth_headers(data_2["access_token"]),
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_sessions_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/sessions")
    assert resp.status_code == 401


# ── Session metadata ───────────────────────────────────────────────────────────

async def test_session_records_user_agent(client: AsyncClient) -> None:
    await _register(client)

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
        headers={"User-Agent": "TestBrowser/1.0"},
    )
    access_token = login_resp.json()["access_token"]

    sessions_resp = await client.get(
        "/api/v1/auth/sessions",
        headers=_auth_headers(access_token),
    )
    assert sessions_resp.status_code == 200
    assert sessions_resp.json()[0]["user_agent"] == "TestBrowser/1.0"
