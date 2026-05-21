import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient, username: str = "miransas", email: str = "miransas@example.com") -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "Secret123"},
    )


async def _login(client: AsyncClient, username_or_email: str = "miransas", password: str = "Secret123") -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password},
    )
    return response.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "miransas", "email": "miransas@example.com", "password": "Secret123"},
    )
    body = response.json()

    assert response.status_code == 201
    assert body["username"] == "miransas"
    assert body["email"] == "miransas@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_returns_400(client: AsyncClient):
    await _register(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "miransas", "email": "miransas@example.com", "password": "Secret123"},
    )
    assert response.status_code == 400


async def test_login_returns_access_token(client: AsyncClient):
    await _register(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "miransas", "password": "Secret123"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "refresh_token" not in body


async def test_auth_me_requires_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_auth_me_returns_current_user(client: AsyncClient):
    await _register(client)
    token_data = await _login(client)
    token = token_data["access_token"]

    response = await client.get("/api/v1/auth/me", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["username"] == "miransas"
