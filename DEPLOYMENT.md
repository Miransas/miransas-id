# Production Deployment

## Before First Deploy

### Secrets

```bash
openssl rand -hex 32   # SECRET_KEY
openssl rand -base64 24  # POSTGRES_PASSWORD, REDIS_PASSWORD
```

- [ ] `SECRET_KEY` generated (32+ random chars)
- [ ] `POSTGRES_PASSWORD` generated
- [ ] `REDIS_PASSWORD` generated
- [ ] `RESEND_API_KEY` obtained from resend.com/api-keys
- [ ] Resend sender domain verified (`noreply@miransas.com`)
- [ ] `SENTRY_DSN` obtained from sentry.io (recommended)

### Configuration

- [ ] `ENVIRONMENT=production` in `.env`
- [ ] `CORS_ORIGINS` set to explicit allowlist (no `*`)
- [ ] `APP_FRONTEND_URL` set to production console URL
- [ ] `EMAIL_FROM` uses verified Resend domain (not `@resend.dev`)
- [ ] `DATABASE_URL` uses `postgresql+asyncpg://` driver

### Infrastructure

- [ ] PostgreSQL 16 running and accessible
- [ ] Redis 7 running with password authentication
- [ ] HTTPS terminated at reverse proxy (Caddy or nginx)
- [ ] Reverse proxy forwards `X-Forwarded-For` (required for IP-based lockout)
- [ ] DNS record for API subdomain pointing to server

### Code

- [ ] Latest CI run on `main` is green
- [ ] All Alembic migrations reviewed
- [ ] Docker image builds without errors

## Deploy

```bash
cp .env.production.example .env
# Fill in all required values in .env

docker compose up -d --build
docker compose exec miransas-id-app ./scripts/migrate.sh up

# Verify
curl https://api.miransas.com/api/v1/health
curl https://api.miransas.com/api/v1/health/detailed
```

## Post-Deploy Verification

- [ ] `/api/v1/health` returns `{"status": "ok"}`
- [ ] `/api/v1/health/detailed` shows `database` and `redis` as `ok`
- [ ] Register → email delivered → verify-email flow works end-to-end
- [ ] Login → /me → refresh rotation works
- [ ] Logs are in JSON format (check with `docker compose logs miransas-id-app`)
- [ ] No secrets visible in logs

## Rollback

```bash
git checkout <previous-tag>
docker compose up -d --build
docker compose exec miransas-id-app ./scripts/migrate.sh down
```

## Operations

| Task | Command |
|------|---------|
| View logs | `docker compose logs -f miransas-id-app` |
| Migration status | `docker compose exec miransas-id-app ./scripts/migrate.sh current` |
| Run migrations | `docker compose exec miransas-id-app ./scripts/migrate.sh up` |
| Rollback one | `docker compose exec miransas-id-app ./scripts/migrate.sh down` |
| Restart app | `docker compose restart miransas-id-app` |

## Monitoring

- **Health endpoint:** integrate `/api/v1/health/detailed` with an uptime monitor (BetterStack, UptimeRobot)
- **Sentry:** errors and performance traces at sentry.io
- **Audit log:** `GET /api/v1/admin/audit-log` — all admin actions with actor, target, and IP
- **Failed logins:** `GET /api/v1/admin/login-attempts?success=false` — forensics log
