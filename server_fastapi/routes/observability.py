"""
Observability API Routes
Endpoints for distributed tracing and observability
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.observability.opentelemetry_setup import get_tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/observability", tags=["Observability"])


class Trace(BaseModel):
    trace_id: str
    service_name: str
    operation_name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str
    span_count: int
    error_count: int
    tags: dict[str, str]


class Span(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: str | None
    service_name: str
    operation_name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str
    tags: dict[str, str]
    logs: list[dict[str, Any]] | None


class TraceDetail(BaseModel):
    trace: Trace
    spans: list[Span]
    service_map: dict[str, list[str]]


@router.get(
    "/traces",
    response_model=list[Trace],
    summary="Get distributed traces",
    description="""
    Get list of distributed traces with optional filtering by service, status, and time range.
    
    **Example Response:**
    ```json
    [
      {
        "trace_id": "abc123def456",
        "service_name": "trading-service",
        "operation_name": "execute_trade",
        "start_time": "2024-01-15T10:00:00Z",
        "end_time": "2024-01-15T10:00:05Z",
        "duration_ms": 5000.0,
        "status": "ok",
        "span_count": 12,
        "error_count": 0,
        "tags": {
          "user_id": "123",
          "bot_id": "bot-456"
        }
      }
    ]
    ```
    
    **Query Parameters:**
    - `service` (optional): Filter by service name (e.g., "trading-service", "analytics-service")
    - `status` (optional): Filter by status ("ok" or "error")
    - `time_range`: Time range for traces ("15m", "1h", "6h", "24h", "7d")
    
    **Note:** This is a simplified implementation. In production, this would
    query a distributed tracing backend (Jaeger, Zipkin, etc.)
    """,
)
@cached(ttl=10, prefix="observability_traces")
async def get_traces(
    service: str | None = Query(None, description="Filter by service name"),
    status: str | None = Query(None, description="Filter by status: ok, error"),
    time_range: str = Query("1h", description="Time range: 15m, 1h, 6h, 24h, 7d"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> list[Trace]:
    """
    Get list of traces with optional filtering

    Note: This is a simplified implementation. In production, this would
    query a distributed tracing backend (Jaeger, Zipkin, etc.)
    """
    try:
        # Parse time range
        end_time = datetime.now()
        if time_range == "15m":
            end_time - timedelta(minutes=15)
        elif time_range == "1h":
            end_time - timedelta(hours=1)
        elif time_range == "6h":
            end_time - timedelta(hours=6)
        elif time_range == "24h":
            end_time - timedelta(days=1)
        elif time_range == "7d":
            end_time - timedelta(days=7)
        else:
            end_time - timedelta(hours=1)

        # In production, this would query a tracing backend
        # For now, return empty list or mock data based on configuration
        # This allows the frontend to work without a full tracing setup

        # Try to get traces from OpenTelemetry if available
        tracer = get_tracer()
        if tracer:
            # In production, integrate with Jaeger/Zipkin backend
            # For now, return empty list
            traces = []
        else:
            # No tracer available, return empty list
            traces = []

        # Filter traces
        if service and service != "all":
            traces = [t for t in traces if t.get("service_name") == service]

        if status and status != "all":
            traces = [t for t in traces if t.get("status") == status]

        return [Trace(**trace) for trace in traces]
    except Exception as e:
        logger.error(f"Error getting traces: {e}", exc_info=True)
        # Return empty list instead of error to allow frontend to work
        return []


@router.get("/traces/{trace_id}")
@cached(ttl=60, prefix="observability_trace_detail")
async def get_trace_detail(
    trace_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> TraceDetail:
    """
    Get detailed trace information including all spans

    Note: This is a simplified implementation. In production, this would
    query a distributed tracing backend.
    """
    try:
        # In production, query tracing backend for trace details
        # For now, return a structure that matches the expected format

        # Try to get trace from OpenTelemetry if available
        tracer = get_tracer()
        if tracer:
            # In production, integrate with Jaeger/Zipkin backend
            # For now, return empty structure
            trace_data = {
                "trace": {
                    "trace_id": trace_id,
                    "service_name": "unknown",
                    "operation_name": "unknown",
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_ms": 0.0,
                    "status": "ok",
                    "span_count": 0,
                    "error_count": 0,
                    "tags": {},
                },
                "spans": [],
                "service_map": {},
            }
        else:
            # No tracer available
            trace_data = {
                "trace": {
                    "trace_id": trace_id,
                    "service_name": "unknown",
                    "operation_name": "unknown",
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_ms": 0.0,
                    "status": "ok",
                    "span_count": 0,
                    "error_count": 0,
                    "tags": {},
                },
                "spans": [],
                "service_map": {},
            }

        return TraceDetail(
            trace=Trace(**trace_data["trace"]),
            spans=[Span(**span) for span in trace_data["spans"]],
            service_map=trace_data["service_map"],
        )
    except Exception as e:
        logger.error(f"Error getting trace detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trace detail")


@router.get("/traces/{trace_id}/export")
async def export_trace(
    trace_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Export trace data as JSON

    Returns trace data in a format suitable for export/analysis.
    """
    try:
        # Get trace detail
        trace_detail = await get_trace_detail(trace_id, current_user)

        # Convert to exportable format
        export_data = {
            "trace_id": trace_detail.trace.trace_id,
            "exported_at": datetime.now().isoformat(),
            "trace": trace_detail.trace.dict(),
            "spans": [span.dict() for span in trace_detail.spans],
            "service_map": trace_detail.service_map,
        }

        return export_data
    except Exception as e:
        logger.error(f"Error exporting trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export trace")


@router.get("/services")
@cached(ttl=300, prefix="observability_services")
async def get_services(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> list[str]:
    """
    Get list of services that have generated traces

    Note: In production, this would query the tracing backend.
    """
    try:
        # In production, query tracing backend for service list
        # For now, return common service names
        services = [
            "api",
            "trading-service",
            "wallet-service",
            "bot-service",
            "market-data-service",
            "analytics-service",
            "ml-service",
        ]

        return services
    except Exception as e:
        logger.error(f"Error getting services: {e}", exc_info=True)
        return []
