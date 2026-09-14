"""Content generation endpoints: kick off crew jobs and fetch results."""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, status
"""Content generation endpoints: kick off crew jobs and fetch results."""
import asyncio
from datetime import datetime
from uuid import uuid4
from app.api.deps import get_cosmos
from app.core.exceptions import CrewExecutionError, JobNotFoundError
from app.core.logging import get_logger
from app.core.security import verify_api_token
from app.crew.content_crew import ContentCrew
from app.models.schemas import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    JobRecord,
    JobStatus,
)
from app.services.cosmos_service import CosmosService

router = APIRouter(prefix="/content", tags=["content"])
logger = get_logger(__name__)


def _run_crew_job(job_id: str, request: ContentGenerationRequest, cosmos: CosmosService) -> None:
    """Background worker: executes the CrewAI pipeline and persists the result."""
    try:
        cosmos.upsert_job(
            {
                "id": job_id,
                "tenant_id": request.tenant_id,
                "topic": request.topic,
                "content_format": request.content_format.value,
                "status": JobStatus.RESEARCHING.value,
                "request": request.model_dump(mode="json"),
            }
        )

        crew = ContentCrew(request)
        result = crew.run()

        cosmos.upsert_job(
            {
                "id": job_id,
                "tenant_id": request.tenant_id,
                "topic": request.topic,
                "content_format": request.content_format.value,
                "status": JobStatus.COMPLETED.value,
                "request": request.model_dump(mode="json"),
                "result": result,
            }
        )
        cosmos.save_content({"id": str(uuid4()), "tenant_id": request.tenant_id, "job_id": job_id, **result})
        logger.info("job_completed", job_id=job_id)

    except Exception as exc:
        logger.error("job_failed", job_id=job_id, error=str(exc), exc_info=True)
        cosmos.upsert_job(
            {
                "id": job_id,
                "tenant_id": request.tenant_id,
                "topic": request.topic,
                "content_format": request.content_format.value,
                "status": JobStatus.FAILED.value,
                "request": request.model_dump(mode="json"),
                "error": str(exc),
            }
        )


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_token)],
)
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    cosmos: CosmosService = Depends(get_cosmos),
) -> ContentGenerationResponse:
    """
    Kick off the CrewAI content pipeline asynchronously. Poll GET /jobs/{job_id}
    for status/result. This keeps the API responsive since a full crew run
    (research -> write -> edit -> SEO -> image -> social) can take 30-120s+.
    """
    job_id = str(uuid4())
    cosmos.upsert_job(
        {
            "id": job_id,
            "tenant_id": request.tenant_id,
            "topic": request.topic,
            "content_format": request.content_format.value,
            "status": JobStatus.PENDING.value,
            "request": request.model_dump(mode="json"),
            "created_at": datetime.utcnow().isoformat(),
        }
    )
    background_tasks.add_task(_run_crew_job, job_id, request, cosmos)
    logger.info("job_queued", job_id=job_id, topic=request.topic)
    return ContentGenerationResponse(job_id=job_id, status=JobStatus.PENDING)


@router.post(
    "/generate/sync",
    dependencies=[Depends(verify_api_token)],
)
async def generate_content_sync(request: ContentGenerationRequest) -> dict:
    """
    Synchronous variant — runs the crew inline and returns the full result.
    Useful for local testing/demos; NOT recommended behind a short-timeout gateway in prod.
    """
    try:
        crew = ContentCrew(request)
        result = await asyncio.to_thread(crew.run)
        return {"status": JobStatus.COMPLETED.value, "result": result}
    except Exception as exc:
        logger.error("sync_generation_failed", error=str(exc), exc_info=True)
        raise CrewExecutionError("Content generation failed", details={"error": str(exc)}) from exc
