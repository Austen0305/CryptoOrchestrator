"""
Connection Pool Monitoring
Tracks and reports on database connection pool health and usage.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class ConnectionPoolMonitor:
    """
    Monitor database connection pool health and metrics
    """

    def __init__(self, engine: AsyncEngine | None = None):
        """
        Initialize pool monitor

        Args:
            engine: SQLAlchemy async engine to monitor
        """
        self.engine = engine
        self.metrics_history: list[dict[str, Any]] = []
        self.max_history = 1000

    async def get_pool_metrics(self) -> dict[str, Any]:
        """
        Get current connection pool metrics

        Returns:
            Dictionary with pool metrics
        """
        if not self.engine:
            return {
                "error": "Engine not configured",
                "timestamp": datetime.utcnow().isoformat(),
            }

        try:
            pool = self.engine.pool

            # Get pool statistics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "pool_size": getattr(pool, "size", None),
                "checked_in": getattr(pool, "checkedin", None),
                "checked_out": getattr(pool, "checkedout", None),
                "overflow": getattr(pool, "overflow", None),
                "invalid": getattr(pool, "invalid", None),
            }

            # Calculate derived metrics
            if metrics["pool_size"] is not None:
                metrics["available_connections"] = metrics["pool_size"] - (
                    metrics["checked_out"] or 0
                )
                metrics["utilization_percent"] = (
                    (metrics["checked_out"] or 0) / metrics["pool_size"] * 100
                    if metrics["pool_size"] > 0
                    else 0
                )

            # Get pool configuration
            metrics["config"] = {
                "pool_size": getattr(pool, "_pool_size", None),
                "max_overflow": getattr(pool, "_max_overflow", None),
                "pool_timeout": getattr(pool, "_timeout", None),
                "pool_recycle": getattr(pool, "_recycle", None),
            }

            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history :]

            return metrics

        except Exception as e:
            logger.error(f"Error getting pool metrics: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def check_pool_health(self) -> dict[str, Any]:
        """
        Check connection pool health

        Returns:
            Health status dictionary
        """
        metrics = await self.get_pool_metrics()

        if "error" in metrics:
            return {"healthy": False, "status": "error", "message": metrics["error"]}

        # Health checks
        utilization = metrics.get("utilization_percent", 0)
        checked_out = metrics.get("checked_out", 0)
        pool_size = metrics.get("pool_size", 0)

        health_status = {
            "healthy": True,
            "status": "healthy",
            "warnings": [],
            "metrics": metrics,
        }

        # Warning: High utilization (>80%)
        if utilization > 80:
            health_status["warnings"].append(
                f"High pool utilization: {utilization:.1f}%"
            )
            health_status["status"] = "degraded"

        # Warning: All connections checked out
        if checked_out >= pool_size and pool_size > 0:
            health_status["warnings"].append(
                "All connections in use - may experience connection timeouts"
            )
            health_status["status"] = "degraded"
            health_status["healthy"] = False

        # Warning: Invalid connections detected
        invalid = metrics.get("invalid", 0)
        if invalid > 0:
            health_status["warnings"].append(f"Invalid connections detected: {invalid}")
            health_status["status"] = "degraded"

        return health_status

    def get_metrics_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get historical pool metrics

        Args:
            limit: Maximum number of historical entries to return

        Returns:
            List of historical metrics
        """
        return self.metrics_history[-limit:] if limit else self.metrics_history

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        Get summary statistics from metrics history

        Returns:
            Summary statistics
        """
        if not self.metrics_history:
            return {"total_samples": 0, "message": "No metrics collected yet"}

        utilizations = [
            m.get("utilization_percent", 0)
            for m in self.metrics_history
            if "utilization_percent" in m
        ]

        checked_out_values = [
            m.get("checked_out", 0) for m in self.metrics_history if "checked_out" in m
        ]

        return {
            "total_samples": len(self.metrics_history),
            "avg_utilization": (
                sum(utilizations) / len(utilizations) if utilizations else 0
            ),
            "max_utilization": max(utilizations) if utilizations else 0,
            "min_utilization": min(utilizations) if utilizations else 0,
            "avg_checked_out": (
                sum(checked_out_values) / len(checked_out_values)
                if checked_out_values
                else 0
            ),
            "max_checked_out": max(checked_out_values) if checked_out_values else 0,
            "first_sample": self.metrics_history[0]["timestamp"],
            "last_sample": self.metrics_history[-1]["timestamp"],
        }


def get_pool_monitor(engine: AsyncEngine | None = None) -> ConnectionPoolMonitor:
    """Get singleton pool monitor instance"""
    if not hasattr(get_pool_monitor, "_instance"):
        get_pool_monitor._instance = ConnectionPoolMonitor(engine)
    elif engine and get_pool_monitor._instance.engine != engine:
        # Update engine if provided
        get_pool_monitor._instance.engine = engine
    return get_pool_monitor._instance
