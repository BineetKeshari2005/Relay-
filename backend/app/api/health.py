"""Health check and service status endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config.settings import settings

router = APIRouter(tags=["Health & Status"])


class SimpleHealthResponse(BaseModel):
    status: str = Field("ok", description="Liveness status")
    service: str = Field(..., description="Service identifier")


class DetailedHealthResponse(BaseModel):
    status: str = Field("ok", description="Overall health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    moss_configured: bool = Field(..., description="Whether Moss credentials are set")
    llm_provider: str = Field(..., description="Configured LLM provider")


class VersionResponse(BaseModel):
    version: str = Field(..., description="Current version string")
    service: str = Field(..., description="Service name")
    phase: str = Field("Phase 1 - Foundation", description="Project development phase")


@router.get("/health", response_model=SimpleHealthResponse, summary="Simple Liveness Check")
async def get_health_root() -> SimpleHealthResponse:
    """Basic health check used by load balancers and container monitors."""
    return SimpleHealthResponse(status="ok", service=settings.service_name)


@router.get("/api/health", response_model=DetailedHealthResponse, summary="Detailed System Health")
async def get_api_health() -> DetailedHealthResponse:
    """Detailed health check returning provider configuration states."""
    return DetailedHealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        moss_configured=settings.is_moss_configured,
        llm_provider=settings.llm_provider,
    )


@router.get("/api/version", response_model=VersionResponse, summary="API Version Info")
async def get_version() -> VersionResponse:
    """Returns application version and active development phase metadata."""
    return VersionResponse(
        version=settings.version,
        service=settings.service_name,
        phase="Phase 1 - Foundation",
    )
