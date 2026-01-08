"""
Task Rate Limiting Utilities
Implements rate limiting for Celery tasks to prevent resource exhaustion.
"""

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class TaskRateLimiter:
    """
    Rate limiter for Celery tasks to prevent overwhelming resources.
    """

    def __init__(self) -> None:
        # Rate limit configuration: {task_name: (max_calls, time_window_seconds)}
        self.rate_limits: dict[str, tuple[int, int]] = {}
        # Request history: {task_name: deque of timestamps}
        self.request_history: dict[str, deque] = {}

    def set_rate_limit(
        self, task_name: str, max_calls: int, time_window_seconds: int
    ) -> None:
        """
        Set rate limit for a task.

        Args:
            task_name: Task name pattern (supports wildcards)
            max_calls: Maximum number of calls allowed
            time_window_seconds: Time window in seconds
        """
        self.rate_limits[task_name] = (max_calls, time_window_seconds)
        if task_name not in self.request_history:
            self.request_history[task_name] = deque()

        logger.info(
            f"Rate limit set for {task_name}: {max_calls} calls per {time_window_seconds}s"
        )

    def check_rate_limit(self, task_name: str) -> tuple[bool, str | None]:
        """
        Check if task execution is allowed under rate limit.

        Args:
            task_name: Task name to check

        Returns:
            Tuple of (allowed, error_message)
        """
        # Find matching rate limit (exact match or pattern match)
        matching_limit = None
        for pattern, limit_config in self.rate_limits.items():
            if pattern == task_name or self._matches_pattern(task_name, pattern):
                matching_limit = limit_config
                break

        if not matching_limit:
            # No rate limit configured
            return True, None

        max_calls, time_window = matching_limit
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=time_window)

        # Get request history for this task
        if task_name not in self.request_history:
            self.request_history[task_name] = deque()

        history = self.request_history[task_name]

        # Remove old entries
        while history and history[0] < cutoff_time:
            history.popleft()

        # Check if limit exceeded
        if len(history) >= max_calls:
            retry_after = (
                history[0] + timedelta(seconds=time_window) - now
            ).total_seconds()
            error_msg = (
                f"Rate limit exceeded for {task_name}: "
                f"{max_calls} calls per {time_window}s. "
                f"Retry after {retry_after:.1f}s"
            )
            return False, error_msg

        # Record request
        history.append(now)
        return True, None

    def _matches_pattern(self, task_name: str, pattern: str) -> bool:
        """
        Check if task name matches pattern (supports wildcards).

        Args:
            task_name: Task name
            pattern: Pattern with wildcards (e.g., 'tasks.*')

        Returns:
            True if matches
        """
        if "*" in pattern:
            # Simple wildcard matching
            pattern_parts = pattern.split("*")
            if len(pattern_parts) == 2:
                return task_name.startswith(pattern_parts[0]) and task_name.endswith(
                    pattern_parts[1]
                )
            elif len(pattern_parts) == 1:
                return task_name.startswith(pattern_parts[0]) or task_name.endswith(
                    pattern_parts[0]
                )
        return task_name == pattern

    def get_rate_limit_status(self, task_name: str) -> dict[str, Any]:
        """
        Get current rate limit status for a task.

        Args:
            task_name: Task name

        Returns:
            Dictionary with rate limit status
        """
        matching_limit = None
        for pattern, limit_config in self.rate_limits.items():
            if pattern == task_name or self._matches_pattern(task_name, pattern):
                matching_limit = limit_config
                break

        if not matching_limit:
            return {
                "task_name": task_name,
                "rate_limited": False,
                "message": "No rate limit configured",
            }

        max_calls, time_window = matching_limit
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=time_window)

        history = self.request_history.get(task_name, deque())

        # Remove old entries
        while history and history[0] < cutoff_time:
            history.popleft()

        current_calls = len(history)
        remaining_calls = max(0, max_calls - current_calls)

        return {
            "task_name": task_name,
            "rate_limited": True,
            "max_calls": max_calls,
            "time_window_seconds": time_window,
            "current_calls": current_calls,
            "remaining_calls": remaining_calls,
            "reset_after_seconds": (
                (history[0] + timedelta(seconds=time_window) - now).total_seconds()
                if history
                else 0
            ),
        }

    def reset_rate_limit(self, task_name: str) -> None:
        """
        Reset rate limit history for a task.

        Args:
            task_name: Task name
        """
        if task_name in self.request_history:
            self.request_history[task_name].clear()
            logger.info(f"Rate limit history reset for {task_name}")


# Global rate limiter instance
_task_rate_limiter = TaskRateLimiter()


def get_task_rate_limiter() -> TaskRateLimiter:
    """Get singleton task rate limiter instance"""
    return _task_rate_limiter
