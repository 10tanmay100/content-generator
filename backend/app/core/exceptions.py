"""Custom exception types and FastAPI exception handlers."""
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base application error with an HTTP status code attached."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class JobNotFoundError(AppError):
    def __init__(self, job_id: str):
        super().__init__(f"Job '{job_id}' not found", status.HTTP_404_NOT_FOUND)


class CrewExecutionError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.error("app_error", path=str(request.url), error=exc.message, details=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=str(request.url), error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )
