def register_user(
    client,
    username="miransas",
    email="miransas@example.com",
    rank="Novice",
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "secret123",
            "rank": rank,
        },
    )


def login_user(client, username="miransas", password="secret123"):
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_user(client):
    response = register_user(client)
    body = response.json()

    assert response.status_code == 201
    assert body["username"] == "miransas"
    assert body["email"] == "miransas@example.com"
    assert "password" not in body


def test_register_duplicate_user_returns_400(client):
    first = register_user(client)
    second = register_user(client)

    assert first.status_code == 201
    assert second.status_code == 400


def test_login_returns_bearer_token(client):
    register_user(client)

    response = login_user(client)
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_returns_new_access_token(client):
    register_user(client)
    login = login_user(client)
    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != refresh_token


def test_refresh_rotation_rejects_reused_refresh_token(client):
    register_user(client)
    login = login_user(client)
    refresh_token = login.json()["refresh_token"]

    first_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert first_refresh.status_code == 200
    assert second_refresh.status_code == 401


def test_refresh_rejects_access_token(client):
    register_user(client)
    login = login_user(client)
    access_token = login.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    register_user(client)
    login = login_user(client)
    refresh_token = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert logout.status_code == 204
    assert refresh.status_code == 401


def test_auth_me_requires_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_auth_me_returns_current_user(client):
    register_user(client)
    login = login_user(client)
    token = login.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["username"] == "miransas"


def test_update_current_user_profile(client):
    register_user(client)
    login = login_user(client)
    token = login.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers=auth_headers(token),
        json={
            "full_name": "Miransas User",
            "badges": ["founder", "beta_tester"],
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["full_name"] == "Miransas User"
    assert body["badges"] == ["founder", "beta_tester"]


def test_list_users_requires_token(client):
    response = client.get("/api/v1/users")

    assert response.status_code == 401


def test_list_users_with_token(client):
    register_user(client)
    login = login_user(client)
    token = login.json()["access_token"]

    response = client.get("/api/v1/users", headers=auth_headers(token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_admin_users_requires_core_developer_rank(client):
    register_user(client)
    login = login_user(client)
    token = login.json()["access_token"]

    response = client.get("/api/v1/admin/users", headers=auth_headers(token))

    assert response.status_code == 403


def test_admin_users_allows_core_developer(client):
    register_user(
        client,
        username="coredev",
        email="coredev@example.com",
        rank="Core Developer",
    )
    login = login_user(client, username="coredev")
    token = login.json()["access_token"]

    response = client.get("/api/v1/admin/users", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()[0]["username"] == "coredev"
