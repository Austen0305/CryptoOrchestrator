"""
Circuit Breaker Metrics and Management Endpoint
Provides visibility into circuit breaker health
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/circuit-breakers", tags=["monitoring"])


class CircuitBreakerStats(BaseModel):
    """Circuit breaker statistics response"""

    name: str
    state: str
    failure_count: int
    success_count: int
    last_failure_time: str | None
    failure_threshold: int
    timeout: int
    current_backoff: int
    success_rate: float
    health_score: float
    history_size: int


class CircuitBreakerSummary(BaseModel):
    """Overall circuit breaker system summary"""

    total_breakers: int
    healthy: int
    degraded: int
    open: int
    average_health_score: float
    breakers: List[CircuitBreakerStats]


@router.get("/stats", response_model=CircuitBreakerSummary)
async def get_circuit_breaker_stats():
    """
    Get statistics for all circuit breakers

    Returns comprehensive metrics including:
    - Circuit state (CLOSED, HALF_OPEN, OPEN)
    - Failure/success counts
    - Success rate and health score
    - Exponential backoff timing
    """
    try:
        from ..middleware.circuit_breaker import (
            exchange_breaker,
            database_breaker,
            ml_service_breaker,
        )

        breakers = [exchange_breaker, database_breaker, ml_service_breaker]
        stats = [CircuitBreakerStats(**breaker.get_stats()) for breaker in breakers]

        # Calculate summary metrics
        open_count = sum(1 for s in stats if s.state == "open")
        healthy_count = sum(1 for s in stats if s.health_score >= 80)
        degraded_count = sum(1 for s in stats if 50 <= s.health_score < 80)
        avg_health = sum(s.health_score for s in stats) / len(stats) if stats else 100.0

        return CircuitBreakerSummary(
            total_breakers=len(stats),
            healthy=healthy_count,
            degraded=degraded_count,
            open=open_count,
            average_health_score=round(avg_health, 2),
            breakers=stats,
        )

    except Exception as e:
        logger.error(f"Error fetching circuit breaker stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve circuit breaker statistics"
        )


@router.post("/{name}/reset")
async def reset_circuit_breaker(name: str):
    """
    Manually reset a circuit breaker

    Use this endpoint to force a circuit breaker back to CLOSED state
    after resolving the underlying issue.
    """
    try:
        from ..middleware.circuit_breaker import (
            exchange_breaker,
            database_breaker,
            ml_service_breaker,
        )

        breaker_map = {
            "exchange_api": exchange_breaker,
            "database": database_breaker,
            "ml_service": ml_service_breaker,
        }

        if name not in breaker_map:
            raise HTTPException(
                status_code=404, detail=f"Circuit breaker '{name}' not found"
            )

        breaker = breaker_map[name]
        breaker.reset()

        logger.info(f"Circuit breaker '{name}' manually reset")

        return {
            "message": f"Circuit breaker '{name}' has been reset",
            "stats": breaker.get_stats(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker '{name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to reset circuit breaker '{name}'"
        )


@router.get("/{name}")
async def get_circuit_breaker_detail(name: str):
    """Get detailed stats for a specific circuit breaker"""
    try:
        from ..middleware.circuit_breaker import (
            exchange_breaker,
            database_breaker,
            ml_service_breaker,
        )

        breaker_map = {
            "exchange_api": exchange_breaker,
            "database": database_breaker,
            "ml_service": ml_service_breaker,
        }

        if name not in breaker_map:
            raise HTTPException(
                status_code=404, detail=f"Circuit breaker '{name}' not found"
            )

        breaker = breaker_map[name]
        return CircuitBreakerStats(**breaker.get_stats())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching circuit breaker '{name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve circuit breaker '{name}'"
        )
