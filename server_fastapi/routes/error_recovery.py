"""
Error Recovery Management Routes
Provides endpoints for monitoring and managing error recovery systems
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..middleware.auth import get_current_user
from ..utils.error_recovery import error_recovery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/error-recovery", tags=["Error Recovery"])


@router.get("/circuit-breakers")
async def get_circuit_breakers(
    current_user: dict = Depends(get_current_user),
):
    """Get status of all circuit breakers"""
    try:
        breakers = {}
        for name, cb in error_recovery.circuit_breakers.items():
            breakers[name] = cb.get_state()
        return breakers
    except Exception as e:
        logger.error(f"Error getting circuit breakers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breakers: {str(e)}",
        )


@router.get("/circuit-breakers/{name}")
async def get_circuit_breaker(
    name: str,
    current_user: dict = Depends(get_current_user),
):
    """Get status of specific circuit breaker"""
    try:
        cb = error_recovery.get_circuit_breaker(name)
        if not cb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker not found: {name}",
            )
        return cb.get_state()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breaker: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker: {str(e)}",
        )


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    current_user: dict = Depends(get_current_user),
):
    """Reset a circuit breaker (admin only)"""
    # Admin check
    if current_user.get("role") != "admin" and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    try:
        cb = error_recovery.get_circuit_breaker(name)
        if not cb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker not found: {name}",
            )
        cb.reset()
        return {"message": f"Circuit breaker {name} reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}",
        )
