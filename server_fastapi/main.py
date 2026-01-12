# Set environment variables to disable CUDA/GPU before any imports
# This prevents CUDA initialization errors on systems without GPU
import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")  # Suppress TensorFlow warnings
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import asyncio
import json
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ENABLE_HEAVY_MIDDLEWARE = (
    os.getenv("ENABLE_HEAVY_MIDDLEWARE", "false").lower() == "true"
)

# Core Domain Bootstrap
from .core.bootstrap import bootstrap_domain_services

# Middleware
from .middleware.validation import InputValidationMiddleware
from .middleware.monitoring import MonitoringMiddleware
from .middleware.regulatory_filter import RegulatoryFilterMiddleware

# Services
from .config.settings import get_settings
from .services.logging_config import setup_logging
from .services.monitoring.sentry_integration import init_sentry

# Database & Cache
from .database.connection_pool import db_pool
from . import database as _db_module

init_database = getattr(_db_module, "init_database", None)

import redis.asyncio as aioredis
from .middleware.cache_manager import init_redis
from .middleware.redis_manager import cache_manager

# Circuit Breakers
from .middleware.circuit_breaker import database_breaker, exchange_breaker

# Rate Limiting
from .rate_limit_config import limiter

# Env Loading
from dotenv import load_dotenv

load_dotenv()

# Standard Libs
import logging
from contextlib import asynccontextmanager

# Suppress logging errors during testing
if os.getenv("TESTING", "false").lower() == "true":
    _original_handle_error = logging.Handler.handleError

    def _suppress_file_lock_errors(self, record):
        try:
            _original_handle_error(self, record)
        except (PermissionError, OSError):
            pass

    logging.Handler.handleError = _suppress_file_lock_errors

logger = logging.getLogger(__name__)

# Configure Logging (Fail Fast if config invalid)
settings = get_settings()
is_testing = os.getenv("TESTING", "false").lower() == "true"
log_file_path = (
    os.path.join(settings.log_dir, "app.log")
    if settings.log_dir and not is_testing
    else None
)

try:
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        log_file=log_file_path,
        enable_file=not is_testing,
    )
    logging.info("[OK] Logging configured")
except Exception as e:
    # If logging fails, we panic.
    sys.stderr.write(f"CRITICAL: Failed to setup logging: {e}\n")
    sys.exit(1)

