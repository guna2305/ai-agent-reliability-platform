"""OpenTelemetry setup — enabled via OTEL_ENABLED=true in .env.

All imports are deferred so missing packages don't crash the app.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def setup_otel(app) -> None:  # type: ignore[type-arg]
    from src.infrastructure.config.settings import get_settings
    settings = get_settings()

    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. "
            "Run: pip install opentelemetry-sdk opentelemetry-exporter-otlp "
            "opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy"
        )
        return

    resource = Resource(attributes={"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()

    logger.info(
        "OpenTelemetry configured",
        extra={"endpoint": settings.otel_exporter_otlp_endpoint},
    )


def get_tracer(name: str = "agent-platform"):
    """Get a tracer for manual instrumentation. Safe to call even if OTel is disabled."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _NoopTracer()


class _NoopTracer:
    """Fallback no-op tracer when OpenTelemetry is not installed."""
    def start_as_current_span(self, name: str, **kwargs):
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield None
        return _noop()
