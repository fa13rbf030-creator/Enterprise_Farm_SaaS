from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "procurement"
    environment: str = "development"

    jwt_secret: str = (
        "development-secret-change-before-production-123456"
    )
    jwt_algorithm: str = "HS256"
    token_issuer: str = "enterprise-farm-identity"

    database_url: str = (
        "postgresql+asyncpg://saas_user:saas_password"
        "@localhost:5432/enterprise_farm_db"
    )

    model_config = SettingsConfigDict(
        env_prefix="PROCUREMENT_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
