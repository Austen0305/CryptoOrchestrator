"""
Performance monitoring middleware for tracking request performance.
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from collections import defaultdict, deque
import asyncio

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Track and analyze API performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_times: deque = deque(maxlen=max_history)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0
        })
        self.lock = asyncio.Lock()
    
    async def record_request(
        self,
        method: str,
        path: str,
        duration: float,
        status_code: int
    ):
        """Record a request's performance metrics"""
        endpoint = f"{method} {path}"
        is_error = status_code >= 400
        
        async with self.lock:
            self.request_times.append({
                "endpoint": endpoint,
                "duration": duration,
                "status_code": status_code,
                "timestamp": time.time()
            })
            
            stats = self.endpoint_stats[endpoint]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["min_time"] = min(stats["min_time"], duration)
            stats["max_time"] = max(stats["max_time"], duration)
            
            if is_error:
                stats["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self.request_times:
            return {
                "total_requests": 0,
                "average_response_time": 0.0,
                "endpoints": {}
            }
        
        total_requests = len(self.request_times)
        total_time = sum(req["duration"] for req in self.request_times)
        avg_time = total_time / total_requests if total_requests > 0 else 0.0
        
        # Calculate per-endpoint statistics
        endpoint_stats = {}
        for endpoint, stats in self.endpoint_stats.items():
            endpoint_stats[endpoint] = {
                "count": stats["count"],
                "average_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0.0,
                "min_time": stats["min_time"] if stats["min_time"] != float('inf') else 0.0,
                "max_time": stats["max_time"],
                "error_rate": stats["errors"] / stats["count"] if stats["count"] > 0 else 0.0,
                "errors": stats["errors"]
            }
        
        return {
            "total_requests": total_requests,
            "average_response_time": round(avg_time * 1000, 2),  # Convert to ms
            "endpoints": endpoint_stats
        }
    
    def get_slow_requests(self, threshold_ms: float = 1000.0, limit: int = 10) -> list:
        """Get slowest requests above threshold"""
        slow_requests = [
            req for req in self.request_times
            if req["duration"] * 1000 >= threshold_ms
        ]
        
        # Sort by duration descending
        slow_requests.sort(key=lambda x: x["duration"], reverse=True)
        
        return slow_requests[:limit]


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor request performance"""
    
    def __init__(self, app, monitor: PerformanceMonitor = None):
        super().__init__(app)
        self.monitor = monitor or performance_monitor
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics asynchronously (don't block response)
        asyncio.create_task(
            self.monitor.record_request(
                method=request.method,
                path=request.url.path,
                duration=duration,
                status_code=response.status_code
            )
        )
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"
        
        return response

