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
- Redis-backed sliding window rate limiting on all auth endpoints
- Username-based and IP-based brute-force lockout with escalating durations
- Login attempt log (success and failure) for forensics
- Admin endpoints to query login attempts and manually clear lockouts

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

Set `RESEND_API_KEY` in `.env` for production email sending. If empty, emails are logged to console (development mode). Set `APP_FRONTEND_URL` to the URL where verification and reset links will direct users.

Redis is required for rate limiting, brute-force protection, and token storage. Start it locally:

```bash
# Via Docker (simplest)
docker run -d -p 6379:6379 redis:7

# Or via Homebrew (macOS)
brew services start redis
```

Rate limiting is disabled by default in tests via the `RATE_LIMIT_ENABLED=False` setting.

## Run

```bash
uvicorn src.main:app --reload
```

Open `http://127.0.0.1:8000/docs`

## Run With Docker

```bash
docker compose up --build
```

The compose setup starts `app` on `http://127.0.0.1:8000`, `db` as PostgreSQL 16, and `redis` as Redis 7. All three are health-checked before the app starts.

## Tests

```bash
pytest -q
```

Uses an isolated in-memory SQLite database and fakeredis (no real Redis required). Includes timing-consistency tests, JWT claim tests, password complexity tests, user-enumeration prevention tests, rate limiting tests, brute-force lockout tests, and admin lockout management tests.

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
POST /api/v1/auth/logout-all          (requires auth)
GET  /api/v1/auth/sessions            (requires auth)
GET  /api/v1/auth/me                  (requires auth)
PATCH /api/v1/auth/me                 (requires auth)
POST /api/v1/auth/send-verification   (requires auth)
POST /api/v1/auth/verify-email
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password

GET  /api/v1/users             (requires auth, no PII)
GET  /api/v1/users/{id}        (requires auth, no PII)

GET   /api/v1/admin/users              (Core Developer only)
PATCH /api/v1/admin/users/{id}         (Core Developer only)
GET   /api/v1/admin/audit-log          (Core Developer only)
POST  /api/v1/admin/lockouts/clear     (Core Developer only)
GET   /api/v1/admin/login-attempts     (Core Developer only)
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

### Email verification

```
POST /api/v1/auth/send-verification
Authorization: Bearer <access_token>
```

Generates a 32-byte cryptographic token, stores its SHA-256 hash in Redis (24-hour TTL), and sends a verification email. Rate-limited at 3/hour per IP and 3/hour per authenticated user. Returns 400 if already verified.

```json
POST /api/v1/auth/verify-email
{ "token": "<token_from_email>" }
```

Atomically consumes the token (single-use) and marks `is_verified=true`. Invalid or expired tokens return a generic 400. Rate-limited at 10/min per IP.

### Password reset

```json
POST /api/v1/auth/forgot-password
{ "email": "charlie@example.com" }
```

Always returns 202 with an identical generic message regardless of whether the email exists (user-enumeration protection). Rate-limited at 5/hour per IP and 3/hour per email address. If the account exists, sends a reset email with a single-use token (1-hour TTL).

```json
POST /api/v1/auth/reset-password
{ "token": "<token_from_email>", "new_password": "NewStr0ng!Pass#01" }
```

Atomically consumes the token, updates the password hash, revokes **all active sessions** for the user, and deletes any outstanding verification tokens. Returns 204 on success. Same password complexity rules as registration apply.

### Public user directory

```
GET /api/v1/users
GET /api/v1/users/{id}
Authorization: Bearer <access_token>
```

Returns id, username, full_name, rank, badges. **Email, last login, and creation date are never returned** — these responses contain no PII.

### Admin endpoints (Core Developer only)

`GET /api/v1/admin/users` — full user list including all fields.

`PATCH /api/v1/admin/users/{id}` — update rank, badges, or is_active. Self-modification is blocked (403). Disabling a user immediately revokes all their active sessions atomically. Cannot remove the last active Core Developer.

`GET /api/v1/admin/audit-log` — immutable log of all admin actions with actor, target, action type, and IP address.

