import time
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt as jose_jwt

from src.core.config import settings

# "miransas" is a reserved username; tests use a non-reserved account.
_USERNAME = "charlie"
_EMAIL = "charlie@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"


async def _register(
    client: AsyncClient,
    username: str = _USERNAME,
    email: str = _EMAIL,
    password: str = _STRONG_PASSWORD,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )


async def _login(
    client: AsyncClient,
    username_or_email: str = _USERNAME,
    password: str = _STRONG_PASSWORD,
) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password},
    )
    return resp.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_token(overrides: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "999",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=15),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "access",
    }
    payload.update(overrides)
    return jose_jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Core flow ─────────────────────────────────────────────────────────────────

async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_register_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": _USERNAME, "email": _EMAIL, "password": _STRONG_PASSWORD},
    )
    body = response.json()

    assert response.status_code == 201
    assert body["username"] == _USERNAME
    assert body["email"] == _EMAIL
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_returns_400_with_generic_message(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": _USERNAME, "email": _EMAIL, "password": _STRONG_PASSWORD},
    )
    body = response.json()

    assert response.status_code == 400
    # Must not reveal which field caused the conflict — prevents user enumeration.
    assert "email" not in body["detail"].lower()
    assert "username" not in body["detail"].lower()
    assert "already" not in body["detail"].lower()


async def test_login_returns_access_token(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]  # Bölüm 2 complete


async def test_auth_me_requires_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_auth_me_returns_current_user(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    response = await client.get("/api/v1/auth/me", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["username"] == _USERNAME


# ── Security: error message hygiene ───────────────────────────────────────────

async def test_login_wrong_password_returns_generic_error(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": "WrongP@ss#00"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_nonexistent_user_returns_same_error(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "nobody_here", "password": "WrongP@ss#00"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# ── Security: timing consistency ──────────────────────────────────────────────

async def test_login_timing_consistency(client: AsyncClient) -> None:
    """Nonexistent-user and wrong-password login should take similar wall-clock time."""
    await _register(client)

    iterations = 3

    start = time.monotonic()
    for _ in range(iterations):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "no_such_user_xyz", "password": "WrongP@ss#00"},
        )
    no_user_avg = (time.monotonic() - start) / iterations

    start = time.monotonic()
    for _ in range(iterations):
        await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": _USERNAME, "password": "WrongP@ss#00"},
        )
    wrong_pass_avg = (time.monotonic() - start) / iterations

    ratio = max(no_user_avg, wrong_pass_avg) / max(min(no_user_avg, wrong_pass_avg), 0.001)
    assert ratio < 2.0, (
        f"Timing ratio {ratio:.2f}x suggests timing leak: "
        f"no-user={no_user_avg*1000:.0f}ms, wrong-pass={wrong_pass_avg*1000:.0f}ms"
    )


# ── Security: password complexity ─────────────────────────────────────────────

async def test_weak_password_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "Password1"},
    )
    assert response.status_code == 422


async def test_password_too_short_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "Sh0rt!"},
    )
    assert response.status_code == 422


async def test_password_containing_username_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "Alice!2345678x"},
    )
    assert response.status_code == 422


async def test_reserved_username_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "admin", "email": "admin@example.com", "password": _STRONG_PASSWORD},
    )
    assert response.status_code == 422


async def test_invalid_username_chars_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "bad user!", "email": "bad@example.com", "password": _STRONG_PASSWORD},
    )
    assert response.status_code == 422


# ── Security: JWT claims ───────────────────────────────────────────────────────

async def test_jwt_has_required_claims(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    payload = jose_jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        audience=settings.JWT_AUDIENCE,
    )

    for claim in ("iat", "exp", "nbf", "iss", "aud", "sub", "type"):
        assert claim in payload, f"Missing required JWT claim: {claim}"

    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert payload["type"] == "access"


async def test_jwt_wrong_audience_rejected(client: AsyncClient) -> None:
    token = _make_token({"aud": "wrong-audience"})
    response = await client.get("/api/v1/auth/me", headers=_auth_headers(token))
    assert response.status_code == 401


async def test_jwt_wrong_issuer_rejected(client: AsyncClient) -> None:
    token = _make_token({"iss": "rogue-service"})
    response = await client.get("/api/v1/auth/me", headers=_auth_headers(token))
    assert response.status_code == 401


async def test_jwt_expired_rejected(client: AsyncClient) -> None:
    now = datetime.now(timezone.utc)
    token = _make_token({
        "iat": now - timedelta(hours=2),
        "nbf": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    })
    response = await client.get("/api/v1/auth/me", headers=_auth_headers(token))
    assert response.status_code == 401


async def test_jwt_tampered_signature_rejected(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    parts = token.split(".")
    parts[2] = parts[2][:-4] + "ZZZZ"
    tampered = ".".join(parts)

    response = await client.get("/api/v1/auth/me", headers=_auth_headers(tampered))
    assert response.status_code == 401
