# 🆔 Miransas ID (Central Authentication Node)

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

**Miransas ID** is the centralized identity and access management (IAM) service for the **Miransas Ecosystem**. It provides a secure, unified authentication layer for high-performance projects including *binboi*, *miransas-chess*, and *Worktio*.

Built with a focus on performance and security, Miransas ID ensures that every "node" in the ecosystem can verify users with minimal latency and maximum safety.

---

## 🚀 Features

* **Unified Identity:** One account to access all Miransas software and services.
* **Secure by Design:** Password hashing using **Argon2** and stateless authentication via **JWT**.
* **Ecosystem Integration:** Built-in support for **Miransas Ranks** (Novice to Elite) and **Achievement Badges**.
* **Performance:** Powered by **FastAPI** and **SQLModel** for high-concurrency handling.
* **Scalability:** Microservice-ready architecture designed for cloud deployment.

---

## 📂 Project Structure & Roadmap

The project follows **Clean Architecture** principles to ensure maintainability and separation of concerns.

```text
miransas-id/
├── src/
│   ├── main.py             # Application Entry Point
│   ├── api/                # Route Handlers & Dependencies
│   ├── core/               # Security (JWT/Hash) & Configuration
│   ├── models/             # Database Models (SQLModel)
│   ├── schemas/            # Data Validation (Pydantic)
│   ├── services/           # Business Logic
│   └── database/           # Session & Engine Management
├── tests/                  # Automated Test Suite
└── .github/workflows/      # CI/CD Pipelines

Anladım usta, hepsini tek bir profesyonel README.md dosyası içinde, projenin tüm detaylarını, klasör yapısını ve kurulum rehberini kapsayacak şekilde birleştirdim. GitHub profilinde tam bir "Engineered by Miransas" duruşu sergileyecek.

İşte projenin ana dizinine yapıştıracağın o dosya:

Markdown
# 🆔 Miransas ID (Central Authentication Node)

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

**Miransas ID** is the centralized identity and access management (IAM) service for the **Miransas Ecosystem**. It provides a secure, unified authentication layer for high-performance projects including *binboi*, *miransas-chess*, and *Worktio*.

Built with a focus on performance and security, Miransas ID ensures that every "node" in the ecosystem can verify users with minimal latency and maximum safety.

---

## 🚀 Features

* **Unified Identity:** One account to access all Miransas software and services.
* **Secure by Design:** Password hashing using **Argon2** and stateless authentication via **JWT**.
* **Ecosystem Integration:** Built-in support for **Miransas Ranks** (Novice to Elite) and **Achievement Badges**.
* **Performance:** Powered by **FastAPI** and **SQLModel** for high-concurrency handling.
* **Scalability:** Microservice-ready architecture designed for cloud deployment.

---

## 📂 Project Structure & Roadmap

The project follows **Clean Architecture** principles to ensure maintainability and separation of concerns.

```text
miransas-id/
├── src/
│   ├── main.py             # Application Entry Point
│   ├── api/                # Route Handlers & Dependencies
│   ├── core/               # Security (JWT/Hash) & Configuration
│   ├── models/             # Database Models (SQLModel)
│   ├── schemas/            # Data Validation (Pydantic)
│   ├── services/           # Business Logic
│   └── database/           # Session & Engine Management
├── tests/                  # Automated Test Suite
└── .github/workflows/      # CI/CD Pipelines
🛠️ Tech Stack
Framework: FastAPI

ORM/Models: SQLModel (SQLAlchemy + Pydantic)

Database: PostgreSQL (Optimized for Neon/Vercel)

Security: Argon2-cffi & python-jose (JWT)

Environment: Docker & Vercel

⚙️ Quick Start
1. Prerequisites
Python 3.12+ (Homebrew version recommended for macOS)

PostgreSQL instance

2. Installation & Setup
Bash
# Clone the repository
git clone [https://github.com/sardorazimov/miransas-id.git](https://github.com/sardorazimov/miransas-id.git)
cd miransas-id

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
3. Environment Configuration
Copy .env.example to .env and fill in your secrets (ensure .env is ignored by git):

Bash
PROJECT_NAME="Miransas ID"
SECRET_KEY="your-generated-hex-key"
DATABASE_URL="your-postgres-connection-string"
4. Run the Engine
Bash
export PYTHONPATH=$PYTHONPATH:.
uvicorn src.main:app --reload
Check the live documentation at: http://127.0.0.1:8000/docs

🛡️ License & Contributions
Licensed under the MIT License. As an open-source project under the Miransas umbrella, contributions are welcome via Pull Requests.

🌌 Developed by Miransas
Designed for the next generation of software automation.
Lead Architect: Sardor Azimov