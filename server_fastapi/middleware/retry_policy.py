"""
Retry policy with exponential backoff for resilient service calls.
Wraps circuit breakers with intelligent retry logic.
"""

import asyncio
import logging
from typing import Callable, Any, Optional, TypeVar, List
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryPolicy:
    """
    Configurable retry policy with exponential backoff and jitter.

    Features:
    - Exponential backoff with configurable base delay
    - Jitter to prevent thundering herd
    - Maximum retry attempts
    - Configurable exceptions to retry on
    - Dead-letter channel for permanent failures
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,),
        dead_letter_callback: Optional[Callable] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.dead_letter_callback = dead_letter_callback

    async def execute(self, func: Callable[[], Any], *args, **kwargs) -> Any:
        """
        Execute function with retry policy.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from function execution

        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        attempts = 0

        for attempt in range(self.max_attempts):
            attempts = attempt + 1
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                if attempts > 1:
                    logger.info(
                        f"Function {func.__name__} succeeded after {attempts} attempts"
                    )

                return result

            except self.retryable_exceptions as e:
                last_exception = e

                # Don't retry on last attempt
                if attempts >= self.max_attempts:
                    logger.error(
                        f"Function {func.__name__} failed after {attempts} attempts: {e}"
                    )

                    # Send to dead letter channel if configured
                    if self.dead_letter_callback:
                        try:
                            await self.dead_letter_callback(e, args, kwargs)
                        except Exception as dl_error:
                            logger.error(f"Dead letter callback failed: {dl_error}")

                    break

                # Calculate delay with exponential backoff
                delay = self._calculate_delay(attempts)

                logger.warning(
                    f"Function {func.__name__} failed (attempt {attempts}/{self.max_attempts}): {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )

                # Wait before retry
                await asyncio.sleep(delay)

        # Re-raise last exception if all retries failed
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay with exponential backoff and optional jitter.

        Formula: base_delay * (exponential_base ^ (attempt - 1))
        """
        import random

        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter (random 0-20% of delay) to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * 0.2 * random.random()
            delay = delay + jitter_amount

        return delay


def retry_with_policy(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
):
    """
    Decorator to apply retry policy to async functions.

    Usage:
        @retry_with_policy(max_attempts=3, base_delay=1.0)
        async def my_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            policy = RetryPolicy(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
            )
            return await policy.execute(func, *args, **kwargs)

        return wrapper

    return decorator


# Pre-configured retry policies for common use cases
exchange_retry_policy = RetryPolicy(
    max_attempts=5,
    base_delay=0.5,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(ConnectionError, TimeoutError, Exception),
)

database_retry_policy = RetryPolicy(
    max_attempts=3,
    base_delay=0.1,
    max_delay=5.0,
    exponential_base=2.0,
    jitter=False,
    retryable_exceptions=(ConnectionError, TimeoutError),
)

api_retry_policy = RetryPolicy(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(ConnectionError, TimeoutError, Exception),
)
