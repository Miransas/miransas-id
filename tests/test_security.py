"""Tests for JWT security properties — rank claim presence, backward compat."""
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt as jose_jwt

from src.core.config import settings
from src.core.security import create_access_token, create_refresh_token, create_token_id, decode_token
from src.models.user import MiransasRank

_USERNAME = "charlie"
_EMAIL = "charlie@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"


async def _register(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": _USERNAME, "email": _EMAIL, "password": _STRONG_PASSWORD},
    )


async def _login(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
    )
    return resp.json()


# ── Rank claim ─────────────────────────────────────────────────────────────────

def test_access_token_contains_rank_claim() -> None:
    token = create_access_token(subject=42, rank=MiransasRank.NOVICE.value)
    payload = jose_jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        audience=settings.JWT_AUDIENCE,
    )
    assert "rank" in payload
    assert payload["rank"] == MiransasRank.NOVICE.value


def test_access_token_rank_reflects_user_rank() -> None:
    for rank in MiransasRank:
        token = create_access_token(subject=1, rank=rank.value)
        payload = jose_jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
        )
        assert payload["rank"] == rank.value


def test_refresh_token_does_not_contain_rank() -> None:
    token = create_refresh_token(subject=42, token_id=create_token_id())
    payload = jose_jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        audience=settings.JWT_AUDIENCE,
    )
    assert "rank" not in payload


def test_decode_token_backward_compat_no_rank() -> None:
    """Tokens minted before rank was added must still decode successfully."""
    now = datetime.now(timezone.utc)
    old_token = jose_jwt.encode(
        {
            "sub": "1",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=15),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "access",
            # no "rank" claim
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    payload = decode_token(old_token, expected_type="access")
    assert payload["sub"] == "1"
    assert "rank" not in payload


# ── Login response carries rank claim ─────────────────────────────────────────

async def test_login_access_token_has_rank_claim(client: AsyncClient) -> None:
    await _register(client)
    tokens = await _login(client)

    payload = jose_jwt.decode(
        tokens["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        audience=settings.JWT_AUDIENCE,
    )
    assert "rank" in payload
    assert payload["rank"] == MiransasRank.NOVICE.value


async def test_refresh_access_token_has_rank_claim(client: AsyncClient) -> None:
    """After token rotation, the new access token must also carry rank."""
    await _register(client)
    tokens = await _login(client)

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200

    payload = jose_jwt.decode(
        refresh_resp.json()["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        audience=settings.JWT_AUDIENCE,
    )
    assert "rank" in payload
    assert payload["rank"] == MiransasRank.NOVICE.value
