from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Miransas ID"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str # Vercel'den gelecek
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Gün
    
    # Database
    DATABASE_URL: str # Vercel/Neon/Postgres URL

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()