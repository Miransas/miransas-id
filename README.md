# Miransas ID

Miransas ID is a FastAPI-based identity and authentication service for the Miransas ecosystem. It provides a foundation for shared accounts, JWT authentication, ranks, badges, and future product integrations.

## Features

- FastAPI application with versioned API under `/api/v1`
- SQLModel async ORM (SQLite in development, PostgreSQL in production)
- Argon2id password hashing via `passlib[argon2]`
- JWT access tokens (HS256)
- Rank and badge fields on user accounts (`Novice`, `Architect`, `Elite`, `Core Developer`)
- Alembic migrations

## Project Structure

```
src/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       └── health.py
├── core/
│   ├── config.py
│   └── security.py
├── database/
│   └── session.py
├── models/
│   ├── session.py
│   └── user.py
├── schemas/
│   ├── auth.py
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

Copy the example env and adjust for your environment:

```bash
cp .env.example .env
```

For local development, the app runs without `.env` and falls back to SQLite automatically.

## Run

```bash
uvicorn src.main:app --reload
```

Open:

```
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
pytest -q
```

The test suite uses an isolated in-memory SQLite database and does not require PostgreSQL.

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

```
GET  /api/v1/health
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Register

```json
POST /api/v1/auth/register
{
  "username": "sardor",
  "email": "sardor@example.com",
  "password": "Secret123",
  "full_name": "Sardor"
}
```

Returns the created user (201).

### Login

```json
POST /api/v1/auth/login
{
  "username_or_email": "sardor",
  "password": "Secret123"
}
```

Returns `{"access_token": "...", "token_type": "bearer"}`.

### Protected endpoints

Send the access token as:

```
Authorization: Bearer <access_token>
```

`GET /api/v1/auth/me` returns the currently authenticated user.

## Current Status

FAZ-1 Bölüm 1 complete. Working endpoints: register, login, `/me`. Single async stack (SQLModel + AsyncSession + Argon2 + JWT HS256).

Planned for upcoming sections:
- Bölüm 2: refresh token rotation, server-side session revocation, logout
- Bölüm 3: profile update (`PATCH /auth/me`), user listing, rank-based admin endpoints
