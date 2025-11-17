"""
Sentry Integration for Error Tracking and Monitoring
"""

import os
import logging
from typing import Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Sentry, but don't fail if not installed
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk[fastapi]")


def init_sentry(dsn: Optional[str] = None, environment: Optional[str] = None) -> bool:
    """
    Initialize Sentry error tracking.
    
    Args:
        dsn: Sentry DSN (or use SENTRY_DSN env var)
        environment: Environment name (or use ENVIRONMENT env var)
    
    Returns:
        True if Sentry was initialized, False otherwise
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not available")
        return False
    
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.warning("Sentry DSN not provided, skipping initialization")
        return False
    
    environment = environment or os.getenv("ENVIRONMENT", "development")
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,  # 10% of transactions for profiling
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        # Filter out health check noise
        ignore_errors=[
            KeyboardInterrupt,
            SystemExit,
        ],
        # Custom tags
        before_send=lambda event, hint: filter_sentry_events(event, hint),
    )
    
    logger.info(f"Sentry initialized for environment: {environment}")
    return True


def filter_sentry_events(event, hint):
    """Filter out noisy events from Sentry."""
    # Don't send events for health checks
    if event.get("request", {}).get("url", "").endswith("/health"):
        return None
    
    # Don't send events for metrics endpoints
    if "/metrics" in event.get("request", {}).get("url", ""):
        return None
    
    return event


def capture_exception(exception: Exception, **kwargs):
    """Capture an exception in Sentry."""
    if SENTRY_AVAILABLE:
        sentry_sdk.capture_exception(exception, **kwargs)
    else:
        logger.exception("Exception occurred (Sentry not available)")


def capture_message(message: str, level: str = "info", **kwargs):
    """Capture a message in Sentry."""
    if SENTRY_AVAILABLE:
        sentry_sdk.capture_message(message, level=level, **kwargs)
    else:
        logger.log(getattr(logging, level.upper(), logging.INFO), message)


def sentry_context(**tags):
    """Add context to Sentry events."""
    if SENTRY_AVAILABLE:
        sentry_sdk.set_context("custom", tags)


def sentry_user(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """Set user context for Sentry."""
    if SENTRY_AVAILABLE:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username,
        })


def sentry_trace(func):
    """Decorator to trace function execution in Sentry."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if SENTRY_AVAILABLE:
            with sentry_sdk.start_transaction(op="function", name=func.__name__):
                return await func(*args, **kwargs)
        else:
            return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if SENTRY_AVAILABLE:
            with sentry_sdk.start_transaction(op="function", name=func.__name__):
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

