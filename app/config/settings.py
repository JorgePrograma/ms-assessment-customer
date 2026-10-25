from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Customers API"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://customers:customers@localhost:5432/customers"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    cors_origins: list[str] = []
    cors_origin_regex: str | None = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"


@lru_cache
def get_settings() -> Settings:
    return Settings()
