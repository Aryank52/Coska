"""COSKA FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.api import health, incidents, investigations, verification


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("coska_starting", env=settings.app_env)
    yield
    logger.info("coska_shutting_down")


app = FastAPI(
    title="COSKA",
    description="Autonomous Incident Intelligence & Verified Recovery",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(incidents.router, prefix="/api", tags=["incidents"])
app.include_router(investigations.router, prefix="/api", tags=["investigations"])
app.include_router(verification.router, prefix="/api", tags=["verification"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "COSKA",
        "tagline": "Autonomous Incident Intelligence & Verified Recovery",
        "version": "0.1.0",
        "status": "operational"
    }