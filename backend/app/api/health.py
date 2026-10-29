"""Health check endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import structlog

from app.config import get_settings
from app.services.nebius import NebiusClient
from app.services.tavily import TavilyClient

logger = structlog.get_logger()
router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str = "coska"
    version: str = "0.1.0"


class AIHealthResponse(BaseModel):
    status: str
    nebius_connected: bool
    nebius_model: str
    tavily_connected: bool
    details: dict = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    return HealthResponse(status="healthy")


@router.get("/health/ai", response_model=AIHealthResponse)
async def ai_health_check(
    nebius: NebiusClient = Depends(),
    tavily: TavilyClient = Depends()
):
    """AI provider health check."""
    nebius_ok = False
    tavily_ok = False
    details = {}
    
    # Check Nebius
    try:
        nebius_ok = await nebius.health_check()
        details["nebius"] = "connected" if nebius_ok else "disconnected"
    except Exception as e:
        logger.warning("nebius_health_check_failed", error=str(e))
        details["nebius"] = f"error: {str(e)}"
    
    # Check Tavily
    try:
        tavily_ok = await tavily.health_check()
        details["tavily"] = "connected" if tavily_ok else "disconnected"
    except Exception as e:
        logger.warning("tavily_health_check_failed", error=str(e))
        details["tavily"] = f"error: {str(e)}"
    
    return AIHealthResponse(
        status="healthy" if (nebius_ok and tavily_ok) else "degraded",
        nebius_connected=nebius_ok,
        nebius_model=get_settings().nebius_model,
        tavily_connected=tavily_ok,
        details=details
    )