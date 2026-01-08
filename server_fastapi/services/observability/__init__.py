"""
OpenTelemetry Observability Module
"""

from .opentelemetry_setup import (
    OTEL_AVAILABLE,
    create_span,
    get_meter,
    get_tracer,
    instrument_fastapi,
    instrument_requests,
    instrument_sqlalchemy,
    record_metric,
    setup_opentelemetry,
)

__all__ = [
    "setup_opentelemetry",
    "instrument_fastapi",
    "instrument_sqlalchemy",
    "instrument_requests",
    "get_tracer",
    "get_meter",
    "create_span",
    "record_metric",
    "OTEL_AVAILABLE",
]
