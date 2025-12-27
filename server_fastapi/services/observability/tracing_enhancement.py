"""
Distributed Tracing Enhancement
Enhanced OpenTelemetry integration for distributed tracing
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# OpenTelemetry availability
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning("OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests opentelemetry-instrumentation-sqlalchemy")


@dataclass
class TraceContext:
    """Trace context information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service_name: str = "cryptoorchestrator"
    operation_name: str = "unknown"


# Context variable for current trace
current_trace_context: ContextVar[Optional[TraceContext]] = ContextVar("current_trace_context", default=None)


class TracingEnhancementService:
    """
    Enhanced distributed tracing service
    
    Features:
    - OpenTelemetry integration
    - Trace correlation across services
    - Service dependency mapping
    - Performance analysis
    - Error tracking
    """
    
    def __init__(self, service_name: str = "cryptoorchestrator"):
        """
        Initialize tracing enhancement service
        
        Args:
            service_name: Name of the service
        """
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available, tracing disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.service_name = service_name
        self.tracer_provider = None
        self.tracer = None
        
        self._initialize_tracer()
    
    def _initialize_tracer(self):
        """Initialize OpenTelemetry tracer"""
        if not self.enabled:
            return
        
        try:
            # Create resource
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": "1.0.0",
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Add console exporter (in production, use OTLP exporter)
            console_exporter = ConsoleSpanExporter()
            span_processor = BatchSpanProcessor(console_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            logger.info("OpenTelemetry tracer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize tracer: {e}", exc_info=True)
            self.enabled = False
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[Any] = None,
    ):
        """
        Start a new span
        
        Args:
            name: Span name
            attributes: Optional span attributes
            parent_context: Optional parent span context
        
        Returns:
            Span context
        """
        if not self.enabled or not self.tracer:
            return None
        
        try:
            span = self.tracer.start_span(name, context=parent_context)
            
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            # Store trace context
            trace_context = TraceContext(
                trace_id=format(span.get_span_context().trace_id, "032x"),
                span_id=format(span.get_span_context().span_id, "016x"),
                service_name=self.service_name,
                operation_name=name,
            )
            current_trace_context.set(trace_context)
            
            return span
        except Exception as e:
            logger.error(f"Failed to start span: {e}", exc_info=True)
            return None
    
    def end_span(self, span, status: str = "ok", error: Optional[Exception] = None):
        """
        End a span
        
        Args:
            span: Span to end
            status: Status ("ok", "error")
            error: Optional error exception
        """
        if not self.enabled or not span:
            return
        
        try:
            if error:
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, str(error)))
            else:
                span.set_status(Status(StatusCode.OK))
            
            span.end()
            current_trace_context.set(None)
        except Exception as e:
            logger.error(f"Failed to end span: {e}", exc_info=True)
    
    def add_span_attribute(self, span, key: str, value: Any):
        """Add attribute to span"""
        if not self.enabled or not span:
            return
        
        try:
            span.set_attribute(key, str(value))
        except Exception as e:
            logger.error(f"Failed to add attribute: {e}", exc_info=True)
    
    def add_span_event(self, span, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to span"""
        if not self.enabled or not span:
            return
        
        try:
            span.add_event(name, attributes=attributes or {})
        except Exception as e:
            logger.error(f"Failed to add event: {e}", exc_info=True)
    
    def get_current_trace_context(self) -> Optional[TraceContext]:
        """Get current trace context"""
        return current_trace_context.get()
    
    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application
        
        Args:
            app: FastAPI application instance
        """
        if not self.enabled:
            return
        
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)
    
    def instrument_requests(self):
        """Instrument requests library"""
        if not self.enabled:
            return
        
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests library instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument requests: {e}", exc_info=True)
    
    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine
        
        Args:
            engine: SQLAlchemy engine
        """
        if not self.enabled:
            return
        
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}", exc_info=True)
    
    def get_service_dependencies(self) -> List[Dict[str, Any]]:
        """
        Get service dependency map
        
        Returns:
            List of service dependencies
        """
        # In production, this would analyze trace data to build dependency map
        # For now, return static dependencies
        return [
            {
                "service": "api",
                "dependencies": ["database", "redis", "external_apis"],
            },
            {
                "service": "database",
                "dependencies": [],
            },
            {
                "service": "redis",
                "dependencies": [],
            },
        ]


# Global instance
tracing_enhancement_service = TracingEnhancementService()
