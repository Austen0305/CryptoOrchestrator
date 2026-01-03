"""
Performance Profiling Service
Identifies slow endpoints and slow database queries.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Slow query threshold (100ms as per plan)
SLOW_QUERY_THRESHOLD_MS = 100

# Slow endpoint threshold (200ms p95 as per plan)
SLOW_ENDPOINT_THRESHOLD_MS = 200


class PerformanceProfiler:
    """Service for performance profiling and slow query/endpoint detection"""

    def __init__(self):
        self.slow_queries: List[Dict[str, Any]] = []
        self.slow_endpoints: List[Dict[str, Any]] = []
        self.query_times: Dict[str, List[float]] = defaultdict(list)
        self.endpoint_times: Dict[str, List[float]] = defaultdict(list)
        self.max_entries = 1000  # Keep last 1000 entries

    def record_query(
        self, query: str, duration_ms: float, params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a database query execution time"""
        self.query_times[query].append(duration_ms)

        # Keep only last N entries per query
        if len(self.query_times[query]) > self.max_entries:
            self.query_times[query] = self.query_times[query][-self.max_entries :]

        # Log slow queries
        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            slow_query = {
                "query": query[:200],  # Truncate long queries
                "duration_ms": duration_ms,
                "params": str(params)[:200] if params else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.slow_queries.append(slow_query)

            # Keep only last N slow queries
            if len(self.slow_queries) > self.max_entries:
                self.slow_queries = self.slow_queries[-self.max_entries :]

            # Enhanced structured logging (2026 best practice)
            logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms",
                extra={
                    "query": query[:200],
                    "duration_ms": duration_ms,
                    "threshold_ms": SLOW_QUERY_THRESHOLD_MS,
                    "query_preview": query[:100],
                    "has_params": params is not None,
                },
            )

    def record_endpoint(
        self, method: str, path: str, duration_ms: float, status_code: int
    ) -> None:
        """Record an endpoint execution time"""
        endpoint_key = f"{method} {path}"
        self.endpoint_times[endpoint_key].append(duration_ms)

        # Keep only last N entries per endpoint
        if len(self.endpoint_times[endpoint_key]) > self.max_entries:
            self.endpoint_times[endpoint_key] = self.endpoint_times[endpoint_key][
                -self.max_entries :
            ]

        # Calculate p95
        times = self.endpoint_times[endpoint_key]
        if len(times) >= 20:  # Need at least 20 samples for p95
            sorted_times = sorted(times)
            p95_index = int(len(sorted_times) * 0.95)
            p95 = sorted_times[p95_index]

            # Log slow endpoints (p95 > threshold)
            if p95 > SLOW_ENDPOINT_THRESHOLD_MS:
                slow_endpoint = {
                    "method": method,
                    "path": path,
                    "p95_ms": p95,
                    "avg_ms": sum(times) / len(times),
                    "max_ms": max(times),
                    "count": len(times),
                    "status_code": status_code,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Avoid duplicates (check if already logged recently)
                recent = [
                    e
                    for e in self.slow_endpoints
                    if e["method"] == method
                    and e["path"] == path
                    and (
                        datetime.utcnow() - datetime.fromisoformat(e["timestamp"])
                    ).total_seconds()
                    < 300
                ]

                if not recent:
                    self.slow_endpoints.append(slow_endpoint)

                    # Keep only last N slow endpoints
                    if len(self.slow_endpoints) > self.max_entries:
                        self.slow_endpoints = self.slow_endpoints[-self.max_entries :]

                    logger.warning(
                        f"Slow endpoint detected (p95): {p95:.2f}ms - {method} {path}",
                        extra={
                            "method": method,
                            "path": path,
                            "p95_ms": p95,
                            "avg_ms": slow_endpoint["avg_ms"],
                            "threshold_ms": SLOW_ENDPOINT_THRESHOLD_MS,
                        },
                    )

    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get slow queries sorted by duration"""
        return sorted(self.slow_queries, key=lambda x: x["duration_ms"], reverse=True)[
            :limit
        ]

    def get_slow_endpoints(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get slow endpoints sorted by p95"""
        return sorted(
            self.slow_endpoints, key=lambda x: x.get("p95_ms", 0), reverse=True
        )[:limit]

    def get_query_statistics(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for queries"""
        if query:
            times = self.query_times.get(query, [])
        else:
            # Aggregate all queries
            all_times = []
            for times_list in self.query_times.values():
                all_times.extend(times_list)
            times = all_times

        if not times:
            return {
                "count": 0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p95_ms": 0.0,
            }

        sorted_times = sorted(times)
        p95_index = int(len(sorted_times) * 0.95)

        return {
            "count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": sorted_times[p95_index] if sorted_times else 0.0,
        }

    def get_endpoint_statistics(
        self, method: Optional[str] = None, path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics for endpoints"""
        if method and path:
            endpoint_key = f"{method} {path}"
            times = self.endpoint_times.get(endpoint_key, [])
        else:
            # Aggregate all endpoints
            all_times = []
            for times_list in self.endpoint_times.values():
                all_times.extend(times_list)
            times = all_times

        if not times:
            return {
                "count": 0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p95_ms": 0.0,
            }

        sorted_times = sorted(times)
        p95_index = int(len(sorted_times) * 0.95)

        return {
            "count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": sorted_times[p95_index] if sorted_times else 0.0,
        }

    def clear_old_entries(self, max_age_hours: int = 24) -> None:
        """Clear old profiling entries"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        # Clear old slow queries
        self.slow_queries = [
            q
            for q in self.slow_queries
            if datetime.fromisoformat(q["timestamp"]) > cutoff
        ]

        # Clear old slow endpoints
        self.slow_endpoints = [
            e
            for e in self.slow_endpoints
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]


# Singleton instance
_performance_profiler: Optional[PerformanceProfiler] = None


def get_performance_profiler() -> PerformanceProfiler:
    """Get performance profiler instance"""
    global _performance_profiler
    if _performance_profiler is None:
        _performance_profiler = PerformanceProfiler()
    return _performance_profiler


# SQLAlchemy event listener for query profiling
def setup_query_profiling(engine) -> None:
    """
    Setup SQLAlchemy query profiling

    Args:
        engine: SQLAlchemy engine (sync or async engine's sync_engine)
    """
    profiler = get_performance_profiler()

    # Handle both sync and async engines
    sync_engine = engine
    if hasattr(engine, "sync_engine"):
        sync_engine = engine.sync_engine
    elif hasattr(engine, "_sync_engine"):
        sync_engine = engine._sync_engine

    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info["query_start_time"].pop(-1)
        duration_ms = total * 1000

        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            profiler.record_query(
                query=statement, duration_ms=duration_ms, params=parameters
            )
