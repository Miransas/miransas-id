# Centralized SSO Authentication Server

A high-performance, secure, and scalable Centralized Single Sign-On (SSO) Authentication Server built with Rust. This service handles user authentication, authorization flows (OAuth 2.0 / OIDC), and dynamic UI rendering for multiple client applications (SaaS, Mobile, Gaming) from a single centralized endpoint.

## 🚀 Features

* **Blazing Fast & Memory Safe:** Built completely in Rust using the `axum` web framework and `tokio` asynchronous runtime.
* **Centralized Login & Whitelisting:** Single entry point for multiple clients (`client_id`) with secure redirect URI validation.
* **Dynamic UI & Theming:** Server-side HTML rendering via `Askama`. The login interface dynamically adapts its theme, logo, and colors based on the requesting client, all without a heavy JavaScript framework.
* **Zero-Dependency Frontend:** The UI uses pure CSS and Vanilla JS (with built-in dark/light mode memory) to ensure lightning-fast load times.
* **Secure Cryptography:** Password hashing via `argon2id` and secure JWT/Paseto generation.
* **Robust Database:** Asynchronous PostgreSQL interactions and compile-time checked queries using `sqlx`.

## 🛠️ Tech Stack

* **Language:** Rust
* **Web Framework:** Axum
* **Database & ORM:** PostgreSQL + SQLx
* **Template Engine:** Askama
* **Cryptography:** Argon2, JSON Web Tokens (JWT)
