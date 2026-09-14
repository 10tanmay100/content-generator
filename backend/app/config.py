"""
Centralized application configuration using pydantic-settings.
All values are read from environment variables / .env file.
Never hardcode secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    environment: str = Field(default="development", alias="ENVIRONMENT")
    app_name: str = Field(default="content-creation-pipeline", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Ollama (local LLM)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2:latest", alias="OLLAMA_MODEL")
    ollama_model_reasoning: str = Field(default="deepseek-r1:8b", alias="OLLAMA_MODEL_REASONING")
    ollama_temperature: float = Field(default=0.6, alias="OLLAMA_TEMPERATURE")

    # Cosmos DB
    cosmos_endpoint: str = Field(default="", alias="COSMOS_ENDPOINT")
    cosmos_key: str = Field(default="", alias="COSMOS_KEY")
    cosmos_database: str = Field(default="content_pipeline_db", alias="COSMOS_DATABASE")
    cosmos_container_jobs: str = Field(default="jobs", alias="COSMOS_CONTAINER_JOBS")
    cosmos_container_content: str = Field(default="content", alias="COSMOS_CONTAINER_CONTENT")
    cosmos_partition_key: str = Field(default="/tenant_id", alias="COSMOS_PARTITION_KEY")

    # Azure AI Search
    azure_search_endpoint: str = Field(default="", alias="AZURE_SEARCH_ENDPOINT")
    azure_search_api_key: str = Field(default="", alias="AZURE_SEARCH_API_KEY")
    azure_search_index: str = Field(default="content-vector-index", alias="AZURE_SEARCH_INDEX")

    # App Insights
    appinsights_connection_string: str = Field(default="", alias="APPLICATIONINSIGHTS_CONNECTION_STRING")

    # Image gen — Pollinations.ai (free, no API key required)
    public_base_url: str = Field(default="http://localhost:8000", alias="PUBLIC_BASE_URL")
    image_storage_dir: str = Field(default="generated_images", alias="IMAGE_STORAGE_DIR")
    image_width: int = Field(default=1024, alias="IMAGE_WIDTH")
    image_height: int = Field(default=576, alias="IMAGE_HEIGHT")
    # Optional: swap in a paid provider later without touching agent code
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    stability_api_key: str = Field(default="", alias="STABILITY_API_KEY")
    ollama_model_reasoning: str = Field(default="deepseek-r1:14b", alias="OLLAMA_MODEL_REASONING")
    # Auth
    api_auth_token: str = Field(default="change-me-local-dev-token", alias="API_AUTH_TOKEN")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (singleton for the process lifetime)."""
    return Settings()