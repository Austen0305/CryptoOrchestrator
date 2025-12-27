"""
OpenTelemetry Observability Module
"""

from .opentelemetry_setup import (
    setup_opentelemetry,
    instrument_fastapi,
    instrument_sqlalchemy,
    instrument_requests,
    get_tracer,
    get_meter,
    create_span,
    record_metric,
    OTEL_AVAILABLE,
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
