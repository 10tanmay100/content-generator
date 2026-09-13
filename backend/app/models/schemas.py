"""Pydantic request/response schemas for the public API."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    EDITING = "editing"
    SEO_OPTIMIZING = "seo_optimizing"
    GENERATING_IMAGE = "generating_image"
    SOCIAL_ADAPTING = "social_adapting"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentFormat(str, Enum):
    BLOG = "blog"
    SOCIAL = "social"
    EMAIL = "email"
    NEWSLETTER = "newsletter"


class ContentGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300, description="Topic or working title for the content")
    content_format: ContentFormat = Field(default=ContentFormat.BLOG)
    tone: str = Field(default="professional", description="e.g. professional, casual, witty, authoritative")
    target_audience: str = Field(default="general readers")
    target_keywords: list[str] = Field(default_factory=list)
    word_count: int = Field(default=900, ge=150, le=5000)
    generate_image: bool = Field(default=True)
    generate_social_variants: bool = Field(default=True)
    tenant_id: str = Field(default="default", description="Multi-tenant partition key")


class ContentGenerationResponse(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.PENDING
    message: str = "Job accepted and queued for processing"


class AgentStepResult(BaseModel):
    agent: str
    status: str
    output_summary: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobRecord(BaseModel):
    id: str
    tenant_id: str
    topic: str
    content_format: ContentFormat
    status: JobStatus
    request: dict[str, Any]
    result: Optional[dict[str, Any]] = None
    steps: list[AgentStepResult] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    llm_cost_usd: float = 0.0
    llm_tokens_used: int = 0


class ContentResult(BaseModel):
    title: str
    body_markdown: str
    meta_description: Optional[str] = None
    seo_keywords: list[str] = Field(default_factory=list)
    seo_score: Optional[int] = None
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None
    alt_text: Optional[str] = None
    social_variants: dict[str, str] = Field(default_factory=dict)
    hashtags: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    version: str = "1.0.0"
