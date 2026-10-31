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
    
    # AI Provider
    ai_provider: str = "mock"  # mock, local, openai_compatible, auto
    ai_model: str = "coska-deterministic-mock"
    
    # OpenAI-compatible provider (OpenAI, vLLM, TGI, etc.)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1/"
    openai_model: str = "gpt-4o"
    
    # Local LLM (Ollama, llama.cpp, LM Studio, etc.)
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "llama3.1:8b"
    local_llm_api_key: str = "ollama"
    
    # Tavily (optional - for external web research)
    tavily_api_key: str = ""
    tavily_enabled: bool = False
    
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