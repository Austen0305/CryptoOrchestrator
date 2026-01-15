"""
Background Jobs Monitoring Routes
Monitor Celery tasks and background job status with enhanced metrics and management.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.monitoring.celery_monitoring import get_celery_monitoring_service
from ..utils.task_batching import get_task_batcher
from ..utils.task_rate_limiter import get_task_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/background-jobs", tags=["Background Jobs"])


class JobStatus(BaseModel):
    """Job status information"""

    job_id: str
    status: str  # pending, started, success, failure, retry
    task_name: str
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any | None = None
    error: str | None = None
    progress: float | None = None  # 0.0 to 1.0


def _get_active_workers() -> int:
    """Get number of active Celery workers"""
    try:
        from ..celery_app import celery_app

        inspect = celery_app.control.inspect()
        active = inspect.active()
        if active:
            return len(active)
    except Exception as e:
        logger.warning(f"Failed to get active workers: {e}")
    return 0


def _get_pending_tasks() -> int:
    """Get number of pending Celery tasks"""
    try:
        from ..celery_app import celery_app

        inspect = celery_app.control.inspect()
        reserved = inspect.reserved()
        scheduled = inspect.scheduled()

        pending = 0
        if reserved:
            pending += sum(len(tasks) for tasks in reserved.values())
        if scheduled:
            pending += sum(len(tasks) for tasks in scheduled.values())
        return pending
    except Exception as e:
        logger.warning(f"Failed to get pending tasks: {e}")
    return 0


@router.get("/status")
@cached(
    ttl=30, prefix="background_jobs_status"
)  # 30s TTL for job status (frequently changing)
async def get_jobs_status(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get overall background jobs status (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin" and "admin" not in current_user.get(
        "roles", []
    ):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Check Celery availability
        celery_available = False
        try:
            from ..celery_app import celery_app

            celery_available = celery_app is not None
        except Exception:
            pass

        return {
            "celery_available": celery_available,
            "active_workers": _get_active_workers(),
            "pending_tasks": _get_pending_tasks(),
            "completed_tasks_24h": 0,  # Would require task history tracking
            "failed_tasks_24h": 0,  # Would require task history tracking
        }
    except Exception as e:
        logger.error(f"Error getting jobs status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get jobs status")


@router.get("/tasks")
@cached(ttl=30, prefix="background_tasks")  # 30s TTL for active tasks
async def get_active_tasks(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[JobStatus]:
    """Get list of active background tasks with pagination (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin" and "admin" not in current_user.get(
        "roles", []
    ):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        tasks = []
        try:
            from ..celery_app import celery_app

            inspect = celery_app.control.inspect()

            # Get active tasks
            active = inspect.active()
            if active:
                for _worker, task_list in active.items():
                    for task in task_list:
                        tasks.append(
                            JobStatus(
                                job_id=task.get("id", "unknown"),
                                status="started",
                                task_name=task.get("name", "unknown"),
                                started_at=(
                                    datetime.fromtimestamp(task.get("time_start", 0))
                                    if task.get("time_start")
                                    else None
                                ),
                                progress=task.get("kwargs", {}).get("progress", None),
                            )
                        )

            # Get scheduled tasks
            scheduled = inspect.scheduled()
            if scheduled:
                for _worker, task_list in scheduled.items():
                    for task in task_list:
                        tasks.append(
                            JobStatus(
                                job_id=task.get("request", {}).get("id", "unknown"),
                                status="pending",
                                task_name=task.get("request", {}).get(
                                    "task", "unknown"
                                ),
                                created_at=(
                                    datetime.fromtimestamp(task.get("eta", 0))
                                    if task.get("eta")
                                    else None
                                ),
                            )
                        )
        except Exception as e:
            logger.warning(f"Celery inspection failed: {e}")

        return tasks
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get active tasks")


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> JobStatus:
    """Get status of a specific background task (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin" and "admin" not in current_user.get(
        "roles", []
    ):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from ..celery_app import celery_app

        # Get task result from Celery result backend
        result = celery_app.AsyncResult(task_id)

        if result.state == "PENDING":
            # Task is pending or doesn't exist
            raise HTTPException(status_code=404, detail="Task not found or pending")

        # Get task info
        task_info = result.info if result.info else {}

        return JobStatus(
            job_id=task_id,
            status=result.state.lower(),
            task_name=task_info.get("task_name", "unknown"),
            result=task_info.get("result") if result.successful() else None,
            error=str(task_info) if result.failed() else None,
            progress=task_info.get("progress", None),
            completed_at=datetime.now(UTC) if result.ready() else None,
        )
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="Celery not available")
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/stats")
@cached(ttl=60, prefix="background_jobs_stats")  # 60s TTL for job statistics
async def get_jobs_statistics(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get background jobs statistics (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin" and "admin" not in current_user.get(
        "roles", []
    ):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        monitoring_service = get_celery_monitoring_service()
        task_stats = monitoring_service.get_task_statistics()

        # Get queue metrics
        queue_metrics = await monitoring_service.get_task_metrics()

        return {
            "task_statistics": task_stats,
            "queue_metrics": queue_metrics,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting jobs statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get jobs statistics")


@router.get("/queue-depth")
async def get_queue_depth(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, int]:
    """Get queue depth for each priority queue (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin" and "admin" not in current_user.get(
        "roles", []
    ):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        monitoring_service = get_celery_monitoring_service()
        queue_depths = await monitoring_service.get_queue_depth()
        return queue_depths
    except Exception as e:
        logger.error(f"Error getting queue depth: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get queue depth: {str(e)}"
        )


@router.get("/batching/stats")
async def get_batching_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get task batching statistics (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        batcher = get_task_batcher()
        stats = batcher.get_batch_stats()
        return {"batches": stats, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.error(f"Error getting batching stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get batching stats: {str(e)}"
        )


@router.post("/batching/flush")
async def flush_all_batches(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Flush all pending batches (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        batcher = get_task_batcher()
        results = await batcher.flush_all_batches()
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error flushing batches: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to flush batches: {str(e)}"
        )


@router.get("/rate-limits")
async def get_rate_limits(
    current_user: Annotated[dict, Depends(get_current_user)],
    task_name: str | None = Query(None, description="Filter by task name"),
) -> dict[str, Any]:
    """Get rate limit status for tasks (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        rate_limiter = get_task_rate_limiter()

        if task_name:
            status = rate_limiter.get_rate_limit_status(task_name)
            return {"rate_limits": [status]}
        else:
            # Get all configured rate limits
            all_statuses = []
            for pattern in rate_limiter.rate_limits:
                status = rate_limiter.get_rate_limit_status(pattern)
                all_statuses.append(status)

            return {"rate_limits": all_statuses}
    except Exception as e:
        logger.error(f"Error getting rate limits: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get rate limits: {str(e)}"
        )


@router.post("/rate-limits/{task_name}/reset")
async def reset_rate_limit(
    task_name: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Reset rate limit for a task (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        rate_limiter = get_task_rate_limiter()
        rate_limiter.reset_rate_limit(task_name)
        return {
            "success": True,
            "message": f"Rate limit reset for {task_name}",
            "task_name": task_name,
        }
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to reset rate limit: {str(e)}"
        )
