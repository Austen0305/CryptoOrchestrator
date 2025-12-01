"""
Background Jobs Monitoring Routes
Monitor Celery tasks and background job status
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/background-jobs", tags=["Background Jobs"])


class JobStatus(BaseModel):
    """Job status information"""
    job_id: str
    status: str  # pending, started, success, failure, retry
    task_name: str
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0


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
async def get_jobs_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get overall background jobs status"""
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
async def get_active_tasks(
    current_user: dict = Depends(get_current_user)
) -> List[JobStatus]:
    """Get list of active background tasks"""
    try:
        tasks = []
        try:
            from ..celery_app import celery_app
            inspect = celery_app.control.inspect()
            
            # Get active tasks
            active = inspect.active()
            if active:
                for worker, task_list in active.items():
                    for task in task_list:
                        tasks.append(JobStatus(
                            job_id=task.get('id', 'unknown'),
                            status='started',
                            task_name=task.get('name', 'unknown'),
                            started_at=datetime.fromtimestamp(task.get('time_start', 0)) if task.get('time_start') else None,
                            progress=task.get('kwargs', {}).get('progress', None)
                        ))
            
            # Get scheduled tasks
            scheduled = inspect.scheduled()
            if scheduled:
                for worker, task_list in scheduled.items():
                    for task in task_list:
                        tasks.append(JobStatus(
                            job_id=task.get('request', {}).get('id', 'unknown'),
                            status='pending',
                            task_name=task.get('request', {}).get('task', 'unknown'),
                            created_at=datetime.fromtimestamp(task.get('eta', 0)) if task.get('eta') else None
                        ))
        except Exception as e:
            logger.warning(f"Celery inspection failed: {e}")
        
        return tasks
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get active tasks")


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
) -> JobStatus:
    """Get status of a specific background task"""
    try:
        from ..celery_app import celery_app
        
        # Get task result from Celery result backend
        result = celery_app.AsyncResult(task_id)
        
        if result.state == 'PENDING':
            # Task is pending or doesn't exist
            raise HTTPException(status_code=404, detail="Task not found or pending")
        
        # Get task info
        task_info = result.info if result.info else {}
        
        return JobStatus(
            job_id=task_id,
            status=result.state.lower(),
            task_name=task_info.get('task_name', 'unknown'),
            result=task_info.get('result') if result.successful() else None,
            error=str(task_info) if result.failed() else None,
            progress=task_info.get('progress', None),
            completed_at=datetime.utcnow() if result.ready() else None
        )
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="Celery not available")
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/stats")
async def get_jobs_statistics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get background jobs statistics"""
    try:
        return {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_duration_seconds": 0.0,
            "tasks_by_type": {},
        }
    except Exception as e:
        logger.error(f"Error getting jobs statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get jobs statistics")

