"""Password reset flow tests."""
import re

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sa_update
from sqlmodel import select

from src.core.constants import AuditAction, SessionRevocationReason
from src.core.security import hash_token
from src.models.audit_log import AuditLog
from src.models.session import UserSession
from src.models.user import User

_USERNAME = "resetuser"
_EMAIL = "resetuser@example.com"
_STRONG_PASSWORD = "Str0ng!Pass#99"
_NEW_PASSWORD = "NewStr0ng!Pass#01"
_WRONG_NEW_PASSWORD = "weak"


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
    assert resp.status_code == 201


async def _login(
    client: AsyncClient,
    username: str = _USERNAME,
    password: str = _STRONG_PASSWORD,
) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": password},
    )
    return resp.json() if resp.status_code == 200 else {}


def _extract_token_from_email(email_body: str) -> str:
    match = re.search(r"token=([\w\-_]+)", email_body)
    assert match, f"No token in body:\n{email_body}"
    return match.group(1)


async def _forgot(client: AsyncClient, email: str = _EMAIL) -> int:
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
    )
    return resp.status_code


# ── Core flow ──────────────────────────────────────────────────────────────────

async def test_forgot_password_sends_email_for_existing_user(
    client: AsyncClient, captured_emails
) -> None:
    await _register(client)
    status = await _forgot(client)
    assert status == 202
    emails = captured_emails()
    assert len(emails) == 1
    assert emails[0]["to"] == _EMAIL
    assert "reset" in emails[0]["subject"].lower()


async def test_forgot_password_does_not_send_for_nonexistent_user(
    client: AsyncClient, captured_emails
) -> None:
    """No email sent for unknown address, but response is still 202."""
    status = await _forgot(client, email="nobody@example.com")
    assert status == 202
    assert len(captured_emails()) == 0


async def test_forgot_password_response_is_generic(
    client: AsyncClient, captured_emails
) -> None:
    """Existing and non-existing email return identical response body."""
    await _register(client)

    resp_exists = await client.post(
        "/api/v1/auth/forgot-password", json={"email": _EMAIL}
    )
    resp_missing = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}
    )

    assert resp_exists.status_code == resp_missing.status_code == 202
    assert resp_exists.json() == resp_missing.json()


async def test_forgot_password_rate_limited_per_ip(
    client: AsyncClient, captured_emails, monkeypatch
) -> None:
    """6th forgot-password from the same IP within 1 hour → 429."""
    from src.core.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    await _register(client)

    for _ in range(5):
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": _EMAIL},
            headers={"X-Forwarded-For": "30.0.0.1"},
        )

    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": _EMAIL},
        headers={"X-Forwarded-For": "30.0.0.1"},
    )
    assert resp.status_code == 429


async def test_forgot_password_rate_limited_per_email(
    client: AsyncClient, captured_emails, monkeypatch
) -> None:
    """Per-email limit (3/hour): 4th request silently drops with generic 202, no new email."""
    from src.core.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    await _register(client)

    # 3 successful sends from different IPs
    for i in range(3):
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": _EMAIL},
            headers={"X-Forwarded-For": f"30.1.1.{i+1}"},
        )
    assert len(captured_emails()) == 3

    # 4th: per-email limit hit — silently swallowed, returns generic 202
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": _EMAIL},
        headers={"X-Forwarded-For": "30.1.1.99"},
    )
    assert resp.status_code == 202
    assert len(captured_emails()) == 3  # no new email


async def test_reset_password_updates_password(
    client: AsyncClient, captured_emails
) -> None:
    """After reset, old password fails and new password works."""
    await _register(client)
    await _forgot(client)
    token = _extract_token_from_email(captured_emails()[0]["text"])

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": _NEW_PASSWORD},
    )
    assert resp.status_code == 204

    # Old password no longer works
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _STRONG_PASSWORD},
    )
    assert old_login.status_code == 401

    # New password works
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": _USERNAME, "password": _NEW_PASSWORD},
    )
    assert new_login.status_code == 200


