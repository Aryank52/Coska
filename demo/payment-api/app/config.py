"""Configuration for Payment API."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    db_pool_size: int = 5  # INTENTIONALLY LOW - causes pool exhaustion
    db_pool_timeout: int = 5
    database_url: str = "sqlite+aiosqlite:///./payments.db"
    
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    app_env: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()