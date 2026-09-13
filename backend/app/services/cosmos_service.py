"""
Azure Cosmos DB service layer: job + content persistence.
Uses the SQL (Core) API via azure-cosmos SDK.
"""
from datetime import datetime
from typing import Any, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class CosmosService:
    """Thin async-friendly wrapper around Cosmos DB for job/content documents."""

    def __init__(self) -> None:
        self._client: Optional[CosmosClient] = None
        self._jobs_container = None
        self._content_container = None

    def _ensure_connected(self) -> None:
        if self._client is not None and self._jobs_container is not None:
            return
        if not settings.cosmos_endpoint or not settings.cosmos_key:
            raise RuntimeError("Cosmos DB is not configured (COSMOS_ENDPOINT / COSMOS_KEY missing).")

        try:
            client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
            database = client.create_database_if_not_exists(id=settings.cosmos_database)
            jobs_container = database.create_container_if_not_exists(
                id=settings.cosmos_container_jobs,
                partition_key=PartitionKey(path=settings.cosmos_partition_key)
            )
            content_container = database.create_container_if_not_exists(
                id=settings.cosmos_container_content,
                partition_key=PartitionKey(path=settings.cosmos_partition_key)
            )
        except Exception:
            # Don't cache a half-initialized client — surface the real error
            # and let the next call retry from scratch instead of masking it.
            self._client = None
            self._jobs_container = None
            self._content_container = None
            raise

        self._client = client
        self._jobs_container = jobs_container
        self._content_container = content_container
        logger.info("cosmos_connected", database=settings.cosmos_database)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def upsert_job(self, job: dict[str, Any]) -> dict[str, Any]:
        self._ensure_connected()
        job["updated_at"] = datetime.utcnow().isoformat()
        job.setdefault("tenant_id", "default")
        self._jobs_container.upsert_item(job)
        return job

    def get_job(self, job_id: str, tenant_id: str = "default") -> Optional[dict[str, Any]]:
        self._ensure_connected()
        try:
            return self._jobs_container.read_item(item=job_id, partition_key=tenant_id)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def list_jobs(self, tenant_id: str = "default", limit: int = 50) -> list[dict[str, Any]]:
        self._ensure_connected()
        query = "SELECT TOP @limit * FROM c WHERE c.tenant_id = @tenant ORDER BY c.created_at DESC"
        items = self._jobs_container.query_items(
            query=query,
            parameters=[{"name": "@limit", "value": limit}, {"name": "@tenant", "value": tenant_id}],
            enable_cross_partition_query=True,
        )
        return list(items)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def save_content(self, content_doc: dict[str, Any]) -> dict[str, Any]:
        self._ensure_connected()
        content_doc.setdefault("tenant_id", "default")
        self._content_container.upsert_item(content_doc)
        return content_doc


# Module-level singleton (safe: SDK client is thread-safe for typical usage)
cosmos_service = CosmosService()