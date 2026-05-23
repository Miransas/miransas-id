from httpx import AsyncClient

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


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── PATCH /auth/me ─────────────────────────────────────────────────────────────

async def test_patch_me_updates_full_name(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.patch(
        "/api/v1/auth/me",
        headers=_auth(token),
        json={"full_name": "Charlie Brown"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Charlie Brown"


async def test_patch_me_empty_body_changes_nothing(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.patch("/api/v1/auth/me", headers=_auth(token), json={})
    assert resp.status_code == 200
    assert resp.json()["username"] == _USERNAME


async def test_patch_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/auth/me", json={"full_name": "Ghost"})
    assert resp.status_code == 401


async def test_patch_me_does_not_expose_password(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.patch(
        "/api/v1/auth/me", headers=_auth(token), json={"full_name": "X"}
    )
    body = resp.json()
    assert "password" not in body
    assert "hashed_password" not in body


# ── GET /users ─────────────────────────────────────────────────────────────────

async def test_list_users_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users")
    assert resp.status_code == 401


async def test_list_users_returns_active_users(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.get("/api/v1/users", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["username"] == _USERNAME


async def test_list_users_no_pii(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.get("/api/v1/users", headers=_auth(token))
    user = resp.json()[0]

    assert "email" not in user
    assert "last_login" not in user
    assert "created_at" not in user
    assert "hashed_password" not in user
    assert "is_active" not in user


# ── GET /users/{id} ────────────────────────────────────────────────────────────

async def test_get_user_returns_public_profile(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    list_resp = await client.get("/api/v1/users", headers=_auth(token))
    user_id = list_resp.json()[0]["id"]

    resp = await client.get(f"/api/v1/users/{user_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == _USERNAME


async def test_get_user_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/1")
    assert resp.status_code == 401


async def test_get_user_not_found_returns_404(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.get("/api/v1/users/9999", headers=_auth(token))
    assert resp.status_code == 404


async def test_get_user_no_pii(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    list_resp = await client.get("/api/v1/users", headers=_auth(token))
    user_id = list_resp.json()[0]["id"]

    resp = await client.get(f"/api/v1/users/{user_id}", headers=_auth(token))
    body = resp.json()

    assert "email" not in body
    assert "last_login" not in body
    assert "created_at" not in body


# ── GET /users/me ──────────────────────────────────────────────────────────────

async def test_get_me_authenticated_returns_user(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.get("/api/v1/users/me", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == _USERNAME


async def test_get_me_unauthenticated_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_get_me_includes_email(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    resp = await client.get("/api/v1/users/me", headers=_auth(token))
    body = resp.json()
    assert "email" in body
    assert body["email"] == _EMAIL


async def test_get_me_does_not_collide_with_user_id_route(client: AsyncClient) -> None:
    await _register(client)
    token = (await _login(client))["access_token"]

    me_resp = await client.get("/api/v1/users/me", headers=_auth(token))
    assert me_resp.status_code == 200

    user_id = me_resp.json()["id"]
    id_resp = await client.get(f"/api/v1/users/{user_id}", headers=_auth(token))
    assert id_resp.status_code == 200
    assert id_resp.json()["username"] == _USERNAME
