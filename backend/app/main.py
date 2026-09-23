"""FastAPI application entrypoint for Relay backend."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.context import router as context_router
from app.api.contributions import router as contributions_router
from app.api.demo import router as demo_router
from app.api.health import router as health_router
from app.api.reasoning import router as reasoning_router
from app.api.retrieval import router as retrieval_router, get_active_provider
from app.config.settings import settings
from app.retrieval.moss import MossRetrievalProvider

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("relay")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("Starting Relay Backend [%s] in %s mode", settings.version, settings.environment)
    if settings.is_moss_configured:
        logger.info("Moss is configured with index '%s'. Initializing and warming index...", settings.moss_index_name)
        provider = get_active_provider()
        if isinstance(provider, MossRetrievalProvider):
            try:
                await provider.load()
                logger.info("Moss Retrieval Provider is READY and warm.")
            except Exception as e:
                logger.error("Failed to load Moss index on startup: %s", e)
    else:
        logger.info("Moss is unconfigured. Using Mock Retrieval Provider for local development.")
    yield
    logger.info("Shutting down Relay Backend.")


app = FastAPI(
    title="Relay API",
    description=(
        "Real-time decision-support copilot for field technicians. "
        "Built for YC Fall 2026 x Moss: The Zero Latency Builder Sprint."
    ),
    version=settings.version,
    lifespan=lifespan,
)

# CORS Middleware (configured for local development and future frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(demo_router)
app.include_router(retrieval_router)
app.include_router(context_router)
app.include_router(reasoning_router)
app.include_router(contributions_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service info and links."""
    return {
        "service": settings.service_name,
        "tagline": "Real-time AI decision-support copilot for field technicians",
        "version": settings.version,
        "phase": "Phase 6 - Technician Knowledge Contribution & Ingestion",
        "docs_url": "/docs",
        "health_check": "/health",
        "retrieval_health": "/api/retrieval/health",
        "demo_asset": "/api/demo/asset/ACX-420-017",
        "context_assemble": "/api/context/assemble",
        "reasoning_analyze": "/api/reasoning/analyze",
        "contributions": "/api/knowledge/contributions",
    }
