"""
Cache Analytics Service
Provides detailed analytics and insights into cache performance.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class CacheAnalytics:
    """
    Tracks and analyzes cache performance metrics.
    """

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history

        # Performance metrics
        self.response_times: deque = deque(maxlen=max_history)
        self.cache_operations: deque = deque(maxlen=max_history)

        # Hit/miss tracking by key pattern
        self.hits_by_pattern: Dict[str, int] = defaultdict(int)
        self.misses_by_pattern: Dict[str, int] = defaultdict(int)

        # Size tracking
        self.size_by_pattern: Dict[str, int] = defaultdict(int)

        # Error tracking
        self.errors_by_type: Dict[str, int] = defaultdict(int)

        # Time-based metrics
        self.hourly_metrics: Dict[int, Dict[str, Any]] = defaultdict(
            lambda: {"hits": 0, "misses": 0, "errors": 0}
        )

    def record_operation(
        self,
        operation: str,  # 'get', 'set', 'delete'
        key: str,
        hit: bool = False,
        response_time_ms: Optional[float] = None,
        size_bytes: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record a cache operation.

        Args:
            operation: Operation type ('get', 'set', 'delete')
            key: Cache key
            hit: Whether it was a cache hit (for 'get' operations)
            response_time_ms: Response time in milliseconds
            size_bytes: Size of cached value in bytes
            error: Error message if operation failed
        """
        timestamp = datetime.utcnow()
        hour = timestamp.hour

        # Extract key pattern (e.g., 'user:123' -> 'user:*')
        pattern = self._extract_pattern(key)

        # Record operation
        self.cache_operations.append(
            {
                "timestamp": timestamp,
                "operation": operation,
                "key": key,
                "pattern": pattern,
                "hit": hit,
                "response_time_ms": response_time_ms,
                "size_bytes": size_bytes,
                "error": error,
            }
        )

        # Update metrics
        if operation == "get":
            if hit:
                self.hits_by_pattern[pattern] += 1
                self.hourly_metrics[hour]["hits"] += 1
            else:
                self.misses_by_pattern[pattern] += 1
                self.hourly_metrics[hour]["misses"] += 1

        if response_time_ms is not None:
            self.response_times.append(response_time_ms)

        if size_bytes is not None:
            self.size_by_pattern[pattern] += size_bytes

        if error:
            self.errors_by_type[error] += 1
            self.hourly_metrics[hour]["errors"] += 1

    def _extract_pattern(self, key: str) -> str:
        """
        Extract pattern from cache key.

        Args:
            key: Cache key (e.g., 'user:123:profile')

        Returns:
            Pattern (e.g., 'user:*:profile')
        """
        # Simple pattern extraction - replace IDs with wildcards
        parts = key.split(":")
        if len(parts) > 1:
            # Replace middle parts that look like IDs
            pattern_parts = []
            for i, part in enumerate(parts):
                if i == 0:
                    pattern_parts.append(part)  # Keep prefix
                elif part.isdigit() or (len(part) == 36 and "-" in part):  # UUID
                    pattern_parts.append("*")
                else:
                    pattern_parts.append(part)
            return ":".join(pattern_parts)
        return key

    def get_statistics(
        self, time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Args:
            time_window_minutes: Optional time window to filter statistics

        Returns:
            Dictionary with cache statistics
        """
        cutoff_time = None
        if time_window_minutes:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        # Filter operations by time window
        if cutoff_time:
            recent_operations = [
                op for op in self.cache_operations if op["timestamp"] >= cutoff_time
            ]
        else:
            recent_operations = list(self.cache_operations)

        # Calculate metrics
        total_gets = sum(1 for op in recent_operations if op["operation"] == "get")
        total_hits = sum(1 for op in recent_operations if op.get("hit", False))
        total_misses = total_gets - total_hits
        hit_rate = (total_hits / total_gets * 100) if total_gets > 0 else 0

        # Response time statistics
        response_times = [
            op["response_time_ms"]
            for op in recent_operations
            if op.get("response_time_ms") is not None
        ]

        response_time_stats = {}
        if response_times:
            response_time_stats = {
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": (
                    statistics.quantiles(response_times, n=20)[18]
                    if len(response_times) > 20
                    else max(response_times)
                ),
                "p99": (
                    statistics.quantiles(response_times, n=100)[98]
                    if len(response_times) > 100
                    else max(response_times)
                ),
                "min": min(response_times),
                "max": max(response_times),
            }

        # Top patterns by hit rate
        pattern_stats = []
        for pattern in set(self.hits_by_pattern.keys()) | set(
            self.misses_by_pattern.keys()
        ):
            hits = self.hits_by_pattern.get(pattern, 0)
            misses = self.misses_by_pattern.get(pattern, 0)
            total = hits + misses
            if total > 0:
                pattern_stats.append(
                    {
                        "pattern": pattern,
                        "hits": hits,
                        "misses": misses,
                        "hit_rate": (hits / total * 100),
                        "total_size_bytes": self.size_by_pattern.get(pattern, 0),
                    }
                )

        pattern_stats.sort(key=lambda x: x["hit_rate"], reverse=True)

        return {
            "time_window_minutes": time_window_minutes,
            "total_operations": len(recent_operations),
            "total_gets": total_gets,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate": round(hit_rate, 2),
            "response_time_ms": response_time_stats,
            "top_patterns": pattern_stats[:10],
            "errors": dict(self.errors_by_type),
            "hourly_metrics": dict(self.hourly_metrics),
        }

    def get_pattern_analysis(self, pattern: str) -> Dict[str, Any]:
        """
        Get detailed analysis for a specific cache pattern.

        Args:
            pattern: Cache key pattern to analyze

        Returns:
            Dictionary with pattern-specific metrics
        """
        pattern_operations = [
            op for op in self.cache_operations if op.get("pattern") == pattern
        ]

        if not pattern_operations:
            return {
                "pattern": pattern,
                "message": "No operations found for this pattern",
            }

        hits = sum(1 for op in pattern_operations if op.get("hit", False))
        misses = sum(
            1
            for op in pattern_operations
            if op["operation"] == "get" and not op.get("hit", False)
        )
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        response_times = [
            op["response_time_ms"]
            for op in pattern_operations
            if op.get("response_time_ms") is not None
        ]

        sizes = [
            op["size_bytes"]
            for op in pattern_operations
            if op.get("size_bytes") is not None
        ]

        return {
            "pattern": pattern,
            "total_operations": len(pattern_operations),
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hit_rate, 2),
            "avg_response_time_ms": (
                statistics.mean(response_times) if response_times else None
            ),
            "avg_size_bytes": statistics.mean(sizes) if sizes else None,
            "total_size_bytes": sum(sizes) if sizes else 0,
        }

    def reset_statistics(self) -> None:
        """Reset all statistics"""
        self.response_times.clear()
        self.cache_operations.clear()
        self.hits_by_pattern.clear()
        self.misses_by_pattern.clear()
        self.size_by_pattern.clear()
        self.errors_by_type.clear()
        self.hourly_metrics.clear()


# Global analytics instance
_cache_analytics = CacheAnalytics()


def get_cache_analytics() -> CacheAnalytics:
    """Get singleton cache analytics instance"""
    return _cache_analytics
