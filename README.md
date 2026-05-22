# Miransas ID

[![CI](https://github.com/Miransas/miransas-id/actions/workflows/main.yml/badge.svg)](https://github.com/Miransas/miransas-id/actions)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

The central authentication and identity provider for the Miransas ecosystem.

> **Warning:** This service issues credentials for every Miransas product (Binboi, Rabilt, miransas-db, and future services). A compromised account here means all connected products are exposed — security is the primary constraint on every design decision.

## Features

- Auth core: register, login, refresh token rotation with reuse detection, logout (single device + all devices)
- Email verification + password reset (Resend), with cryptographic single-use tokens stored as SHA-256 hashes
- RBAC: Novice / Architect / Elite / Core Developer
- Two-layer brute-force lockout (username + IP) with escalating durations
- User enumeration protection across all entry points (timing normalization, generic errors)
- Immutable audit log for all admin actions
- Argon2id passwords (64 MiB, t=3, p=4), JWT HS256 with full claim set (iss, aud, iat, nbf, exp, sub, type)
- Structured JSON logging (production) + Sentry error tracking with PII scrubbing
- Docker multi-stage build, non-root container user
- 118 tests covering all security invariants

## Quick Start

```bash
git clone <repo> && cd miransas-id
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn src.main:app --reload
```

Visit http://127.0.0.1:8000/docs

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full checklist.

```bash
cp .env.production.example .env
# Fill in all required secrets (openssl rand -hex 32 for SECRET_KEY)
docker compose up -d --build
docker compose exec miransas-id-app ./scripts/migrate.sh up
curl http://localhost:8000/api/v1/health/detailed
```

## API

### Authentication
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/v1/auth/register` | — |
| POST | `/api/v1/auth/login` | — |
| POST | `/api/v1/auth/refresh` | — |
| POST | `/api/v1/auth/logout` | — |
| POST | `/api/v1/auth/logout-all` | Bearer |
| GET  | `/api/v1/auth/sessions` | Bearer |
| GET  | `/api/v1/auth/me` | Bearer |
| PATCH | `/api/v1/auth/me` | Bearer |
| POST | `/api/v1/auth/send-verification` | Bearer |
| POST | `/api/v1/auth/verify-email` | — |
| POST | `/api/v1/auth/forgot-password` | — |
| POST | `/api/v1/auth/reset-password` | — |

### Users
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/api/v1/users` | Bearer |
| GET | `/api/v1/users/{user_id}` | Bearer |

### Admin (Core Developer only)
| Method | Endpoint |
|--------|----------|
| GET   | `/api/v1/admin/users` |
| GET   | `/api/v1/admin/users/{user_id}` |
| PATCH | `/api/v1/admin/users/{user_id}` |
| GET   | `/api/v1/admin/audit-log` |
| POST  | `/api/v1/admin/lockouts/clear` |
| GET   | `/api/v1/admin/login-attempts` |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Liveness probe |
| GET | `/api/v1/health/detailed` | Readiness probe — checks DB + Redis |

## Running Tests

```bash
pytest -q                      # all tests
pytest -v -k "test_name"       # single test
pytest --cov=src               # with coverage report
```

Tests use in-memory SQLite and fakeredis — no real Redis or PostgreSQL required.

## Database Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## Security

See [SECURITY.md](SECURITY.md) for the complete policy and disclosure timeline.

Key guarantees: Argon2id · JWT full claims · refresh token rotation + reuse detection · username/IP lockout · user enumeration protection · immutable audit log · production startup validation · Sentry PII scrubbing.

## Stack

Python 3.12+ · FastAPI · SQLModel + async SQLAlchemy · PostgreSQL 16 (asyncpg) · Redis 7 · Alembic · Argon2id · python-jose · Resend · Sentry · pytest + pytest-asyncio + fakeredis

## Rank Permissions

| Rank | Auth endpoints | Admin endpoints |
|------|---------------|-----------------|
| Novice | ✓ | — |
| Architect | ✓ | — |
| Elite | ✓ | — |
| Core Developer | ✓ | ✓ |

## License

MIT

---

**Status:** FAZ-1 complete. 118 tests passing, 93% coverage.
