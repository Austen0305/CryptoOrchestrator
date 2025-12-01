"""
Query Monitoring Middleware
Monitors database query performance and provides insights
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import time

from ..services.query_optimizer import query_optimizer

logger = logging.getLogger(__name__)


class QueryMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor database query performance"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Track request start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log slow requests with query context
        if duration > 2.0:  # 2 seconds threshold
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration:.3f}s (request_id: {request_id})"
            )
        
        # Add query performance header if available
        query_stats = await query_optimizer.get_query_statistics()
        if query_stats.get("total_queries", 0) > 0:
            response.headers["X-Query-Count"] = str(query_stats["total_queries"])
            response.headers["X-Avg-Query-Time-Ms"] = str(
                query_stats.get("avg_time_per_query_ms", 0)
            )
        
        return response

