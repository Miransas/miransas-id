"""Email verification flow tests."""
import re

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.constants import AuditAction
from src.core.security import get_password_hash, hash_token
from src.models.audit_log import AuditLog
from src.models.user import User

_USERNAME = "verifyuser"
_EMAIL = "verifyuser@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"


async def _register(
    client: AsyncClient,
    username: str = _USERNAME,
    email: str = _EMAIL,
    password: str = _STRONG_PASSWORD,
) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()


async def _login(
    client: AsyncClient,
    username: str = _USERNAME,
    password: str = _STRONG_PASSWORD,
) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": password},
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _extract_token_from_email(email_body: str) -> str:
    match = re.search(r"token=([\w\-_]+)", email_body)
    assert match, f"No token found in email body:\n{email_body}"
    return match.group(1)


# ── Core flow ──────────────────────────────────────────────────────────────────

async def test_send_verification_sends_email(
    client: AsyncClient, captured_emails
) -> None:
    """Sending verification email captures a message with the correct recipient."""
    await _register(client)
    tokens = await _login(client)
    headers = _auth_headers(tokens["access_token"])

    resp = await client.post("/api/v1/auth/send-verification", headers=headers)

    assert resp.status_code == 200
    emails = captured_emails()
    assert len(emails) == 1
    assert emails[0]["to"] == _EMAIL
    assert "verify" in emails[0]["subject"].lower()
    assert "token=" in emails[0]["text"]


async def test_send_verification_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/send-verification")
    assert resp.status_code == 401


async def test_send_verification_rate_limited_per_user(
    client: AsyncClient, captured_emails, monkeypatch
) -> None:
    """4th send-verification request from the same user within 1 hour → 429."""
    from src.core.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    await _register(client)
    tokens = await _login(client)
    headers = _auth_headers(tokens["access_token"])

    for _ in range(3):
        await client.post("/api/v1/auth/send-verification", headers=headers)

    resp = await client.post("/api/v1/auth/send-verification", headers=headers)
    assert resp.status_code == 429


async def test_send_verification_already_verified_returns_400(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    """Sending verification to an already-verified user returns 400."""
    await _register(client)
    tokens = await _login(client)

    # Force-verify via DB
    result = await db.execute(select(User).where(User.username == _USERNAME))
    user = result.scalars().first()
    user.is_verified = True
    db.add(user)
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )
    assert resp.status_code == 400
    assert "already verified" in resp.json()["detail"].lower()


async def test_verify_email_marks_user_verified(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    """Full flow: send → extract token → verify → is_verified=True in DB."""
    await _register(client)
    tokens = await _login(client)

    await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )

    token = _extract_token_from_email(captured_emails()[0]["text"])
    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})

    assert resp.status_code == 200
    assert resp.json()["is_verified"] is True

    await db.invalidate()
    result = await db.execute(select(User).where(User.username == _USERNAME))
    user = result.scalars().first()
    assert user.is_verified is True


async def test_verify_email_token_is_single_use(
    client: AsyncClient, captured_emails
) -> None:
    """Using a token a second time returns 400."""
    await _register(client)
    tokens = await _login(client)

    await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )

    token = _extract_token_from_email(captured_emails()[0]["text"])
    first = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert first.status_code == 200

    second = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert second.status_code == 400


async def test_verify_email_invalid_token_returns_400(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/verify-email", json={"token": "a" * 43})
    assert resp.status_code == 400
    assert "Invalid or expired" in resp.json()["detail"]


async def test_verify_email_writes_audit_log(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    await _register(client)
    tokens = await _login(client)

    await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )
    token = _extract_token_from_email(captured_emails()[0]["text"])
    await client.post("/api/v1/auth/verify-email", json={"token": token})

    result = await db.execute(
        select(AuditLog).where(AuditLog.action == AuditAction.EMAIL_VERIFIED)
    )
    entry = result.scalars().first()
    assert entry is not None


async def test_verify_email_rate_limited(
    client: AsyncClient, captured_emails, monkeypatch
) -> None:
    """11th verify-email attempt from same IP → 429."""
    from src.core.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    await _register(client)
    tokens = await _login(client)
    await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )

    for _ in range(10):
        await client.post(
            "/api/v1/auth/verify-email",
            json={"token": "x" * 43},
            headers={"X-Forwarded-For": "20.0.0.1"},
        )

    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": "x" * 43},
        headers={"X-Forwarded-For": "20.0.0.1"},
    )
    assert resp.status_code == 429


async def test_verify_email_for_inactive_user_rejected(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    """Verifying email for a disabled user returns 400."""
    await _register(client)
    tokens = await _login(client)

    await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )
    token = _extract_token_from_email(captured_emails()[0]["text"])

    # Disable user
    result = await db.execute(select(User).where(User.username == _USERNAME))
    user = result.scalars().first()
    user.is_active = False
    db.add(user)
    await db.commit()

    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 400


async def test_verification_token_is_hashed_in_redis(
    client: AsyncClient, fake_redis, captured_emails
) -> None:
    """The plain token must NOT exist as a Redis key; the hashed form must."""
    await _register(client)
    tokens = await _login(client)

    await client.post(
        "/api/v1/auth/send-verification",
        headers=_auth_headers(tokens["access_token"]),
    )
    plain_token = _extract_token_from_email(captured_emails()[0]["text"])

    from src.core.constants import TOKEN_TYPE_EMAIL_VERIFY
    plain_key = f"{TOKEN_TYPE_EMAIL_VERIFY}:{plain_token}"
    hashed_key = f"{TOKEN_TYPE_EMAIL_VERIFY}:{hash_token(plain_token)}"

    plain_exists = await fake_redis.exists(plain_key)
    hashed_exists = await fake_redis.exists(hashed_key)

    assert plain_exists == 0, "Plain token must not exist in Redis"
    assert hashed_exists == 1, "Hashed token must exist in Redis"
