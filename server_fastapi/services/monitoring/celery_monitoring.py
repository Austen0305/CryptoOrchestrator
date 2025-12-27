"""
Celery Task Monitoring Service
Tracks task execution metrics, queue depth, and task performance.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import current_app
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class CeleryMonitoringService:
    """Service for monitoring Celery tasks"""

    def __init__(self):
        self.task_metrics: Dict[str, Dict[str, Any]] = {}

    async def get_task_metrics(
        self, task_name: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get task execution metrics

        Args:
            task_name: Optional task name filter
            hours: Time window in hours

        Returns:
            Dictionary with task metrics
        """
        try:
            inspect = current_app.control.inspect()

            # Get active tasks
            active_tasks = inspect.active() or {}

            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled() or {}

            # Get reserved tasks
            reserved_tasks = inspect.reserved() or {}

            # Get queue stats
            stats = inspect.stats() or {}

            # Aggregate metrics
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
            total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())

            return {
                "active_tasks": total_active,
                "scheduled_tasks": total_scheduled,
                "reserved_tasks": total_reserved,
                "workers": len(stats),
                "worker_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting Celery metrics: {e}", exc_info=True)
            return {
                "active_tasks": 0,
                "scheduled_tasks": 0,
                "reserved_tasks": 0,
                "workers": 0,
                "error": str(e),
            }

    async def get_queue_depth(self) -> Dict[str, int]:
        """Get queue depth for each priority queue"""
        try:
            inspect = current_app.control.inspect()
            active = inspect.active() or {}

            queue_depths = {
                "high_priority": 0,
                "medium_priority": 0,
                "low_priority": 0,
                "default": 0,
            }

            # Count tasks by queue
            for worker, tasks in active.items():
                for task in tasks:
                    queue = task.get("delivery_info", {}).get("routing_key", "default")
                    if queue in queue_depths:
                        queue_depths[queue] += 1
                    else:
                        queue_depths["default"] += 1

            return queue_depths
        except Exception as e:
            logger.error(f"Error getting queue depth: {e}", exc_info=True)
            return {}

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task"""
        try:
            result = AsyncResult(task_id, app=current_app)

            return {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
            }
        except Exception as e:
            logger.error(f"Error getting task status: {e}", exc_info=True)
            return {"task_id": task_id, "status": "UNKNOWN", "error": str(e)}

    def record_task_execution(
        self, task_name: str, duration_seconds: float, success: bool
    ) -> None:
        """Record task execution for metrics"""
        if task_name not in self.task_metrics:
            self.task_metrics[task_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "min_duration": float("inf"),
                "max_duration": 0.0,
            }

        metrics = self.task_metrics[task_name]
        metrics["total_executions"] += 1
        metrics["total_duration"] += duration_seconds

        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1

        metrics["avg_duration"] = (
            metrics["total_duration"] / metrics["total_executions"]
        )
        metrics["min_duration"] = min(metrics["min_duration"], duration_seconds)
        metrics["max_duration"] = max(metrics["max_duration"], duration_seconds)

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics for all tasks"""
        return {"tasks": self.task_metrics, "timestamp": datetime.utcnow().isoformat()}


# Singleton instance
_celery_monitoring_service: Optional[CeleryMonitoringService] = None


def get_celery_monitoring_service() -> CeleryMonitoringService:
    """Get Celery monitoring service instance"""
    global _celery_monitoring_service
    if _celery_monitoring_service is None:
        _celery_monitoring_service = CeleryMonitoringService()
    return _celery_monitoring_service
