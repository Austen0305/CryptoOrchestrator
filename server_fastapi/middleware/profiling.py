"""
Middleware Profiling Utility
Profiles middleware execution time to identify bottlenecks
"""

import time
import logging
from typing import Dict, List
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global profiling data
_profiling_data: Dict[str, List[float]] = defaultdict(list)
_profiling_enabled = False


def enable_profiling() -> None:
    """Enable middleware profiling"""
    global _profiling_enabled
    _profiling_enabled = True
    logger.info("Middleware profiling enabled")


def disable_profiling() -> None:
    """Disable middleware profiling"""
    global _profiling_enabled
    _profiling_enabled = False
    logger.info("Middleware profiling disabled")


def get_profiling_stats() -> Dict[str, Dict[str, float]]:
    """
    Get profiling statistics

    Returns:
        Dictionary mapping middleware names to stats (avg, min, max, count)
    """
    stats = {}
    for middleware_name, times in _profiling_data.items():
        if times:
            stats[middleware_name] = {
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "count": len(times),
                "total": sum(times),
            }
    return stats


def clear_profiling_data() -> None:
    """Clear all profiling data"""
    global _profiling_data
    _profiling_data.clear()
    logger.info("Profiling data cleared")


class ProfilingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that profiles other middleware execution times
    
    This should be added early in the middleware stack to profile
    all subsequent middleware.
    """

    def __init__(self, app, enabled: bool | None = None):
        super().__init__(app)
        global _profiling_enabled
        if enabled is not None:
            _profiling_enabled = enabled
        self.enabled = _profiling_enabled

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Store start time
        start_time = time.time()
        
        # Add profiling context to request state
        request.state.profiling_start = start_time
        request.state.profiling_steps = []

        try:
            response = await call_next(request)
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Log if request took longer than 1 second
            if total_time > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {total_time:.3f}s"
                )
                if hasattr(request.state, "profiling_steps"):
                    steps = request.state.profiling_steps
                    if steps:
                        logger.warning(f"Middleware steps: {steps}")
            
            return response
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"Request failed after {total_time:.3f}s: {request.method} {request.url.path} - {e}"
            )
            raise


def profile_middleware(middleware_name: str):
    """
    Decorator to profile a specific middleware function
    
    Usage:
        @profile_middleware("MyMiddleware")
        async def dispatch(self, request, call_next):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not _profiling_enabled:
                return await func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                _profiling_data[middleware_name].append(elapsed)
                
                # Log slow middleware
                if elapsed > 0.5:
                    logger.warning(
                        f"Slow middleware: {middleware_name} took {elapsed:.3f}s"
                    )
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Middleware {middleware_name} failed after {elapsed:.3f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


async def log_profiling_summary() -> None:
    """Log profiling summary to help identify bottlenecks"""
    if not _profiling_enabled:
        return
    
    stats = get_profiling_stats()
    if not stats:
        logger.info("No profiling data collected")
        return
    
    logger.info("=" * 60)
    logger.info("Middleware Profiling Summary")
    logger.info("=" * 60)
    
    # Sort by average time (descending)
    sorted_stats = sorted(
        stats.items(),
        key=lambda x: x[1]["avg"],
        reverse=True
    )
    
    for middleware_name, middleware_stats in sorted_stats:
        logger.info(
            f"{middleware_name:30s} "
            f"avg: {middleware_stats['avg']:.3f}s "
            f"min: {middleware_stats['min']:.3f}s "
            f"max: {middleware_stats['max']:.3f}s "
            f"count: {middleware_stats['count']} "
            f"total: {middleware_stats['total']:.3f}s"
        )
    
    logger.info("=" * 60)


def get_slow_middleware(threshold: float = 0.1) -> List[tuple]:
    """
    Get middleware that takes longer than threshold
    
    Args:
        threshold: Time threshold in seconds
        
    Returns:
        List of (middleware_name, avg_time) tuples
    """
    stats = get_profiling_stats()
    slow = [
        (name, data["avg"])
        for name, data in stats.items()
        if data["avg"] > threshold
    ]
    return sorted(slow, key=lambda x: x[1], reverse=True)
