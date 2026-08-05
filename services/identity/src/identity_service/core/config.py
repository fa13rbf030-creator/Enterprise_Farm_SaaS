from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="IDENTITY_",
        extra="ignore",
    )

    service_name: str = "identity"
    environment: str = "development"

    database_url: str = (
        "postgresql+asyncpg://saas_user:saas_password"
        "@localhost:5432/enterprise_farm_db"
    )

    jwt_secret: str = Field(
        default="development-secret-change-before-production-123456",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_days: int = Field(default=30, ge=1, le=365)
    token_issuer: str = "enterprise-farm-identity"


@lru_cache
def get_settings() -> Settings:
    return Settings()
