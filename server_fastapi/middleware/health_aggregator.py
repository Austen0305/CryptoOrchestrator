"""
Health Check Aggregation System
Aggregates health checks from multiple services and components
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result"""

    name: str
    status: HealthStatus
    message: str | None = None
    details: dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.details is None:
            self.details = {}


class HealthAggregator:
    """
    Aggregates health checks from multiple sources

    Features:
    - Multiple health check providers
    - Automatic aggregation
    - Caching
    - Timeout handling
    - Dependency tracking
    """

    def __init__(self, cache_ttl: int = 30):
        self.checkers: dict[str, Callable] = {}
        self.cache_ttl = cache_ttl
        self._cache: dict[str, Any] | None = None
        self._cache_time: datetime | None = None

    def register(self, name: str, checker: Callable):
        """Register a health check function"""
        self.checkers[name] = checker
        logger.debug(f"Health check registered: {name}")

    async def check_all(self, use_cache: bool = True) -> dict[str, Any]:
        """Run all health checks"""
        # Check cache
        if use_cache and self._cache and self._cache_time:
            age = (datetime.now(UTC) - self._cache_time).total_seconds()
            if age < self.cache_ttl:
                return self._cache

        # Run checks
        checks: list[HealthCheck] = []
        tasks = []

        for name, checker in self.checkers.items():
            tasks.append(self._run_check(name, checker))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, HealthCheck):
                checks.append(result)
            elif isinstance(result, Exception):
                checks.append(
                    HealthCheck(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=str(result),
                    )
                )

        # Aggregate status
        overall_status = self._aggregate_status(checks)

        # Build response
        response = {
            "status": overall_status.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "timestamp": check.timestamp.isoformat(),
                }
                for check in checks
            },
        }

        # Cache result
        self._cache = response
        self._cache_time = datetime.now(UTC)

        return response

    async def _run_check(self, name: str, checker: Callable) -> HealthCheck:
        """Run a single health check with timeout"""
        try:
            if asyncio.iscoroutinefunction(checker):
                result = await asyncio.wait_for(checker(), timeout=5.0)
            else:
                result = checker()

            # Handle different return types
            if isinstance(result, HealthCheck):
                return result
            elif isinstance(result, dict):
                return HealthCheck(
                    name=name,
                    status=HealthStatus(result.get("status", "unknown")),
                    message=result.get("message"),
                    details=result.get("details", {}),
                )
            elif isinstance(result, bool):
                return HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                )
            else:
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Unexpected return type: {type(result)}",
                )
        except TimeoutError:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Health check timeout",
            )
        except Exception as e:
            logger.error(f"Health check error for {name}: {e}", exc_info=True)
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )

    def _aggregate_status(self, checks: list[HealthCheck]) -> HealthStatus:
        """Aggregate health check statuses"""
        if not checks:
            return HealthStatus.UNKNOWN

        statuses = [check.status for check in checks]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN

    async def check(self, name: str) -> HealthCheck:
        """Check a specific health check"""
        checker = self.checkers.get(name)
        if not checker:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check not found: {name}",
            )

        return await self._run_check(name, checker)


# Global health aggregator
health_aggregator = HealthAggregator()


# Register common health checks
async def check_database():
    """Check database health"""
    try:
        from sqlalchemy import text

        from ..database.session import get_db_context

        async with get_db_context() as session:
            await session.execute(text("SELECT 1"))
        return HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection OK",
        )
    except Exception as e:
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {e}",
        )


async def check_redis():
    """Check Redis health"""
    try:
        import redis.asyncio as redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url)
        await client.ping()
        await client.close()
        return HealthCheck(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis connection OK",
        )
    except Exception as e:
        return HealthCheck(
            name="redis",
            status=HealthStatus.DEGRADED,
            message=f"Redis unavailable: {e}",
        )


import os

# Register default health checks
health_aggregator.register("database", check_database)
if os.getenv("REDIS_ENABLED", "false").lower() == "true":
    health_aggregator.register("redis", check_redis)
