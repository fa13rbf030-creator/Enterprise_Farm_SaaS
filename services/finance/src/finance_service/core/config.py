from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FINANCE_",
        extra="ignore",
    )

    service_name: str = "finance"
    environment: str = "development"

    database_url: str = (
        "postgresql+asyncpg://saas_user:saas_password"
        "@localhost:5432/enterprise_farm_db"
    )

    base_currency: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    decimal_places: int = Field(
        default=2,
        ge=0,
        le=6,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
