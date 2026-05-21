# Miransas ID

Miransas ID is the central authentication provider for the Miransas ecosystem. A compromised account here means Binboi, Rabilt, and all connected products are exposed — security is the primary constraint on every design decision.

## Features

- FastAPI application with versioned API under `/api/v1`
- SQLModel async ORM (SQLite in development, PostgreSQL in production)
- Argon2id password hashing (64 MiB, t=3, p=4, 256-bit hash)
- JWT HS256 with `iss`, `aud`, `iat`, `nbf`, `exp`, `sub`, `type` claims
- Rank and badge fields: `Novice`, `Architect`, `Elite`, `Core Developer`
- Immutable audit log for all admin actions (actor, target, action, IP, timestamp)
- Rank-based access control — Core Developer rank required for admin endpoints
- Security response headers on every response
- Password complexity enforcement with user-enumeration-resistant error messages
- Startup validation — production with unsafe defaults refuses to boot
- Refresh token rotation with reuse detection and token family invalidation
- Server-side session revocation — tokens stored as SHA-256 hashes; per-device and global logout
- Session metadata — user-agent and IP recorded per session for visibility
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

Open `http://127.0.0.1:8000/docs`

## Run With Docker

```bash
docker compose up --build
```

The compose setup starts `app` on `http://127.0.0.1:8000` and `db` as PostgreSQL 16.

## Tests

```bash
pytest -q
```

Uses an isolated in-memory SQLite database. Includes timing-consistency tests, JWT claim tests, password complexity tests, and user-enumeration prevention tests.

## Database Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## Current API

```
GET  /api/v1/health

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all   (requires auth)
GET  /api/v1/auth/sessions     (requires auth)
GET  /api/v1/auth/me           (requires auth)
PATCH /api/v1/auth/me          (requires auth)

GET  /api/v1/users             (requires auth, no PII)
GET  /api/v1/users/{id}        (requires auth, no PII)

GET   /api/v1/admin/users              (Core Developer only)
PATCH /api/v1/admin/users/{id}         (Core Developer only)
GET   /api/v1/admin/audit-log          (Core Developer only)
```

### Register

```json
POST /api/v1/auth/register
{
  "username": "charlie",
  "email": "charlie@example.com",
  "password": "Str0ng!Pass#99",
  "full_name": "Charlie"
}
```

Password rules: ≥ 12 characters, at least one uppercase, lowercase, digit, and special character. Must not contain your username or email. Common passwords are rejected. Some usernames are reserved (`admin`, `root`, `miransas`, etc.).

Returns the created user profile (201). Duplicate username/email returns a generic 400 — the specific field is never revealed.

### Login

```json
POST /api/v1/auth/login
{
  "username_or_email": "charlie",
  "password": "Str0ng!Pass#99"
}
```

Returns `{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}`. Incorrect credentials always return the same generic 401 regardless of whether the user exists (timing-normalised via dummy Argon2 verification).

### Refresh token rotation

```json
POST /api/v1/auth/refresh
{ "refresh_token": "<refresh_token>" }
```

Returns a new token pair. The presented refresh token is immediately invalidated (single-use rotation). Reuse of an already-rotated refresh token triggers automatic invalidation of the entire token family — all sessions for that user/device lose access.

### Logout

```json
POST /api/v1/auth/logout
{ "refresh_token": "<refresh_token>" }
```

Revokes the specific session. Always returns 204 (idempotent — no information leaked for invalid tokens).

### Logout all devices

```
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>
```

Revokes all active sessions for the authenticated user (204).

### Sessions list

```
GET /api/v1/auth/sessions
Authorization: Bearer <access_token>
```

Returns active sessions with user-agent and IP address for visibility.

### Protected endpoints

```
Authorization: Bearer <access_token>
```

`GET /api/v1/auth/me` returns the currently authenticated user.
`PATCH /api/v1/auth/me` updates `full_name` (the only self-editable field).

### Public user directory

```
GET /api/v1/users
GET /api/v1/users/{id}
Authorization: Bearer <access_token>
```

Returns id, username, full_name, rank, badges. **Email, last login, and creation date are never returned** — these responses contain no PII.

### Admin endpoints (Core Developer only)

`GET /api/v1/admin/users` — full user list including all fields.

`PATCH /api/v1/admin/users/{id}` — update rank, badges, or is_active. Self-modification is blocked (403). Disabling a user immediately revokes all their active sessions. Cannot remove the last active Core Developer.

`GET /api/v1/admin/audit-log` — immutable log of all admin actions with actor, target, action type, and IP address.

## Rank Permissions

| Rank | Authenticated endpoints | Admin endpoints | Audit log |
|---|---|---|---|
| Novice | ✓ | — | — |
| Architect | ✓ | — | — |
| Elite | ✓ | — | — |
| Core Developer | ✓ | ✓ | ✓ |

## Security

This is the central authentication provider for the Miransas ecosystem. Security guarantees:

- **Argon2id passwords** — 64 MiB, 3 iterations, 4 threads, 256-bit output
- **JWT with full claims** — `iss`, `aud`, `iat`, `nbf`, `exp` enforced on every token
- **User-enumeration prevention** — all auth errors use generic messages; failed login always runs a full Argon2 verification to normalise timing
- **Password complexity** — 12+ chars, uppercase, lowercase, digit, special; username/email must not appear in password; common passwords rejected
- **Reserved usernames** — platform-sensitive names cannot be registered
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` on every response; `Strict-Transport-Security` in production
- **Production startup validation** — app refuses to boot with default `SECRET_KEY` or wildcard `CORS_ORIGINS` when `ENVIRONMENT=production`
- **Immutable audit log** — admin actions (rank, badges, active status) are recorded with actor ID, target ID, action, IP address, and timestamp; entries are never deleted
- **Self-modification blocked** — Core Developers cannot modify their own rank or status via admin endpoints
- **Last Core Developer invariant** — disabling or demoting the last active Core Developer is rejected with 400
- **Disable propagates immediately** — disabling a user revokes all their active refresh token sessions at the same time
- **Public profiles are PII-free** — `/users` and `/users/{id}` never return email, last login, or creation date

### Production deployment checklist

| Setting | Required value |
|---|---|
| `SECRET_KEY` | Strong random string (min 32 chars) |
| `CORS_ORIGINS` | Explicit list, never `["*"]` |
| `DATABASE_URL` | PostgreSQL URL |
| `ENVIRONMENT` | `production` |
| Transport | HTTPS only |

## Current Status

FAZ-1 complete (Bölüm 1 + 2 + 3). All planned endpoints are working:

- Auth: register, login, refresh rotation, logout, logout-all, sessions, /me, PATCH /me
- Users: public directory (no PII), profile by id
- Admin: full user list, rank/badge/status management, audit log
- Security: Argon2id, JWT claims, timing-safe auth, password complexity, security headers, immutable audit log, Core Developer invariant, disable-revokes-sessions
