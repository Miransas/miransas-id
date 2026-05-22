# Contributing to Miransas ID

Internal project — Miransas team only.

## Setup

```bash
git clone <repo> && cd miransas-id
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn src.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Tests

```bash
pytest -q                     # all tests
pytest -v -k "test_name"      # single test
pytest --cov=src              # with coverage report
```

Tests use an in-memory SQLite database and fakeredis — no real Redis or PostgreSQL required.

## Code Style

- Type hints everywhere.
- Run `ruff check src/ tests/` before pushing.
- Service-layer methods are `async` and `@staticmethod` — no state on service classes.
- Endpoints are thin: validate input → call service → return response.
- All user-facing error messages are generic — never reveal whether a user, email, or resource exists.

## Adding a New Endpoint

1. Schema in `src/schemas/`
2. Service logic in `src/services/`
3. Route in `src/api/v1/`
4. Migration in `migrations/versions/` if DB schema changes
5. Tests in `tests/` — happy path + at least one security/edge case
6. Update `README.md` API list

## Security Checklist

Before merging any change touching auth, sessions, tokens, or admin endpoints:

- [ ] Generic error messages (no information leakage)
- [ ] Tested with invalid and malformed input
- [ ] Audit log entry written for admin actions
- [ ] Rate limit applied to public endpoints
- [ ] No secrets, tokens, or PII in log output
- [ ] If a new sensitive field is added, update `_SENSITIVE_KEYS` in `src/core/observability.py`

See [SECURITY.md](SECURITY.md) for the full security policy.
