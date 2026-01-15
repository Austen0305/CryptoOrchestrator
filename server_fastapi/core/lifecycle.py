import logging
import os
import sys

from fastapi import FastAPI

from server_fastapi import database as _db_module

# Validation
from server_fastapi.config.env_validator import validate_all

# Services
from server_fastapi.core.bootstrap import bootstrap_domain_services

# Database & Cache
from server_fastapi.database.connection_pool import db_pool

# Middleware
from server_fastapi.middleware.graceful_shutdown import setup_graceful_shutdown
from server_fastapi.middleware.redis_manager import cache_manager
from server_fastapi.services.monitoring.sentry_integration import init_sentry
from server_fastapi.utils.startup_validation import startup_validator

logger = logging.getLogger(__name__)


async def _init_observability(app: FastAPI) -> None:
    """Initialize OpenTelemetry if enabled."""
    if os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true":
        from server_fastapi.services.observability.opentelemetry_setup import (
            instrument_fastapi,
            instrument_requests,
            instrument_sqlalchemy,
            setup_opentelemetry,
        )

        setup_opentelemetry(
            service_name=os.getenv("OTEL_SERVICE_NAME", "cryptoorchestrator"),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        )
        instrument_fastapi(app)
        instrument_sqlalchemy()
        instrument_requests()
        logger.info("[OK] OpenTelemetry enabled")


async def _init_rate_limiter(app: FastAPI) -> None:
    """Initialize Distributed Rate Limiter if enabled."""
    if os.getenv("ENABLE_DISTRIBUTED_RATE_LIMIT", "false").lower() == "true":
        from server_fastapi.middleware.distributed_rate_limiter import get_rate_limiter

        rate_limiter = get_rate_limiter()
        await rate_limiter.connect()
        app.state.rate_limiter = rate_limiter
        logger.info("[OK] Distributed rate limiter connected")
    else:
        app.state.rate_limiter = None


async def _init_redis() -> None:
    """Initialize Redis Cache."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        cache_manager.redis_url = redis_url
        await cache_manager.connect()
        if not cache_manager.available:
            logger.warning(
                "Redis is UNAVAILABLE. Falling back to memory (Production Hazard!)"
            )
        else:
            logger.info(f"[OK] Redis cache connected at {redis_url}")
    except Exception as e:
        logger.critical(f"Redis connection failed: {e}")


async def _init_database() -> None:
    """Initialize Database Connection Pool."""
    if db_pool:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        db_pool.initialize(db_url)
        logger.info(f"[OK] Database pool initialized: {db_url}")

        # Initialize Tables
        init_database = getattr(_db_module, "init_database", None)
        if init_database:
            await init_database()
            logger.info("[OK] Database tables verified")


def _init_sentry_service() -> None:
    """Initialize Sentry."""
    if os.getenv("SENTRY_DSN"):
        init_sentry(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("NODE_ENV", "development"),
        )
        logger.info("[OK] Sentry initialized")


async def start_services(app: FastAPI) -> None:
    """
    Initialize all services required for the application.
    """
    logger.info("Starting services...")

    # 1. Bootstrap Domain Services
    try:
        bootstrap_domain_services()
        logger.info("[OK] Domain services bootstrapped")
    except Exception as e:
        logger.critical(f"Domain bootstrap failed: {e}")
        if os.getenv("NODE_ENV") == "production":
            sys.exit(1)

    # 2. Setup Graceful Shutdown
    graceful_shutdown = setup_graceful_shutdown(app, shutdown_timeout=30)
    app.state.graceful_shutdown = graceful_shutdown

    # 3. Environment Validation
    try:
        validate_all(exit_on_error=(os.getenv("NODE_ENV") == "production"))
    except Exception as e:
        logger.critical(f"Environment validation failed: {e}")
        if os.getenv("NODE_ENV") == "production":
            sys.exit(1)

    # 4. Initialize Sub-systems
    await _init_observability(app)
    await _init_rate_limiter(app)
    await _init_redis()
    await _init_database()
    _init_sentry_service()

    # 9. Startup Validation
    res = await startup_validator.validate_all()
    startup_validator.log_results(res)
    if not res["valid"]:
        logger.error("Startup validation reported issues.")

    # 10. API Docs
    from server_fastapi.middleware.api_documentation_enhanced import (
        setup_enhanced_documentation,
    )

    setup_enhanced_documentation(app)


async def stop_services(app: FastAPI) -> None:
    """
    Teardown all services.
    """
    logger.info("Shutting down FastAPI server services...")

    if hasattr(app.state, "graceful_shutdown"):
        await app.state.graceful_shutdown.shutdown()

    if app.state.rate_limiter:
        await app.state.rate_limiter.close()

    if cache_manager:
        await cache_manager.close()

    if db_pool:
        await db_pool.close()