`POST /api/v1/admin/lockouts/clear` — manually clear username or IP lockout. Requires `username_or_email` and/or `ip` in the body. Creates an audit log entry.

`GET /api/v1/admin/login-attempts` — query the login attempt log. Supports `username`, `ip`, `success` filters, and `offset`/`limit` pagination.

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
- **Disable propagates immediately** — disabling a user revokes all their active refresh token sessions atomically in the same transaction
- **Public profiles are PII-free** — `/users` and `/users/{id}` never return email, last login, or creation date
- **Login rate limiting** — login attempts are rate-limited per IP (10/min) using a Redis-backed sliding window algorithm
- **Registration rate limiting** — registration is rate-limited to 5 per 10 minutes per IP (account enumeration prevention)
- **Refresh rate limiting** — refresh token requests are rate-limited to 30 per minute per IP
- **Username-based lockout** — 5 failed attempts → 15-minute lockout; escalates to 1-hour at 10 attempts and 24 hours at 20 attempts
- **IP-based lockout** — 20 failed attempts from a single IP → 1-hour ban regardless of which username was targeted; 100 failures → 24-hour ban
- **Lockout state disclosure prevention** — lockout responses use the same generic "Invalid credentials" message as credential failures; attackers cannot distinguish a locked account from a wrong password
- **Login attempt forensics** — every login attempt (success and failure) is persisted to the database with IP, user-agent, and failure reason; Core Developers can query and filter the log
- **Admin lockout management** — Core Developers can manually clear username or IP lockouts via API; all clears are audit-logged
- **Email verification** — verification tokens are 32-byte cryptographic random, stored as SHA-256 hashes in Redis with 24-hour TTL, single-use (atomically consumed on first use)
- **Password reset** — reset tokens have 1-hour TTL, single-use; successful reset revokes all active sessions and invalidates any outstanding verification tokens for that user
- **User enumeration protection** — `/auth/forgot-password` always returns the same response regardless of whether the email is registered
- **Email rate limiting** — forgot-password is rate-limited at 5/hour per IP and 3/hour per email address; token verification endpoints are rate-limited at 10/min per IP for brute-force protection
- **Email service abstraction** — Resend in production; emails logged to console when no API key is configured; CapturingBackend used in tests for assertion without real sends
- **Production email validation** — app refuses to boot in production with empty `RESEND_API_KEY`, `@resend.dev` sender domain, or localhost `APP_FRONTEND_URL`

### Production deployment checklist

| Setting | Required value |
|---|---|
| `SECRET_KEY` | Strong random string (min 32 chars) |
| `CORS_ORIGINS` | Explicit list, never `["*"]` |
| `DATABASE_URL` | PostgreSQL URL |
| `REDIS_URL` | Redis URL with auth (e.g. `redis://:password@host:6379/0`) |
| `ENVIRONMENT` | `production` |
| `RESEND_API_KEY` | Resend API key |
| `EMAIL_FROM` | Verified sender domain (not `@resend.dev`) |
| `APP_FRONTEND_URL` | Production frontend URL (not localhost) |
| Transport | HTTPS only |

## Current Status

FAZ-1 Bölüm 4B complete (Bölüm 1 + 2 + 3 + 4A + 4B). All planned endpoints are working. 112 tests passing.

- Auth: register, login, refresh rotation, logout, logout-all, sessions, /me, PATCH /me
- Email: send-verification (auth-required, 3/hour/user), verify-email (public, 10/min/IP, single-use token), forgot-password (public, 5/hour/IP, 3/hour/email, user-enumeration-safe), reset-password (public, revokes all sessions + outstanding tokens)
- Users: public directory (no PII), profile by id
- Admin: full user list, rank/badge/status management, audit log, lockout management, login attempts log
- Security: Argon2id, JWT claims, timing-safe auth, password complexity, security headers, immutable audit log, Core Developer invariant, atomic disable-revokes-sessions, Redis rate limiting, username/IP brute-force lockout, login attempt forensics, email verification, password reset with full session revocation, user enumeration protection, cryptographic tokens stored as hashes
