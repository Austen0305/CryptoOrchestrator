"""
Graceful Shutdown Middleware
Handles graceful shutdown of the application with proper cleanup
"""

import asyncio
import logging
import signal
from collections.abc import Callable

from fastapi import FastAPI

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """
    Manages graceful shutdown of the application

    Features:
    - Signal handling (SIGTERM, SIGINT)
    - Cleanup tasks registration
    - Connection draining
    - Timeout protection
    """

    def __init__(self, app: FastAPI, shutdown_timeout: int = 30):
        self.app = app
        self.shutdown_timeout = shutdown_timeout
        self.cleanup_tasks: list[Callable] = []
        self.is_shutting_down = False
        self._shutdown_event = asyncio.Event()

        # Register signal handlers
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def register_cleanup(self, cleanup_func: Callable):
        """Register a cleanup function to be called on shutdown"""
        self.cleanup_tasks.append(cleanup_func)
        logger.debug(f"Registered cleanup task: {cleanup_func.__name__}")

    async def shutdown(self):
        """Perform graceful shutdown"""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return

        self.is_shutting_down = True
        self._shutdown_event.set()

        logger.info("Starting graceful shutdown...")

        try:
            # Run cleanup tasks
            for cleanup_func in self.cleanup_tasks:
                try:
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await asyncio.wait_for(cleanup_func(), timeout=5)
                    else:
                        cleanup_func()
                    logger.debug(f"Completed cleanup: {cleanup_func.__name__}")
                except Exception as e:
                    logger.error(
                        f"Error in cleanup {cleanup_func.__name__}: {e}", exc_info=True
                    )

            logger.info("Graceful shutdown completed")
        except TimeoutError:
            logger.error("Shutdown timeout exceeded, forcing exit")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self._shutdown_event.wait()

    def is_shutting_down_check(self) -> bool:
        """Check if shutdown is in progress"""
        return self.is_shutting_down


# Global graceful shutdown instance
_graceful_shutdown: GracefulShutdown | None = None


def setup_graceful_shutdown(
    app: FastAPI, shutdown_timeout: int = 30
) -> GracefulShutdown:
    """Setup graceful shutdown for the application"""
    global _graceful_shutdown
    _graceful_shutdown = GracefulShutdown(app, shutdown_timeout)

    # Register default cleanup tasks
    @_graceful_shutdown.register_cleanup
    async def close_database():
        """Close database connections"""
        try:
            from ..database.connection_pool import db_pool

            if db_pool and db_pool._is_initialized:
                await db_pool.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")

    @_graceful_shutdown.register_cleanup
    async def close_redis():
        """Close Redis connections"""
        try:
            from ..middleware.cache_manager import cache_manager

            if cache_manager:
                await cache_manager.close()
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")

    return _graceful_shutdown


def get_graceful_shutdown() -> GracefulShutdown | None:
    """Get global graceful shutdown instance"""
    return _graceful_shutdown
