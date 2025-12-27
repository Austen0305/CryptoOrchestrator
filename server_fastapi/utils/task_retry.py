"""
Task Retry Utilities
Implements intelligent retry logic with exponential backoff and circuit breakers.
"""

import logging
from typing import Callable, Optional, Any
from datetime import datetime
from enum import Enum
import time
import random

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    NO_RETRY = "no_retry"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Time to wait before attempting half-open
            success_threshold: Number of successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()

    def call(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:  # noqa: C901
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check circuit state
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    # Transition to half-open
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise Exception(
                        f"Circuit breaker is OPEN. "
                        f"Retry after {self.timeout_seconds - elapsed:.1f} seconds"
                    )

        # Execute function
        try:
            result = func(*args, **kwargs)

            # Record success
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    # Close circuit
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker CLOSED after successful recovery")

            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

            return result

        except Exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state == CircuitBreakerState.HALF_OPEN:
                # Open circuit again
                self.state = CircuitBreakerState.OPEN
                logger.warning(
                    "Circuit breaker OPENED after failure in HALF_OPEN state"
                )

            elif self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    # Open circuit
                    self.state = CircuitBreakerState.OPEN
                    logger.warning(
                        f"Circuit breaker OPENED after {self.failure_count} failures"
                    )

            raise


def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: tuple = (Exception,),
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
) -> Any:
    """
    Retry function with configurable backoff strategy.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delays
        retry_on_exceptions: Tuple of exceptions to retry on
        strategy: Retry strategy to use

    Returns:
        Function result

    Raises:
        Exception: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except retry_on_exceptions as e:
            last_exception = e

            if attempt == max_retries:
                # Last attempt failed
                logger.error(
                    f"Function failed after {max_retries} retries: {e}", exc_info=True
                )
                raise

            # Calculate delay
            if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                delay = min(initial_delay * (exponential_base**attempt), max_delay)
            elif strategy == RetryStrategy.LINEAR_BACKOFF:
                delay = min(initial_delay * (attempt + 1), max_delay)
            elif strategy == RetryStrategy.FIXED_DELAY:
                delay = initial_delay
            else:
                delay = 0

            # Add jitter
            if jitter and delay > 0:
                jitter_amount = delay * 0.1 * random.random()
                delay += jitter_amount

            logger.warning(
                f"Function failed (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {delay:.2f}s: {e}"
            )

            time.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise Exception("Retry logic error: no exception recorded")
