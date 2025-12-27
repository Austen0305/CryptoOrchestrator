"""
Database Query Optimizer
Provides query optimization utilities and connection pool monitoring
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from functools import wraps
import time

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Service for optimizing database queries and monitoring performance"""

    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self._setup_query_logging()

    def _setup_query_logging(self):
        """Setup SQLAlchemy event listeners for query monitoring"""

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total = time.time() - conn.info["query_start_time"].pop(-1)

            # Log slow queries
            if total > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {total:.3f}s\n"
                    f"Query: {statement[:200]}..."
                )

            # Track query statistics
            query_key = statement[:100]  # Use first 100 chars as key
            if query_key not in self.query_stats:
                self.query_stats[query_key] = {
                    "count": 0,
                    "total_time": 0.0,
                    "min_time": float("inf"),
                    "max_time": 0.0,
                    "last_executed": None,
                }

            stats = self.query_stats[query_key]
            stats["count"] += 1
            stats["total_time"] += total
            stats["min_time"] = min(stats["min_time"], total)
            stats["max_time"] = max(stats["max_time"], total)
            stats["last_executed"] = datetime.utcnow()

    async def get_pool_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get database connection pool statistics"""
        try:
            pool = db.bind.pool if hasattr(db.bind, "pool") else None
            if not pool:
                return {"error": "Pool not available"}

            return {
                "size": pool.size(),
                "checked_out": pool.checkedout(),
                "checked_in": pool.checkedin(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "available": pool.size() - pool.checkedout(),
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {"error": str(e)}

    async def analyze_slow_queries(
        self, limit: int = 10, min_executions: int = 5
    ) -> List[Dict[str, Any]]:
        """Analyze and return slow query statistics"""
        slow_queries = []

        for query_key, stats in self.query_stats.items():
            if stats["count"] < min_executions:
                continue

            avg_time = stats["total_time"] / stats["count"]

            if avg_time > self.slow_query_threshold:
                slow_queries.append(
                    {
                        "query_preview": query_key,
                        "executions": stats["count"],
                        "avg_time_ms": round(avg_time * 1000, 2),
                        "min_time_ms": round(stats["min_time"] * 1000, 2),
                        "max_time_ms": round(stats["max_time"] * 1000, 2),
                        "total_time_ms": round(stats["total_time"] * 1000, 2),
                        "last_executed": (
                            stats["last_executed"].isoformat()
                            if stats["last_executed"]
                            else None
                        ),
                    }
                )

        # Sort by average time descending
        slow_queries.sort(key=lambda x: x["avg_time_ms"], reverse=True)

        return slow_queries[:limit]

    async def optimize_query(
        self,
        db: AsyncSession,
        query: str,
        use_index: bool = True,
        explain: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze and optimize a query

        Args:
            db: Database session
            query: SQL query to optimize
            use_index: Whether to suggest index usage
            explain: Whether to return EXPLAIN plan

        Returns:
            Dict with optimization suggestions
        """
        suggestions = []

        # Get EXPLAIN plan if requested
        explain_plan = None
        if explain:
            try:
                result = await db.execute(text(f"EXPLAIN ANALYZE {query}"))
                explain_plan = [row[0] for row in result.fetchall()]
            except Exception as e:
                logger.warning(f"Could not get EXPLAIN plan: {e}")

        # Basic optimization suggestions
        query_lower = query.lower()

        # Check for missing WHERE clause on large tables
        if "select" in query_lower and "where" not in query_lower:
            suggestions.append(
                {
                    "type": "warning",
                    "message": "Query missing WHERE clause - may scan entire table",
                    "suggestion": "Add appropriate WHERE clause to filter results",
                }
            )

        # Check for SELECT *
        if "select *" in query_lower:
            suggestions.append(
                {
                    "type": "info",
                    "message": "Using SELECT * - consider selecting only needed columns",
                    "suggestion": "Specify column names instead of *",
                }
            )

        # Check for missing indexes
        if use_index and "where" in query_lower:
            # This is a simplified check - in production would analyze actual indexes
            suggestions.append(
                {
                    "type": "info",
                    "message": "Ensure WHERE clause columns are indexed",
                    "suggestion": "Check if columns in WHERE clause have indexes",
                }
            )

        # Check for JOIN without ON clause
        if "join" in query_lower and "on" not in query_lower:
            suggestions.append(
                {
                    "type": "error",
                    "message": "JOIN without ON clause",
                    "suggestion": "Add explicit ON clause to JOIN",
                }
            )

        return {
            "query": query[:200],  # Preview
            "suggestions": suggestions,
            "explain_plan": explain_plan,
            "optimization_score": self._calculate_optimization_score(suggestions),
        }

    def _calculate_optimization_score(self, suggestions: List[Dict]) -> int:
        """Calculate optimization score (0-100, higher is better)"""
        score = 100

        for suggestion in suggestions:
            if suggestion["type"] == "error":
                score -= 30
            elif suggestion["type"] == "warning":
                score -= 15
            elif suggestion["type"] == "info":
                score -= 5

        return max(0, score)

    async def get_query_statistics(self) -> Dict[str, Any]:
        """Get overall query statistics"""
        total_queries = sum(stats["count"] for stats in self.query_stats.values())
        total_time = sum(stats["total_time"] for stats in self.query_stats.values())

        return {
            "total_queries": total_queries,
            "unique_queries": len(self.query_stats),
            "total_time_seconds": round(total_time, 2),
            "avg_time_per_query_ms": round(
                (total_time / total_queries * 1000) if total_queries > 0 else 0, 2
            ),
            "slow_query_threshold_seconds": self.slow_query_threshold,
            "slow_queries_count": len(
                [
                    q
                    for q in self.query_stats.values()
                    if (q["total_time"] / q["count"]) > self.slow_query_threshold
                ]
            ),
        }


# Global query optimizer instance
query_optimizer = QueryOptimizer()


def optimize_query_execution(func):
    """
    Decorator to optimize query execution with caching and monitoring

    Usage:
        @optimize_query_execution
        async def get_user_data(user_id: int, db: AsyncSession):
            # Your query here
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log if slow
            if execution_time > query_optimizer.slow_query_threshold:
                logger.warning(
                    f"Slow function execution: {func.__name__} took {execution_time:.3f}s"
                )

            return result
        except Exception as e:
            logger.error(f"Query execution failed in {func.__name__}: {e}")
            raise

    return wrapper
