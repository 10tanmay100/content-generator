"""Liveness/readiness endpoints for Azure Container Apps probes."""
from fastapi import APIRouter

from app.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(environment=settings.environment)


@router.get("/health/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    """
    Readiness probe. Extend this to ping Cosmos DB / Azure AI Search
    if you want deep health checks before routing traffic.
    """
    return HealthResponse(environment=settings.environment)
