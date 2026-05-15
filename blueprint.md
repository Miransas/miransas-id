# MIRANSAS ID — COMPLETE TECHNICAL BLUEPRINT

Miransas ID is designed as a centralized authentication and identity infrastructure for the Miransas ecosystem. The project is not structured as a simple login/register API, but rather as a scalable ecosystem-level identity platform capable of supporting games, developer tools, launchers, cloud services, community systems, and future Miransas products under a unified account architecture.

The backend follows Clean Architecture principles to ensure scalability, maintainability, modularity, and production readiness.

---

# CORE ARCHITECTURE

The project structure is separated into clear architectural layers:

```txt
src/
├── core/
│   ├── config.py
│   └── security.py
│
├── models/
│   └── user.py
│
├── schemas/
│   └── auth.py
│
├── services/
│   └── auth_service.py
│
├── database/
│   └── session.py
│
├── api/
│   └── v1/
│       └── routes/
│
└── main.py
```

Each layer has a dedicated responsibility:

- `core/`
  Handles global configuration, environment management, JWT settings, and security utilities.

- `models/`
  Contains SQLModel database models and ORM structures.

- `schemas/`
  Responsible for request/response validation using Pydantic.

- `services/`
  Contains business logic such as authentication, password validation, rank management, and future ecosystem logic.

- `database/`
  Handles database engine initialization and session lifecycle management.

- `api/v1/`
  Contains versioned API endpoints and routers.

This separation allows the system to evolve into:
- microservices
- distributed services
- public APIs
- launcher backends
- game account systems
- mobile integrations

without requiring major architectural rewrites.

---

# SECURITY INFRASTRUCTURE

Miransas ID is designed with modern authentication and security standards in mind.

## Password Security

Passwords are never stored in plain text.

The system uses:
- Argon2 hashing algorithm

Argon2 provides:
- GPU attack resistance
- memory-hard security
- stronger modern password protection compared to legacy bcrypt implementations

---

## Authentication System

Authentication is based on:
- JWT (JSON Web Token)
- Stateless architecture

Advantages:
- scalable infrastructure
- serverless compatibility
- distributed deployment support
- horizontal scaling support

JWT tokens are signed using:
- HS256
- SECRET_KEY
- environment variable based configuration

---

## Planned Security Extensions

Future security layers include:
- refresh token rotation
- token revocation
- device session management
- suspicious login detection
- MFA / 2FA support
- OAuth integrations
- audit logging
- rate limiting
- security headers
- secret rotation

---

# USER ECOSYSTEM MODEL

Miransas ID is designed as a unified identity system across all Miransas projects.

Each user account may contain:
- username
- email
- password hash
- rank
- badges
- verification status
- activity state
- profile metadata

---

## Rank System

Current planned ranks:
- Novice
- Architect
- Elite
- Core Developer

This system allows the ecosystem to create:
- developer reputation
- contribution tracking
- community hierarchy
- progression systems

---

## Badge System

Badges are stored dynamically using JSON structures.

Potential future badges:
- Founder
- Beta Tester
- Contributor
- Verified Creator
- Early Supporter
- Core Member

The badge system can later integrate with:
- achievements
- activity feeds
- ecosystem rewards
- reputation systems

---

# DATABASE INFRASTRUCTURE

Miransas ID uses:
- PostgreSQL
- SQLModel
- SQLAlchemy
- Pydantic integration

The database layer is designed for:
- type safety
- ORM flexibility
- validation support
- production scalability

---

## Session Management

Database sessions are handled using dependency injection.

Each request:
- opens a safe database session
- performs operations
- automatically closes the connection

This ensures:
- safer transaction management
- reduced memory leaks
- better scalability

---

## Planned Database Improvements

Future improvements include:
- Alembic migrations
- UUIDv7 / ULID identifiers
- soft delete support
- audit tables
- indexing optimization
- query caching
- Redis integration

---

# API STRUCTURE

The backend follows a versioned API architecture:

```txt
/api/v1/
```

This allows:
- backwards compatibility
- safe future upgrades
- ecosystem API stability

Planned API systems:
- auth endpoints
- profile endpoints
- rank endpoints
- badge endpoints
- public profile APIs
- API key management
- developer APIs

---

# CI/CD PIPELINE

Miransas ID includes a modern CI/CD workflow using GitHub Actions.

Current pipeline responsibilities:
- lint checks
- automated tests
- validation
- environment consistency

The project uses:
- Ruff
- pytest
- Docker-based temporary PostgreSQL services during CI

---

# DEVELOPMENT ENVIRONMENT

Current development stack:
- Python 3.12+
- FastAPI
- SQLModel
- PostgreSQL
- Uvicorn

Environment isolation:
- `.venv`

Development runner:
```bash
uvicorn src.main:app --reload
```

---

# MISSING PRODUCTION SYSTEMS

The current architecture is strong, but several production-level systems are still required.

