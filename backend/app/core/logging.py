"""
Structured logging setup (structlog) with optional Azure Application Insights export.
"""
import logging
import sys

import structlog

from app.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    if settings.appinsights_connection_string:
        try:
            from opencensus.ext.azure.log_exporter import AzureLogHandler

            azure_handler = AzureLogHandler(connection_string=settings.appinsights_connection_string)
            logging.getLogger().addHandler(azure_handler)
        except Exception as exc:  # pragma: no cover
            logging.getLogger(__name__).warning("Failed to attach Azure log handler: %s", exc)


def get_logger(name: str):
    return structlog.get_logger(name)
