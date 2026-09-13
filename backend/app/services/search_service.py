"""
Azure AI Search service: index management + hybrid (vector + keyword) search
for retrieving past content and supporting the Research Agent's RAG lookups.
"""
from typing import Any, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

VECTOR_DIM = 384  # matches a small sentence-embedding model; adjust if you swap embedders


class SearchService:
    def __init__(self) -> None:
        self._search_client: Optional[SearchClient] = None
        self._index_client: Optional[SearchIndexClient] = None

    def _credential(self) -> AzureKeyCredential:
        if not settings.azure_search_api_key:
            raise RuntimeError("AZURE_SEARCH_API_KEY is not configured.")
        return AzureKeyCredential(settings.azure_search_api_key)

    def _get_index_client(self) -> SearchIndexClient:
        if self._index_client is None:
            self._index_client = SearchIndexClient(settings.azure_search_endpoint, self._credential())
        return self._index_client

    def _get_search_client(self) -> SearchClient:
        if self._search_client is None:
            self._search_client = SearchClient(
                settings.azure_search_endpoint, settings.azure_search_index, self._credential()
            )
        return self._search_client

    def ensure_index(self) -> None:
        """Idempotently create the vector + semantic search index."""
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="tenant_id", type=SearchFieldDataType.String, filterable=True),
            SearchField(name="title", type=SearchFieldDataType.String, searchable=True),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
            SimpleField(name="content_format", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="created_at", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=VECTOR_DIM,
                vector_search_profile_name="default-vector-profile",
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
            profiles=[VectorSearchProfile(name="default-vector-profile", algorithm_configuration_name="hnsw-config")],
        )

        semantic_search = SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name="default-semantic-config",
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="title"),
                        content_fields=[SemanticField(field_name="content")],
                    ),
                )
            ]
        )

        index = SearchIndex(
            name=settings.azure_search_index,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search,
        )
        self._get_index_client().create_or_update_index(index)
        logger.info("search_index_ready", index=settings.azure_search_index)

    def index_content(self, doc: dict[str, Any]) -> None:
        self._get_search_client().upload_documents(documents=[doc])

    def search(self, query: str, top: int = 5, tenant_id: Optional[str] = None) -> list[dict[str, Any]]:
        filter_expr = f"tenant_id eq '{tenant_id}'" if tenant_id else None
        results = self._get_search_client().search(
            search_text=query,
            top=top,
            filter=filter_expr,
            query_type="semantic",
            semantic_configuration_name="default-semantic-config",
        )
        return [dict(r) for r in results]


search_service = SearchService()
