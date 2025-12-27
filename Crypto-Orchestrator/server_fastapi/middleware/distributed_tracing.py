"""
Distributed Tracing Integration
Provides OpenTelemetry and custom tracing support
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.debug("OpenTelemetry not available, using custom tracing")


class DistributedTracing:
    """Distributed tracing manager"""

    def __init__(self, enable_opentelemetry: bool = True):
        self.enable_opentelemetry = enable_opentelemetry and OPENTELEMETRY_AVAILABLE
        self.tracer = None

        if self.enable_opentelemetry:
            self._setup_opentelemetry()
        else:
            self._setup_custom_tracing()

    def _setup_opentelemetry(self):
        """Setup OpenTelemetry tracing"""
        try:
            resource = Resource.create({"service.name": "cryptoorchestrator"})
            provider = TracerProvider(resource=resource)

            # Add OTLP exporter if configured
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            if otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            else:
                # Use console exporter for development
                console_exporter = ConsoleSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(console_exporter))

            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(__name__)
            logger.info("OpenTelemetry tracing initialized")
        except Exception as e:
            logger.warning(f"Failed to setup OpenTelemetry: {e}")
            self._setup_custom_tracing()

    def _setup_custom_tracing(self):
        """Setup custom tracing (fallback)"""
        logger.info("Using custom tracing (OpenTelemetry not available)")

    def start_span(self, name: str, context: Optional[Dict[str, Any]] = None):
        """Start a trace span"""
        if self.enable_opentelemetry and self.tracer:
            span = self.tracer.start_span(name)
            if context:
                for key, value in context.items():
                    span.set_attribute(key, str(value))
            return span
        else:
            # Custom span object
            return CustomSpan(name, context or {})

    def get_trace_context(self, request: Request) -> Dict[str, str]:
        """Extract trace context from request"""
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        span_id = request.headers.get("X-Span-ID") or str(uuid.uuid4())
        parent_span_id = request.headers.get("X-Parent-Span-ID")

        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
        }

    def inject_trace_context(self, headers: Dict[str, str], trace_id: str, span_id: str):
        """Inject trace context into headers"""
        headers["X-Trace-ID"] = trace_id
        headers["X-Span-ID"] = span_id


class CustomSpan:
    """Custom span implementation (fallback)"""

    def __init__(self, name: str, attributes: Dict[str, Any]):
        self.name = name
        self.attributes = attributes
        self.start_time = time.perf_counter()
        self.end_time = None

    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        self.attributes[key] = value

    def end(self):
        """End the span"""
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        logger.debug(f"Span {self.name} completed in {duration*1000:.2f}ms")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


# Global tracing instance
import os

distributed_tracing = DistributedTracing(
    enable_opentelemetry=os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true"
)


class DistributedTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing"""

    def __init__(self, app):
        super().__init__(app)
        self.tracing = distributed_tracing

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with tracing"""
        # Get trace context
        trace_context = self.tracing.get_trace_context(request)

        # Start span
        span = self.tracing.start_span(
            f"{request.method} {request.url.path}",
            context={
                "http.method": request.method,
                "http.path": request.url.path,
                "http.query": str(request.query_params),
                "trace_id": trace_context["trace_id"],
            },
        )

        # Store in request state
        request.state.trace_id = trace_context["trace_id"]
        request.state.span_id = trace_context["span_id"]
        request.state.span = span

        try:
            # Process request
            response = await call_next(request)

            # Add trace headers
            response.headers["X-Trace-ID"] = trace_context["trace_id"]
            response.headers["X-Span-ID"] = trace_context["span_id"]

            # Set span attributes
            if hasattr(span, "set_attribute"):
                span.set_attribute("http.status_code", response.status_code)

            return response
        except Exception as e:
            # Record error in span
            if hasattr(span, "set_attribute"):
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
            raise
        finally:
            # End span
            if hasattr(span, "end"):
                span.end()


def instrument_fastapi(app):
    """Instrument FastAPI with OpenTelemetry"""
    if distributed_tracing.enable_opentelemetry and OPENTELEMETRY_AVAILABLE:
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")
