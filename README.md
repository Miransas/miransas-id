# README.md

```markdown
# Miransas ID

Miransas ID is a modern identity and authentication infrastructure built for the Miransas ecosystem.

The project is designed as a scalable backend foundation capable of supporting:
- games
- launchers
- developer platforms
- cloud services
- public APIs
- community systems
- future Miransas products

Instead of being a simple login/register API, Miransas ID is structured as a centralized ecosystem identity platform.

---

# Features

- Modern FastAPI backend
- Clean Architecture structure
- JWT Authentication
- Argon2 password hashing
- PostgreSQL support
- SQLModel integration
- Pydantic validation
- CI/CD with GitHub Actions
- Environment-based configuration
- Versioned API structure
- Ecosystem-ready account model
- Rank & badge infrastructure

---

# Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLModel / SQLAlchemy |
| Validation | Pydantic |
| Authentication | JWT |
| Password Hashing | Argon2 |
| CI/CD | GitHub Actions |
| Linting | Ruff |
| Runtime | Uvicorn |

---

# Project Structure

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

---

# Architecture Philosophy

Miransas ID follows Clean Architecture principles.

The project separates:
- business logic
- validation
- database models
- API layers
- security systems

This allows the backend to remain:
- scalable
- maintainable
- modular
- production-ready

---

# Security

Miransas ID uses modern authentication and security practices.

## Password Security

Passwords are hashed using:
- Argon2

Passwords are never stored in plain text.

---

## Authentication

Authentication is based on:
- JWT (JSON Web Token)
- Stateless architecture

Tokens are signed using:
- HS256
- SECRET_KEY
- environment variables

---

# Planned Features

The project is actively evolving.

Planned systems include:
- Refresh token rotation
- OAuth providers
- MFA / 2FA
- Session management
- Redis integration
- Audit logs
- Rate limiting
- Public profiles
- API keys
- Developer dashboard
- Reputation system
- Ecosystem launcher integration

---

# Ecosystem Vision

Miransas ID is intended to become the unified account infrastructure for all Miransas services and products.

Future ecosystem integrations may include:
- BinBoi
- Lost Signal
- future games
- cloud services
- launchers
- developer platforms
- community systems

The project aims to provide a single identity layer across the entire ecosystem.

---

# Development Setup

## Clone Repository

```bash
git clone https://github.com/Miransas/miransas-id.git
cd miransas-id
```

---

## Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Development Server

```bash
uvicorn src.main:app --reload
```

---

# API

Current API structure:

```txt
/api/v1/
```

Planned endpoints:
- /register
- /login
- /refresh
- /me
- /profile
- /badges
- /ranks

---

# CI/CD

GitHub Actions is used for:
- lint checks
- automated testing
- validation
- workflow automation

---

# Documentation

Future documentation plans:

```txt
docs/
├── blueprint.md
├── architecture.md
├── auth-flow.md
├── database.md
├── roadmap.md
└── api-reference.md
```

---

# Current Status

Current project state:
- Backend foundation established
- Security layer initialized
- Database architecture prepared
- Authentication infrastructure in progress

The project is still under active development.

---

# Contributing

Contributions, ideas, and feedback are welcome.

Future contribution guidelines will be added as the project evolves.

---

# License

This project is licensed under the MIT License.

See the LICENSE file for more information.

---

# Author

Created and maintained by Miransas.
```

---


