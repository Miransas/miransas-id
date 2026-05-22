import warnings
from typing import List, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET = "change_me_in_production_environment"


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    PROJECT_NAME: str = "Miransas ID"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = _DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_ISSUER: str = "miransas-id"
    JWT_AUDIENCE: str = "miransas-ecosystem"

    ARGON2_MEMORY_COST: int = 65536  # 64 MiB
    ARGON2_TIME_COST: int = 3
    ARGON2_PARALLELISM: int = 4

    CORS_ORIGINS: List[str] = ["*"]
    DATABASE_URL: str = "sqlite+aiosqlite:///./miransas_id.db"

    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_ENABLED: bool = True

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"
    EMAIL_FROM_NAME: str = "Miransas ID"
    APP_FRONTEND_URL: str = "http://localhost:3000"

    # Token TTLs
    EMAIL_VERIFICATION_TTL_SECONDS: int = 24 * 60 * 60  # 24 hours
    PASSWORD_RESET_TTL_SECONDS: int = 60 * 60  # 1 hour

    # Sentry
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = ""  # defaults to ENVIRONMENT when empty
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _reject_unsafe_production_config(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == _DEFAULT_SECRET:
                raise ValueError(
                    "SECRET_KEY must not be the default value in production. "
                    "Generate a strong random key and set it via environment variable."
                )
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "CORS_ORIGINS must not contain '*' in production. "
                    "Set an explicit list of allowed origins."
                )
            if not self.RESEND_API_KEY:
                raise ValueError(
                    "RESEND_API_KEY must be set in production."
                )
            if "@resend.dev" in self.EMAIL_FROM:
                raise ValueError(
                    "EMAIL_FROM must use a verified domain in production, not @resend.dev."
                )
            if "localhost" in self.APP_FRONTEND_URL:
                raise ValueError(
                    "APP_FRONTEND_URL must not be localhost in production."
                )
            if not self.SENTRY_DSN:
                warnings.warn(
                    "SENTRY_DSN is not set in production. "
                    "Error tracking will be disabled.",
                    stacklevel=2,
                )
        return self


settings = Settings()
