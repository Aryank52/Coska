"""Health check endpoints for COSKA subsystems."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

from app.config import get_settings
from app.services.providers import get_provider
from app.services.tavily import get_tavily_client
from app.tools.sandbox import SandboxEngine

logger = structlog.get_logger()
router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str = "coska"
    version: str = "0.1.0"


class AIHealthResponse(BaseModel):
    status: str
    provider: str
    model: str
    reachable: bool
    authenticated: bool
    model_available: bool
    details: Dict[str, Any] = {}


class TavilyHealthResponse(BaseModel):
    status: str
    configured: bool
    connected: bool
    details: Dict[str, Any] = {}


class SandboxHealthResponse(BaseModel):
    status: str
    provider: str
    available: bool
    mode: str
    details: Dict[str, Any] = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    return HealthResponse(status="healthy")


@router.get("/health/ai", response_model=AIHealthResponse)
async def ai_health_check():
    """AI provider health check."""
    settings = get_settings()
    provider = get_provider()
    
    try:
        info = await provider.health_check()
        is_healthy = info.reachable and info.authenticated
        return AIHealthResponse(
            status="healthy" if is_healthy else "degraded",
            provider=info.name,
            model=info.model,
            reachable=info.reachable,
            authenticated=info.authenticated,
            model_available=info.model_available,
            details={
                "base_url": info.base_url,
                "inference_test": info.inference_test,
                "error": info.error
            }
        )
    except Exception as e:
        logger.warning("ai_health_check_failed", error=str(e))
        return AIHealthResponse(
            status="unhealthy",
            provider=settings.ai_provider,
            model=settings.nebius_model,
            reachable=False,
            authenticated=False,
            model_available=False,
            details={"error": str(e)}
        )


@router.get("/health/tavily", response_model=TavilyHealthResponse)
async def tavily_health_check():
    """Tavily web research service health check."""
    tavily = get_tavily_client()
    configured = tavily.is_configured
    connected = False
    
    if configured:
        connected = await tavily.health_check()

    return TavilyHealthResponse(
        status="healthy" if connected else ("unconfigured" if not configured else "degraded"),
        configured=configured,
        connected=connected,
        details={
            "status_code": "TAVILY_READY" if connected else ("TAVILY_NOT_CONFIGURED" if not configured else "TAVILY_UNAVAILABLE")
        }
    )


@router.get("/health/sandbox", response_model=SandboxHealthResponse)
async def sandbox_health_check():
    """Sandbox execution subsystem health check."""
    settings = get_settings()
    sandbox = SandboxEngine()
    available = sandbox.is_available()

    return SandboxHealthResponse(
        status="healthy" if available else "degraded",
        provider=sandbox.provider_name,
        available=available,
        mode=settings.sandbox_mode,
        details={
            "timeout": settings.sandbox_timeout,
            "memory_limit": settings.sandbox_memory_limit,
            "cpu_limit": settings.sandbox_cpu_limit,
            "is_docker": sandbox.provider_name == "docker"
        }
    )
