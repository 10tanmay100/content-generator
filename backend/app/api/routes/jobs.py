"""Job status/history endpoints backed by Cosmos DB."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_cosmos
from app.core.exceptions import JobNotFoundError
from app.core.security import verify_api_token
from app.models.schemas import JobRecord
from app.services.cosmos_service import CosmosService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", dependencies=[Depends(verify_api_token)])
async def get_job(job_id: str, tenant_id: str = Query(default="default"), cosmos: CosmosService = Depends(get_cosmos)) -> dict:
    job = cosmos.get_job(job_id, tenant_id)
    if not job:
        raise JobNotFoundError(job_id)
    return job


@router.get("", dependencies=[Depends(verify_api_token)])
async def list_jobs(tenant_id: str = Query(default="default"), limit: int = Query(default=50, le=200), cosmos: CosmosService = Depends(get_cosmos)) -> list[dict]:
    return cosmos.list_jobs(tenant_id=tenant_id, limit=limit)
