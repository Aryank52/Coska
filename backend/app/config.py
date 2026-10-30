"""Configuration management for COSKA backend."""
import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Get project root (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Nebius Token Factory
    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.tokenfactory.us-central1.nebius.com/v1/"
    nebius_model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    
    # Tavily
    tavily_api_key: str = ""
    
    # Database
    database_url: str = "sqlite:///./coska.db"
    
    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Frontend
    vite_api_url: str = "http://localhost:8000"
    frontend_origin: str = "http://localhost:5173"
    
    # Sandbox
    sandbox_mode: str = "local"  # local, docker, auto
    sandbox_timeout: int = 300
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0
    
    # AI Provider
    ai_provider: str = "mock"  # auto, mock, nebius
    
    # Logging & Observability
    log_level: str = "INFO"
    
    # Agent Safety Limits
    max_agent_steps: int = 40
    max_tool_calls: int = 25
    max_retries: int = 3
    max_investigation_time: int = 300
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()