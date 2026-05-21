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
        return self


settings = Settings()
