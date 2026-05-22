"""Email and token security property tests."""
import pytest
from httpx import AsyncClient

_STRONG_PASSWORD = "Str0ng!Pass#99"


async def _register_and_login(client: AsyncClient, suffix: str = "") -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": f"secuser{suffix}",
            "email": f"secuser{suffix}@example.com",
            "password": _STRONG_PASSWORD,
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": f"secuser{suffix}", "password": _STRONG_PASSWORD},
    )
    return resp.json()


async def test_verification_token_is_cryptographically_random(
    client: AsyncClient, captured_emails
) -> None:
    """100 consecutive verification tokens must all be unique."""
    tokens_seen: set[str] = set()
    import re

    for i in range(100):
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": f"uniq{i}v",
                "email": f"uniq{i}v@example.com",
                "password": _STRONG_PASSWORD,
            },
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": f"uniq{i}v", "password": _STRONG_PASSWORD},
        )
        access_token = resp.json()["access_token"]
        await client.post(
            "/api/v1/auth/send-verification",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    for email in captured_emails():
        match = re.search(r"token=([\w\-_]+)", email["text"])
        if match:
            token = match.group(1)
            assert token not in tokens_seen, f"Duplicate token found: {token}"
            tokens_seen.add(token)

    assert len(tokens_seen) == 100


async def test_reset_token_is_cryptographically_random(
    client: AsyncClient, captured_emails
) -> None:
    """100 consecutive reset tokens must all be unique."""
    import re

    for i in range(100):
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": f"uniq{i}r",
                "email": f"uniq{i}r@example.com",
                "password": _STRONG_PASSWORD,
            },
        )
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"uniq{i}r@example.com"},
        )

    tokens_seen: set[str] = set()
    for email in captured_emails():
        match = re.search(r"token=([\w\-_]+)", email["text"])
        if match:
            token = match.group(1)
            assert token not in tokens_seen, f"Duplicate reset token found: {token}"
            tokens_seen.add(token)

    assert len(tokens_seen) == 100


async def test_token_minimum_entropy(client: AsyncClient, captured_emails) -> None:
    """token_urlsafe(32) produces tokens >= 43 characters (256 bits encoded in base64url)."""
    import re

    await client.post(
        "/api/v1/auth/register",
        json={"username": "entropycheck", "email": "entropy@example.com", "password": _STRONG_PASSWORD},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "entropycheck", "password": _STRONG_PASSWORD},
    )
    await client.post(
        "/api/v1/auth/send-verification",
        headers={"Authorization": f"Bearer {resp.json()['access_token']}"},
    )

    emails = captured_emails()
    assert emails
    match = re.search(r"token=([\w\-_]+)", emails[0]["text"])
    token = match.group(1)
    assert len(token) >= 43, f"Token too short: {len(token)} chars (expected >= 43)"
