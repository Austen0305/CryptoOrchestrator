"""
OpenTelemetry Setup and Configuration
Provides full observability with distributed tracing, metrics, and logs
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# OpenTelemetry availability
OTEL_AVAILABLE = False
tracer = None
meter = None
logger_provider = None

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
        ConsoleMetricExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.prometheus import PrometheusMetricExporter
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    OTEL_AVAILABLE = True
except ImportError:
    logger.warning(
        "OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy opentelemetry-exporter-otlp"
    )
    OTEL_AVAILABLE = False


def setup_opentelemetry(
    service_name: str = "cryptoorchestrator",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enable_console_exporter: bool = False,
    enable_prometheus: bool = True,
) -> bool:
    """
    Setup OpenTelemetry instrumentation

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP endpoint URL (e.g., http://localhost:4317)
        enable_console_exporter: Enable console exporter for debugging
        enable_prometheus: Enable Prometheus metrics export

    Returns:
        True if setup successful
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, skipping setup")
        return False

    try:
        # Get OTLP endpoint from environment if not provided
        if not otlp_endpoint:
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

        # Create resource
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "service.namespace": "cryptoorchestrator",
            }
        )

        # Setup Tracer Provider
        trace_provider = TracerProvider(resource=resource)

        # Add span processors
        if otlp_endpoint:
            # OTLP exporter (for Jaeger, Tempo, etc.)
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"[OK] OpenTelemetry OTLP exporter configured: {otlp_endpoint}")

        if enable_console_exporter:
            # Console exporter for debugging
            console_exporter = ConsoleSpanExporter()
            trace_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("[OK] OpenTelemetry console exporter enabled")

        trace.set_tracer_provider(trace_provider)
        global tracer
        tracer = trace.get_tracer(__name__)

        # Setup Meter Provider
        metric_readers = []

        if otlp_endpoint:
            # OTLP metric exporter
            otlp_metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
            metric_readers.append(PeriodicExportingMetricReader(otlp_metric_exporter))

        if enable_prometheus:
            # Prometheus exporter (for /metrics endpoint)
            try:
                from opentelemetry.exporter.prometheus import PrometheusMetricExporter

                prometheus_exporter = PrometheusMetricExporter()
                metric_readers.append(
                    PeriodicExportingMetricReader(prometheus_exporter)
                )
                logger.info("[OK] Prometheus metrics exporter enabled")
            except ImportError:
                logger.warning("Prometheus exporter not available")

        if metric_readers:
            meter_provider = MeterProvider(
                resource=resource, metric_readers=metric_readers
            )
            metrics.set_meter_provider(meter_provider)
            global meter
            meter = metrics.get_meter(__name__)

        logger.info("[OK] OpenTelemetry setup complete")
        return True

    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}", exc_info=True)
        return False


def instrument_fastapi(app) -> bool:
    """
    Instrument FastAPI application with OpenTelemetry

    Args:
        app: FastAPI application instance

    Returns:
        True if instrumentation successful
    """
    if not OTEL_AVAILABLE:
        return False

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("[OK] FastAPI instrumented with OpenTelemetry")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)
        return False


def instrument_sqlalchemy() -> bool:
    """
    Instrument SQLAlchemy with OpenTelemetry

    Returns:
        True if instrumentation successful
    """
    if not OTEL_AVAILABLE:
        return False

    try:
        SQLAlchemyInstrumentor().instrument()
        logger.info("[OK] SQLAlchemy instrumented with OpenTelemetry")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}", exc_info=True)
        return False


def instrument_requests() -> bool:
    """
    Instrument requests library with OpenTelemetry

    Returns:
        True if instrumentation successful
    """
    if not OTEL_AVAILABLE:
        return False

    try:
        RequestsInstrumentor().instrument()
        logger.info("[OK] Requests library instrumented with OpenTelemetry")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument requests: {e}", exc_info=True)
        return False


def get_tracer():
    """Get OpenTelemetry tracer"""
    global tracer
    if tracer is None and OTEL_AVAILABLE:
        tracer = trace.get_tracer(__name__)
    return tracer


def get_meter():
    """Get OpenTelemetry meter"""
    global meter
    if meter is None and OTEL_AVAILABLE:
        meter = metrics.get_meter(__name__)
    return meter


def create_span(name: str, attributes: Optional[dict] = None):
    """
    Create a span context manager

    Usage:
        with create_span("operation_name", {"key": "value"}):
            # Your code here
    """
    if not OTEL_AVAILABLE:
        # Return a no-op context manager
        from contextlib import nullcontext

        return nullcontext()

    tracer = get_tracer()
    if tracer:
        span = tracer.start_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        return span
    else:
        from contextlib import nullcontext

        return nullcontext()


def record_metric(
    name: str, value: float, unit: str = "", attributes: Optional[dict] = None
):
    """
    Record a metric value

    Args:
        name: Metric name
        value: Metric value
        unit: Unit of measurement
        attributes: Additional attributes
    """
    if not OTEL_AVAILABLE:
        return

    meter = get_meter()
    if meter:
        counter = meter.create_counter(
            name=name, description=f"Counter for {name}", unit=unit
        )
        counter.add(value, attributes or {})


def record_gauge(
    name: str, value: float, unit: str = "", attributes: Optional[dict] = None
):
    """
    Record a gauge metric value

    Args:
        name: Metric name
        value: Current gauge value
        unit: Unit of measurement
        attributes: Additional attributes
    """
    if not OTEL_AVAILABLE:
        return

    meter = get_meter()
    if meter:
        gauge = meter.create_up_down_counter(
            name=name, description=f"Gauge for {name}", unit=unit
        )
        gauge.add(value, attributes or {})


def record_histogram(
    name: str, value: float, unit: str = "", attributes: Optional[dict] = None
):
    """
    Record a histogram metric value

    Args:
        name: Metric name
        value: Histogram value
        unit: Unit of measurement
        attributes: Additional attributes
    """
    if not OTEL_AVAILABLE:
        return

    meter = get_meter()
    if meter:
        histogram = meter.create_histogram(
            name=name, description=f"Histogram for {name}", unit=unit
        )
        histogram.record(value, attributes or {})


# Initialize on import if enabled
# Enhanced trace correlation support
try:
    from ..monitoring.trace_correlation import get_trace_correlation_service

    trace_correlation = get_trace_correlation_service()
except ImportError:
    trace_correlation = None

if os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true":
    setup_opentelemetry(
        service_name=os.getenv("OTEL_SERVICE_NAME", "cryptoorchestrator"),
        service_version=os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        enable_console_exporter=os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower()
        == "true",
        enable_prometheus=os.getenv("OTEL_PROMETHEUS", "true").lower() == "true",
    )
