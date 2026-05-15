# Miransas ID

Miransas ID is a FastAPI based identity and authentication service for the Miransas ecosystem. It provides a foundation for shared accounts, JWT authentication, ranks, badges, and future product integrations.

## Features

- FastAPI application structure
- Versioned API under `/api/v1`
- SQLModel database models
- Argon2 password hashing
- JWT access tokens
- Protected current-user endpoints
- Rank and badge fields on user accounts
- SQLite fallback for local development
- PostgreSQL support through `DATABASE_URL`

## Project Structure

```txt
src/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       ├── health.py
│       └── users.py
├── core/
│   ├── config.py
│   └── security.py
├── database/
│   └── session.py
├── models/
│   └── user.py
├── schemas/
│   ├── token.py
│   └── user.py
├── services/
│   └── auth_service.py
└── main.py
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file for production-like settings:

```env
SECRET_KEY=change-this-secret
DATABASE_URL=postgresql://user:password@localhost:5432/miransas_id
```

For local experiments, the app can run without `.env`; it falls back to SQLite.

## Run

```bash
uvicorn src.main:app --reload
```

Open:

```txt
http://127.0.0.1:8000/docs
```

## Run With Docker

```bash
docker compose up --build
```

The compose setup starts:

- `app` on `http://127.0.0.1:8000`
- `db` as PostgreSQL 16

## Tests

```bash
pytest
```

The test suite uses an isolated in-memory SQLite database and does not require PostgreSQL.

## CI

GitHub Actions runs the test suite automatically on pushes and pull requests to `main` and `develop`.

## Database Migrations

Apply migrations:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

## Current API

```txt
GET  /api/v1/health
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
PATCH /api/v1/auth/me
GET  /api/v1/users
GET  /api/v1/users/{user_id}
GET  /api/v1/admin/users
```

`/api/v1/auth/login` returns an access token and a refresh token. Send the access token as:

```txt
Authorization: Bearer <access_token>
```

Use the refresh token to request a new access token:

```json
{
  "refresh_token": "<refresh_token>"
}
```

## Rank Permissions

Miransas ID has a first permission layer based on `rank`.

- `Novice`, `Architect`, and `Elite` can use normal authenticated endpoints.
- `Core Developer` can access admin endpoints such as `/api/v1/admin/users`.

## Profile Update

Authenticated users can update their profile fields:

```json
{
  "full_name": "Miransas User",
  "badges": ["founder", "beta_tester"]
}
```

## Current Status

The project now has a working authentication baseline: user registration, login, access and refresh tokens, token validation, protected user lookup, profile updates, rank-based admin permissions, Docker Compose support, Alembic migrations, tests, and health checks. Next planned steps include refresh token rotation and broader role management.
