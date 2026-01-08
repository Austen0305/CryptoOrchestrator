"""
Middleware Profiling Endpoints
Provides endpoints to view and manage middleware profiling
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies.auth import get_current_user
from ..middleware.profiling import (
    _profiling_enabled,
    clear_profiling_data,
    disable_profiling,
    enable_profiling,
    get_profiling_stats,
    get_slow_middleware,
    log_profiling_summary,
)

router = APIRouter(prefix="/api/admin/profiling", tags=["Profiling"])


@router.get("/stats")
async def get_profiling_stats_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Get middleware profiling statistics

    Requires authentication and admin role (optional check)
    """
    try:
        stats = get_profiling_stats()
        slow = get_slow_middleware(threshold=0.1)

        return {
            "enabled": _profiling_enabled,
            "stats": stats,
            "slow_middleware": [
                {"name": name, "avg_time": avg_time} for name, avg_time in slow
            ],
            "summary": {
                "total_middleware": len(stats),
                "slow_middleware_count": len(slow),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get profiling stats: {str(e)}"
        )


@router.post("/enable")
async def enable_profiling_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, str]:
    """Enable middleware profiling"""
    try:
        enable_profiling()
        return {"status": "enabled", "message": "Middleware profiling enabled"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to enable profiling: {str(e)}"
        )


@router.post("/disable")
async def disable_profiling_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, str]:
    """Disable middleware profiling"""
    try:
        disable_profiling()
        return {"status": "disabled", "message": "Middleware profiling disabled"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to disable profiling: {str(e)}"
        )


@router.post("/clear")
async def clear_profiling_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, str]:
    """Clear profiling data"""
    try:
        clear_profiling_data()
        return {"status": "cleared", "message": "Profiling data cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear profiling data: {str(e)}"
        )


@router.post("/summary")
async def log_profiling_summary_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, str]:
    """Log profiling summary to server logs"""
    try:
        await log_profiling_summary()
        return {
            "status": "logged",
            "message": "Profiling summary logged to server logs",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log summary: {str(e)}")