---

## Refresh Token Infrastructure

Required:
- short-lived access tokens
- refresh tokens
- token rotation
- revoke support

Without this:
- stolen JWT tokens remain dangerous

Potential implementation:
- Redis
- refresh token tables
- device tracking

---

## Rate Limiting

Critical for security.

Needed protection against:
- brute force attacks
- spam registrations
- bot abuse

Potential stack:
- SlowAPI
- Redis rate limiting

---

## Email Infrastructure

Required flows:
- email verification
- password reset
- resend verification
- cooldown systems

Potential providers:
- Resend
- Postmark
- SendGrid

---

## Monitoring & Observability

Production systems require:
- structured logging
- error monitoring
- tracing
- uptime monitoring

Potential tools:
- Sentry
- BetterStack
- OpenTelemetry

---

## Audit Logging

Important for ecosystem trust and moderation.

Events to log:
- login attempts
- password changes
- role changes
- badge rewards
- suspicious activity

---

# FRONTEND INTEGRATION

The backend is suitable for a dedicated frontend platform.

Recommended stack:
- Next.js
- TailwindCSS
- Framer Motion
- shadcn/ui
- TanStack Query
- Zustand

Potential frontend systems:
- dashboard
- public profiles
- ecosystem launcher
- account settings
- developer portal

---

# FUTURE ECOSYSTEM FEATURES

Miransas ID is positioned to evolve beyond authentication into a complete ecosystem platform.

---

## Unified Account System

One account may connect:
- BinBoi
- Lost Signal
- future games
- launcher systems
- cloud saves
- developer tools
- forums
- ecosystem dashboards

---

## Public Profiles

Inspired by:
- GitHub
- Steam
- Discord

Potential profile features:
- avatar
- banner
- activity feed
- achievements
- projects
- badges
- contribution stats

---

## Reputation System

Future metrics:
- contribution score
- ecosystem activity
- verified developer status
- creator reputation
- beta participation

---

## API Key Infrastructure

Developer ecosystem support:
- API key creation
- scoped permissions
- revocation
- analytics
- usage tracking

---

# BACKGROUND SERVICES

Future asynchronous systems:
- email sending
- analytics processing
- badge generation
- cleanup jobs
- notifications

Potential technologies:
- Celery
- Dramatiq
- Arq

---

# REDIS INTEGRATION

Redis will likely become a core infrastructure component.

Potential use cases:
- cache
- sessions
- rate limiting
- token revocation
- temporary verification storage

---

# ADVANCED SECURITY

Future security layers:
- CSP headers
- HSTS
- X-Frame-Options
- CSRF protection
- secret rotation
- RBAC permissions

Potential roles:
- admin
- moderator
- developer
- verified
- staff

---

# TESTING STRATEGY

Future test coverage should include:
- unit tests
- integration tests
- auth tests
- permission tests
- refresh token tests
- JWT expiry validation
- invalid token testing

---

# EVENT-DRIVEN ARCHITECTURE

Future event system examples:

```txt
UserRegistered
BadgeEarned
RankUpdated
DeveloperVerified
```

This architecture can power:
- notifications
- analytics
- achievements
- activity feeds
- automation systems

---

# LONG-TERM VISION

Miransas ID is not intended to remain a simple authentication API.

The long-term goal is a scalable identity ecosystem capable of serving:
- games
- launchers
- developer platforms
- cloud services
- community systems
- achievement networks
- public developer ecosystems

The architecture direction combines ideas similar to:
- Steam Account
- Riot Account
- GitHub
- Discord Developer Platform

while remaining fully customizable under the Miransas ecosystem.

---

# CURRENT PROJECT STATUS

Current maturity level:
- strong backend foundation
- scalable architecture
- modern security baseline
- ecosystem-oriented design

Still missing:
- production hardening
- auth maturity systems
- observability
- advanced infrastructure
- frontend integration
- ecosystem layer

However, the project foundation is significantly above the average early-stage authentication backend and already follows patterns used in scalable production systems.

---

# ROADMAP

## Phase 1
- Complete register/login routes
- Finalize JWT flow
- Setup Alembic migrations

## Phase 2
- Refresh token infrastructure
- Email verification
- Password reset
- Rate limiting

## Phase 3
- Redis integration
- Audit logs
- Monitoring systems
- Session tracking

## Phase 4
- Frontend integration
- Public profiles
- Ecosystem dashboard

## Phase 5
- OAuth integrations
- API keys
- Developer platform
- Reputation systems

---

# FINAL SUMMARY

Miransas ID already shows the foundation of a serious ecosystem backend rather than a basic hobby authentication API.

The strongest aspect of the project is that the system is being designed around:
- scalability
- ecosystem integration
- modularity
- future expansion

from the very beginning.

With proper production hardening and ecosystem features, Miransas ID has the potential to evolve into a complete unified identity and developer ecosystem platform for all future Miransas services and products.