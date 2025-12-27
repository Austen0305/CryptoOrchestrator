"""
Trace Correlation Service
Correlates traces across FastAPI → Celery → Blockchain RPC for end-to-end visibility.
"""

import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar
import uuid

logger = logging.getLogger(__name__)

# Context variables for trace correlation
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class TraceCorrelationService:
    """Service for trace correlation across services"""

    def __init__(self):
        self.active_traces: Dict[str, Dict[str, Any]] = {}

    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID from context"""
        return trace_id_var.get()

    def get_span_id(self) -> Optional[str]:
        """Get current span ID from context"""
        return span_id_var.get()

    def get_request_id(self) -> Optional[str]:
        """Get current request ID from context"""
        return request_id_var.get()

    def set_trace_context(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Set trace context variables"""
        if trace_id:
            trace_id_var.set(trace_id)
        if span_id:
            span_id_var.set(span_id)
        if request_id:
            request_id_var.set(request_id)

    def generate_trace_id(self) -> str:
        """Generate a new trace ID"""
        return str(uuid.uuid4())

    def create_trace_context(
        self,
        parent_trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Create trace context for distributed tracing.
        Returns trace_id and span_id for correlation.
        """
        trace_id = parent_trace_id or self.generate_trace_id()
        span_id = self.generate_trace_id()

        self.set_trace_context(
            trace_id=trace_id, span_id=span_id, request_id=self.generate_trace_id()
        )

        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "request_id": self.get_request_id(),
        }

    def propagate_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Propagate trace context in HTTP headers for distributed tracing.
        Follows W3C Trace Context format.
        """
        trace_id = self.get_trace_id()
        span_id = self.get_span_id()

        if trace_id:
            headers["traceparent"] = f"00-{trace_id}-{span_id or '0'}-01"

        if trace_id:
            headers["X-Trace-ID"] = trace_id
        if span_id:
            headers["X-Span-ID"] = span_id
        if self.get_request_id():
            headers["X-Request-ID"] = self.get_request_id()

        return headers

    def extract_trace_context(
        self, headers: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """
        Extract trace context from HTTP headers.
        Supports W3C Trace Context and custom headers.
        """
        trace_id = None
        span_id = None

        # Try W3C Trace Context format
        traceparent = headers.get("traceparent")
        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 3:
                trace_id = parts[1]
                span_id = parts[2]

        # Fallback to custom headers
        if not trace_id:
            trace_id = headers.get("X-Trace-ID")
        if not span_id:
            span_id = headers.get("X-Span-ID")

        if trace_id:
            self.set_trace_context(
                trace_id=trace_id,
                span_id=span_id,
                request_id=headers.get("X-Request-ID"),
            )
            return {
                "trace_id": trace_id,
                "span_id": span_id,
                "request_id": headers.get("X-Request-ID"),
            }

        return None

    def get_correlation_context(self) -> Dict[str, Optional[str]]:
        """Get current correlation context for logging"""
        return {
            "trace_id": self.get_trace_id(),
            "span_id": self.get_span_id(),
            "request_id": self.get_request_id(),
        }


# Singleton instance
_trace_correlation_service: Optional[TraceCorrelationService] = None


def get_trace_correlation_service() -> TraceCorrelationService:
    """Get trace correlation service instance"""
    global _trace_correlation_service
    if _trace_correlation_service is None:
        _trace_correlation_service = TraceCorrelationService()
    return _trace_correlation_service
