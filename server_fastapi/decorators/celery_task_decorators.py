"""
Enhanced Celery Task Decorators
Provides decorators for retry logic, rate limiting, batching, and monitoring.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps

from celery import Task
from celery.exceptions import Retry

from ..services.monitoring.celery_monitoring import get_celery_monitoring_service
from ..utils.task_batching import get_task_deduplicator
from ..utils.task_rate_limiter import get_task_rate_limiter
from ..utils.task_retry import CircuitBreaker, RetryStrategy

logger = logging.getLogger(__name__)


class EnhancedTask(Task):
    """
    Enhanced Celery task base class with retry, rate limiting, and monitoring.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limiter = get_task_rate_limiter()
        self.deduplicator = get_task_deduplicator()
        self.monitoring = get_celery_monitoring_service()
        self.circuit_breaker: CircuitBreaker | None = None

    def __call__(self, *args, **kwargs):
        """Execute task with enhanced features"""
        task_name = self.name
        start_time = None

        try:
            # Check rate limit
            allowed, error_msg = self.rate_limiter.check_rate_limit(task_name)
            if not allowed:
                logger.warning(f"Task {task_name} rate limited: {error_msg}")
                raise Exception(f"Rate limit exceeded: {error_msg}")

            # Check for duplicate execution
            idempotency_key = self.deduplicator.generate_idempotency_key(
                task_name, *args, **kwargs
            )
            cached_result = self.deduplicator.check_duplicate(idempotency_key)
            if cached_result is not None:
                logger.info(f"Returning cached result for duplicate task: {task_name}")
                return cached_result

            # Execute with circuit breaker if configured
            if self.circuit_breaker:
                result = self.circuit_breaker.call(super().__call__, *args, **kwargs)
            else:
                start_time = time.time()
                result = super().__call__(*args, **kwargs)

            # Record execution
            if start_time:
                duration = time.time() - start_time
                self.monitoring.record_task_execution(task_name, duration, success=True)

            # Cache result for deduplication
            self.deduplicator.record_execution(idempotency_key, result)

            return result

        except Exception as e:
            # Record failure
            if start_time:
                duration = time.time() - start_time
                self.monitoring.record_task_execution(
                    task_name, duration, success=False
                )

            logger.error(f"Task {task_name} failed: {e}", exc_info=True)
            raise


def task_with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    retry_on_exceptions: tuple = (Exception,),
):
    """
    Decorator to add retry logic to Celery tasks.

    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        retry_strategy: Retry strategy to use
        retry_on_exceptions: Exceptions to retry on
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except retry_on_exceptions as e:
                # Use Celery's retry mechanism
                raise Retry(exc=e, countdown=initial_delay, max_retries=max_retries)

        return wrapper

    return decorator


def task_with_rate_limit(max_calls: int, time_window_seconds: int):
    """
    Decorator to add rate limiting to Celery tasks.

    Args:
        max_calls: Maximum number of calls allowed
        time_window_seconds: Time window in seconds
    """

    def decorator(func: Callable) -> Callable:
        # Set rate limit for this task
        rate_limiter = get_task_rate_limiter()
        rate_limiter.set_rate_limit(func.__name__, max_calls, time_window_seconds)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check rate limit
            allowed, error_msg = rate_limiter.check_rate_limit(func.__name__)
            if not allowed:
                raise Exception(f"Rate limit exceeded: {error_msg}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def task_with_monitoring(func: Callable) -> Callable:
    """
    Decorator to add monitoring to Celery tasks.

    Tracks execution time, success/failure, and records metrics.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        import time

        task_name = func.__name__
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Record success
            monitoring = get_celery_monitoring_service()
            monitoring.record_task_execution(task_name, duration, success=True)

            return result

        except Exception:
            duration = time.time() - start_time

            # Record failure
            monitoring = get_celery_monitoring_service()
            monitoring.record_task_execution(task_name, duration, success=False)

            raise

    return wrapper
