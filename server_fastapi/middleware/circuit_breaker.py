"""
Advanced Circuit Breaker Pattern Implementation
Protects external services from cascading failures
"""
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Enhanced circuit breaker with exponential backoff and health scoring
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        result = await breaker.call(api_function, *args, **kwargs)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "default",
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.success_rate_history: List[bool] = []
        self.health_score: float = 100.0
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Will retry after {self._get_backoff_time()} seconds."
                )
        
        # Limit calls in HALF_OPEN state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' half-open call limit reached"
                )
            self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        backoff = self._get_backoff_time()
        return elapsed >= backoff
    
    def _get_backoff_time(self) -> int:
        """Calculate exponential backoff time"""
        # Exponential backoff: timeout * (2 ^ failures) capped at 10x timeout
        failures_over_threshold = max(0, self.failure_count - self.failure_threshold)
        backoff = self.timeout * (2 ** min(failures_over_threshold, 5))
        return min(backoff, self.timeout * 10)
    
    def _on_success(self):
        """Handle successful call with health score tracking"""
        self.success_rate_history.append(True)
        self._trim_history()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # Need configured successes to fully close
            if self.success_count >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.failure_count = 0
                self.health_score = min(100.0, self.health_score + 10)
                logger.info(f"Circuit breaker '{self.name}' is now CLOSED")
        
        elif self.state == CircuitState.CLOSED:
            # Decay failure count on success
            self.failure_count = max(0, self.failure_count - 1)
            self.health_score = min(100.0, self.health_score + 2)
    
    def _on_failure(self):
        """Handle failed call with health score degradation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0
        self.success_rate_history.append(False)
        self._trim_history()
        self.health_score = max(0, self.health_score - 5)
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker '{self.name}' is now OPEN after "
                f"{self.failure_count} failures"
            )
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' reopened after failure in HALF_OPEN state")
    
    def _trim_history(self):
        """Keep only recent history for success rate calculation"""
        if len(self.success_rate_history) > 100:
            self.success_rate_history = self.success_rate_history[-100:]
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self.success_rate_history = []
        self.health_score = 100.0
        logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN
    
    def get_stats(self) -> dict:
        """Get current circuit breaker statistics with enhanced metrics"""
        success_rate = (
            sum(self.success_rate_history) / len(self.success_rate_history) * 100
            if self.success_rate_history else 100.0
        )
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout,
            "current_backoff": self._get_backoff_time(),
            "success_rate": round(success_rate, 2),
            "health_score": round(self.health_score, 2),
            "history_size": len(self.success_rate_history)
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests"""
    pass


# Global circuit breakers for common services
exchange_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="exchange_api"
)

database_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30,
    name="database"
)

ml_service_breaker = CircuitBreaker(
    failure_threshold=10,
    timeout=120,
    name="ml_service"
)