# Set uvicorn loggers
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastAPI server (Fail Fast Mode)...")

    # 1. Bootstrap Domain Services
    try:
        bootstrap_domain_services()
        logger.info("[OK] Domain services bootstrapped")
    except Exception as e:
        logger.critical(f"Domain bootstrap failed: {e}")
        if os.getenv("NODE_ENV") == "production":
            sys.exit(1)

    # 2. Setup Graceful Shutdown
    from .middleware.graceful_shutdown import setup_graceful_shutdown

    graceful_shutdown = setup_graceful_shutdown(app, shutdown_timeout=30)
    app.state.graceful_shutdown = graceful_shutdown

    # 3. Environment Validation
    from .config.env_validator import validate_all

    try:
        validate_all(exit_on_error=(os.getenv("NODE_ENV") == "production"))
    except Exception as e:
        logger.critical(f"Environment validation failed: {e}")
        if os.getenv("NODE_ENV") == "production":
            sys.exit(1)

    # 4. OpenTelemetry (Optional but strict if enabled)
    if os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true":
        from .services.observability.opentelemetry_setup import (
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

    # 5. Distributed Rate Limiter
    if os.getenv("ENABLE_DISTRIBUTED_RATE_LIMIT", "false").lower() == "true":
        from .middleware.distributed_rate_limiter import get_rate_limiter

        rate_limiter = get_rate_limiter()
        await rate_limiter.connect()
        app.state.rate_limiter = rate_limiter
        logger.info("[OK] Distributed rate limiter connected")
    else:
        app.state.rate_limiter = None

    # 6. Redis Cache
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
        # In production, this should probably be a hard fail

    # 7. Database Connection Pool
    if db_pool:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        db_pool.initialize(db_url)
        logger.info(f"[OK] Database pool initialized: {db_url}")

        # Initialize Tables
        if init_database:
            await init_database()
            logger.info("[OK] Database tables verified")

    # 8. Sentry
    if os.getenv("SENTRY_DSN"):
        init_sentry(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("NODE_ENV", "development"),
        )
        logger.info("[OK] Sentry initialized")

    # 9. Health Checks
    from .routes.health_advanced import health_checker

    # 10. Startup Validation
    from .utils.startup_validation import startup_validator

    res = await startup_validator.validate_all()
    startup_validator.log_results(res)
    if not res["valid"]:
        logger.error("Startup validation reported issues.")

    # 11. API Docs
    from .middleware.api_documentation_enhanced import setup_enhanced_documentation

    setup_enhanced_documentation(app)

    yield

    # ---------------- SHUTDOWN ----------------
    logger.info("Shutting down FastAPI server...")

    if hasattr(app.state, "graceful_shutdown"):
        await app.state.graceful_shutdown.shutdown()

    if app.state.rate_limiter:
        await app.state.rate_limiter.close()

    if cache_manager:
        await cache_manager.close()

    if db_pool:
        await db_pool.close()


# Create FastAPI app
from .config.openapi_config import custom_openapi, get_openapi_config

openapi_config = get_openapi_config()

app = FastAPI(
    title=openapi_config["title"],
    description=openapi_config["description"],
    version=openapi_config["version"],
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("NODE_ENV") != "production" else None,
    redoc_url=None,
)
app.openapi = lambda: custom_openapi(app)

# Register Middleware
from .middleware.setup import setup_all_middleware

setup_all_middleware(app)

# Register Regulatory Filter
app.add_middleware(RegulatoryFilterMiddleware)


# Health Check
@app.get("/health")
async def health_check():
    status = {"status": "healthy", "database": "unknown"}
    if db_pool and db_pool._is_initialized:
        try:
            if await db_pool.health_check():
                status["database"] = "healthy"
            else:
                status["status"] = "degraded"
                status["database"] = "unhealthy"
        except Exception:
            status["status"] = "degraded"
            status["database"] = "error"
    return status


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "CryptoOrchestrator API", "version": "1.0.0"}


import importlib
import sys
from pathlib import Path

# Add parent directory to Python path if running from server_fastapi directory
if Path.cwd().name == "server_fastapi" or str(Path.cwd()).endswith("server_fastapi"):
    parent_dir = Path.cwd().parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))


logger.info("Loading routers with 2026 Auto-Discovery strategy...")

# -------------------------------------------------------------------------
# Dynamic Router Registration (2026 Modernization)
# -------------------------------------------------------------------------

try:
    from server_fastapi.core.router_discovery import register_routers

    # Register all routers from server_fastapi.routes package
    # Auto-discovery handles prefixes, tags, and graceful fallback
    register_routers(app, "server_fastapi.routes")
except ImportError as e:
    logger.critical(f"Failed to implement router discovery: {e}")
    # This is fatal in strict mode
    raise

# -------------------------------------------------------------------------
# Manual Router Registration (Middleware & Special Cases)
# -------------------------------------------------------------------------

# Middleware Health Check (Located in middleware/, not auto-discovered)
try:
    from .middleware.health_check import router as middleware_health_router

    app.include_router(middleware_health_router, tags=["Middleware Health"])
    logger.info("Middleware health check routes loaded")
except Exception as e:
    logger.warning(f"Middleware health check routes not loaded: {e}")

# API Versioning Stub (Special case, keeps v1/v2 tags intact)
try:
    from server_fastapi.routes.api_versioning import router_v1, router_v2

    app.include_router(router_v1, tags=["API v1"])
    app.include_router(router_v2, tags=["API v2"])
    logger.info("API versioning routes loaded")
except Exception:
    logger.info("API versioning not loaded")

logger.info("Router loading complete")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    is_development = os.getenv("NODE_ENV") == "development"

    # Performance optimizations for production
    uvicorn_config = {
        "app": "server_fastapi.main:app",
        "host": host,
        "port": port,
        "reload": is_development,
        "log_level": "debug" if is_development else "info",
        "access_log": is_development,  # Disable access logs in production for performance
        "workers": 1,  # Single worker for desktop app (avoid port conflicts)
        "loop": "asyncio",
        "http": "auto",  # Use auto for compatibility
    }

    uvicorn.run(**uvicorn_config)
