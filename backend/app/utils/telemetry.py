"""Azure Monitor / Application Insights request tracing middleware."""
from app.config import get_settings

settings = get_settings()


def configure_telemetry(app) -> None:
    """Attach OpenCensus Azure trace middleware if a connection string is configured."""
    if not settings.appinsights_connection_string:
        return
    try:
        from opencensus.ext.azure.trace_exporter import AzureExporter
        from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
        from opencensus.trace.samplers import ProbabilitySampler

        app.add_middleware(
            FastAPIMiddleware,
            exporter=AzureExporter(connection_string=settings.appinsights_connection_string),
            sampler=ProbabilitySampler(rate=1.0 if not settings.is_production else 0.2),
        )
    except Exception:  # pragma: no cover
        pass
