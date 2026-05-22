# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Miransas ID, **do not open a public GitHub issue**.

Email: **security@miransas.com**

Include:
- A description of the issue
- Steps to reproduce
- Potential impact

You should receive an acknowledgment within 48 hours.

## Security Guarantees

Miransas ID is the central authentication provider for the Miransas ecosystem. The following security properties are enforced and tested.

### Authentication

- Passwords are hashed with **Argon2id** (memory: 64 MiB, time cost: 3, parallelism: 4, 256-bit output).
- JWT tokens use HS256 and enforce `iat`, `nbf`, `exp`, `iss`, `aud`, `sub`, and `type` claims on every decode.
- Failed login always runs a full Argon2 verification (dummy hash) to normalize response timing.

### Refresh Token Rotation

- Refresh tokens are 32-byte random, stored as SHA-256 hashes in the database — never in plaintext.
- Every successful refresh rotates the token; the old token is immediately invalidated.
- **Reuse detection:** presenting a previously-rotated token triggers revocation of the entire token family (all sessions on that device lose access).

### Brute-Force Protection

- Login attempts are rate-limited at 10/min per IP via Redis sliding window.
- Username-based lockout: 5 failures → 15-min lockout, escalating to 1 hour at 10 and 24 hours at 20.
- IP-based lockout: 20 failures from a single IP → 1-hour ban; 100 failures → 24-hour ban.
- Lockout state is never leaked — generic "Invalid credentials" in all cases.

### User Enumeration Protection

- `/auth/forgot-password` returns an identical generic response regardless of whether the email exists.
- `/auth/register` returns a generic error on duplicate username or email.
- `/auth/login` timing is normalized via dummy Argon2 for non-existent accounts.

### Email Verification & Password Reset

- Tokens are 32-byte cryptographic random (`secrets.token_urlsafe(32)`).
- Redis stores only the SHA-256 hash of the token — the plain token appears only in the email.
- Tokens are single-use: atomically consumed (GET + DEL pipeline) on first use.
- TTLs: 24 hours for verification, 1 hour for password reset.
- Successful password reset revokes all active sessions and deletes any outstanding reset and verification tokens for the user.
- Forgot-password is rate-limited at 5/hour per IP and 3/hour per email address.

### Admin Actions

- Rank changes, status changes, and badge assignments are written to an immutable audit log.
- Core Developers cannot modify their own rank or active status via admin endpoints.
- At least one active Core Developer is always preserved.
- Disabling a user immediately revokes all their active sessions in the same database transaction.

### Production Hardening

- App refuses to start with default `SECRET_KEY` or wildcard `CORS_ORIGINS` when `ENVIRONMENT=production`.
- Container runs as non-root user (uid 1000).
- Sensitive fields (`password`, `token`, `authorization`, etc.) are scrubbed from Sentry events before transmission.
- JSON structured logs in production; no secrets or PII in log output.

## Disclosure Timeline

| Day | Action |
|-----|--------|
| 0 | Report received |
| 1–2 | Acknowledgment sent |
| 3–30 | Investigation and fix |
| 30–90 | Fix deployed, advisory published |
