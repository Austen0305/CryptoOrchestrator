"""
Error Recovery Mechanisms
Provides automatic error recovery, retry logic, and circuit breakers
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RecoveryStrategy(str, Enum):
    """Error recovery strategies"""

    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    EXPONENTIAL_BACKOFF = "exponential_backoff"


@dataclass
class RetryConfig:
    """Retry configuration"""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class CircuitBreaker:
    """
    Circuit breaker pattern implementation

    Features:
    - Automatic failure detection
    - State management (closed, open, half-open)
    - Automatic recovery
    - Configurable thresholds
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "closed"  # closed, open, half-open
        self.success_count = 0
        self.half_open_threshold = 2

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker"""
        if self.state == "open":
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now(UTC) - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "half-open"
                    self.success_count = 0
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker"""
        if self.state == "open" and self.last_failure_time:
            elapsed = (datetime.now(UTC) - self.last_failure_time).total_seconds()
            if elapsed >= self.recovery_timeout:
                self.state = "half-open"
                self.success_count = 0
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        if self.state == "half-open":
            self.success_count += 1
            if self.success_count >= self.half_open_threshold:
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED - service recovered")
        elif self.state == "closed":
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        if self.state == "half-open":
            self.state = "open"
            logger.warning("Circuit breaker OPEN - service failed in half-open state")
        elif self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker OPEN - {self.failure_count} failures")

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "success_count": self.success_count,
        }

    def reset(self):
        """Reset circuit breaker"""
        self.state = "closed"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class ErrorRecovery:
    """
    Error recovery manager

    Features:
    - Automatic retries
    - Exponential backoff
    - Circuit breakers
    - Fallback functions
    - Error classification
    """

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_configs: dict[str, RetryConfig] = {}

    def register_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        """Register a circuit breaker"""
        self.circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    def register_retry_config(self, name: str, config: RetryConfig):
        """Register retry configuration"""
        self.retry_configs[name] = config

    async def retry_with_backoff(
        self,
        func: Callable,
        config: RetryConfig | None = None,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs,
    ) -> Any:
        """Retry function with exponential backoff"""
        config = config or RetryConfig()

        last_exception = None
        for attempt in range(config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < config.max_attempts - 1:
                    # Calculate delay
                    delay = min(
                        config.initial_delay * (config.exponential_base**attempt),
                        config.max_delay,
                    )

                    # Add jitter
                    if config.jitter:
                        import random

                        delay *= 0.5 + random.random() * 0.5

                    logger.warning(
                        f"Retry attempt {attempt + 1}/{config.max_attempts} after {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed: {e}")
                    raise

        raise last_exception

    async def execute_with_fallback(
        self,
        primary: Callable,
        fallback: Callable,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs,
    ) -> Any:
        """Execute function with fallback"""
        try:
            if asyncio.iscoroutinefunction(primary):
                return await primary(*args, **kwargs)
            else:
                return primary(*args, **kwargs)
        except exceptions as e:
            logger.warning(f"Primary function failed, using fallback: {e}")
            try:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                else:
                    return fallback(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback function also failed: {fallback_error}")
                raise

    def get_circuit_breaker(self, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)


# Global error recovery instance
error_recovery = ErrorRecovery()

# Register default circuit breakers
error_recovery.register_circuit_breaker(
    "database", failure_threshold=5, recovery_timeout=60.0
)
error_recovery.register_circuit_breaker(
    "redis", failure_threshold=3, recovery_timeout=30.0
)
error_recovery.register_circuit_breaker(
    "external_api", failure_threshold=5, recovery_timeout=120.0
)


# Decorator for automatic retry
def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for automatic retry on error"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(max_attempts=max_attempts, initial_delay=delay)
            return await error_recovery.retry_with_backoff(
                func, config=config, exceptions=exceptions, *args, **kwargs
            )

        return wrapper

    return decorator


# Decorator for circuit breaker
def circuit_breaker(name: str):
    """Decorator for circuit breaker"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cb = error_recovery.get_circuit_breaker(name)
            if cb:
                return await cb.call_async(func, *args, **kwargs)
            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