async def test_reset_password_revokes_all_sessions(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    """After password reset, all previously active sessions are revoked."""
    await _register(client)

    # Create 3 sessions
    session_tokens = []
    for _ in range(3):
        tokens = await _login(client)
        session_tokens.append(tokens["refresh_token"])

    await _forgot(client)
    reset_token = _extract_token_from_email(captured_emails()[-1]["text"])

    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": _NEW_PASSWORD},
    )

    # All sessions must now be revoked with reason=password_reset
    result = await db.execute(
        select(UserSession).where(
            UserSession.revocation_reason == SessionRevocationReason.PASSWORD_RESET
        )
    )
    revoked = result.scalars().all()
    assert len(revoked) == 3


async def test_reset_password_token_single_use(
    client: AsyncClient, captured_emails
) -> None:
    """Using a reset token twice → second attempt returns 400."""
    await _register(client)
    await _forgot(client)
    token = _extract_token_from_email(captured_emails()[0]["text"])

    first = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": _NEW_PASSWORD},
    )
    assert first.status_code == 204

    second = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "Anoth3r!Pass#77"},
    )
    assert second.status_code == 400


async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "a" * 43, "new_password": _NEW_PASSWORD},
    )
    assert resp.status_code == 400
    assert "Invalid or expired" in resp.json()["detail"]


async def test_reset_password_writes_audit_log(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    await _register(client)
    await _forgot(client)
    token = _extract_token_from_email(captured_emails()[0]["text"])

    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": _NEW_PASSWORD},
    )

    result = await db.execute(
        select(AuditLog).where(AuditLog.action == AuditAction.PASSWORD_RESET_COMPLETED)
    )
    assert result.scalars().first() is not None

    result2 = await db.execute(
        select(AuditLog).where(AuditLog.action == AuditAction.PASSWORD_RESET_REQUESTED)
    )
    assert result2.scalars().first() is not None


async def test_reset_password_rejects_weak_password(
    client: AsyncClient, captured_emails
) -> None:
    """Weak new_password → 422."""
    await _register(client)
    await _forgot(client)
    token = _extract_token_from_email(captured_emails()[0]["text"])

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "weakpassword"},
    )
    assert resp.status_code == 422


async def test_reset_password_rejects_inactive_user(
    client: AsyncClient, db: AsyncSession, captured_emails
) -> None:
    """Resetting password for a disabled account → 400."""
    await _register(client)
    await _forgot(client)
    token = _extract_token_from_email(captured_emails()[0]["text"])

    # Disable user
    result = await db.execute(select(User).where(User.username == _USERNAME))
    user = result.scalars().first()
    user.is_active = False
    db.add(user)
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": _NEW_PASSWORD},
    )
    assert resp.status_code == 400


async def test_password_reset_token_is_hashed_in_redis(
    client: AsyncClient, fake_redis, captured_emails
) -> None:
    """Plain reset token must not exist in Redis; the hashed form must."""
    await _register(client)
    await _forgot(client)
    plain_token = _extract_token_from_email(captured_emails()[0]["text"])

    from src.core.constants import TOKEN_TYPE_PASSWORD_RESET
    plain_key = f"{TOKEN_TYPE_PASSWORD_RESET}:{plain_token}"
    hashed_key = f"{TOKEN_TYPE_PASSWORD_RESET}:{hash_token(plain_token)}"

    assert await fake_redis.exists(plain_key) == 0
    assert await fake_redis.exists(hashed_key) == 1


async def test_password_reset_invalidates_outstanding_verification_tokens(
    client: AsyncClient, fake_redis, captured_emails
) -> None:
    """After a password reset, any pending email verification tokens for that user are revoked."""
    await _register(client)
    tokens = await _login(client)

    # Get a verification token
    await client.post(
        "/api/v1/auth/send-verification",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    verify_token = _extract_token_from_email(captured_emails()[-1]["text"])

    # Now reset password
    await _forgot(client)
    reset_token = _extract_token_from_email(captured_emails()[-1]["text"])
    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": _NEW_PASSWORD},
    )

    # The old verification token should now be gone
    from src.core.constants import TOKEN_TYPE_EMAIL_VERIFY
    hashed_verify_key = f"{TOKEN_TYPE_EMAIL_VERIFY}:{hash_token(verify_token)}"
    assert await fake_redis.exists(hashed_verify_key) == 0
