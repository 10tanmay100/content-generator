"""
FastAPI application entrypoint: CrewAI-powered content creation pipeline.
Run locally: uvicorn app.main:app --reload
"""
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import content, health, jobs
from app.config import get_settings
from app.core.exceptions import AppError, app_error_handler, unhandled_exception_handler
from app.core.logging import configure_logging, get_logger
from app.utils.telemetry import configure_telemetry

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Production-grade CrewAI multi-agent content creation pipeline (research, writing, editing, SEO, image, social).",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configure_telemetry(app)

# Serve AI-generated hero images saved by app/tools/image_tool.py
Path(settings.image_storage_dir).mkdir(parents=True, exist_ok=True)
app.mount("/generated-images", StaticFiles(directory=settings.image_storage_dir), name="generated-images")

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    logger.info("request_completed", path=request.url.path, method=request.method, duration_ms=duration_ms, status=response.status_code)
    return response


app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(content.router, prefix=settings.api_v1_prefix)
app.include_router(jobs.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict:
    return {"service": settings.app_name, "status": "running", "docs": "/docs"}