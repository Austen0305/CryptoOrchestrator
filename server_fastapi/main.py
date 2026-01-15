# Set environment variables to disable CUDA/GPU before any imports
# This prevents CUDA initialization errors on systems without GPU
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

# Config
from server_fastapi.config.openapi_config import custom_openapi, get_openapi_config
from server_fastapi.config.settings import get_settings

# Core Domain Bootstrap
from server_fastapi.core.errors import setup_exception_handlers
from server_fastapi.core.json import PolarsInternalResponse

# Core Lifecycle
# Core Lifecycle
from server_fastapi.core.lifecycle import start_services, stop_services
from server_fastapi.core.rate_limit import rate_limit_lifespan

# Database
from server_fastapi.database.connection_pool import db_pool

# Middleware
from server_fastapi.middleware.regulatory_filter import RegulatoryFilterMiddleware
from server_fastapi.middleware.security_headers import SecurityHeadersMiddleware
from server_fastapi.middleware.setup import setup_all_middleware
from server_fastapi.services.logging_config import setup_logging

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")  # Suppress TensorFlow warnings
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

load_dotenv()

# Suppress logging errors during testing
if os.getenv("TESTING", "false").lower() == "true":
    _original_handle_error = logging.Handler.handleError

    def _suppress_file_lock_errors(self, record):
        with suppress(OSError):
            _original_handle_error(self, record)

    logging.Handler.handleError = _suppress_file_lock_errors  # type: ignore

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
    logger.info("Starting FastAPI server...")

    # Initialize Rate Limiter
    async with rate_limit_lifespan(app):
        # Start all services
        await start_services(app)

        # ---------------------------------------------------------------------
        # PHASE 12: SENTINEL INTELLIGENCE
        # ---------------------------------------------------------------------
        from server_fastapi.core.bus import bus
        from server_fastapi.core.events import TradeEvent
        from server_fastapi.services.sentinel_service import SentinelService

        sentinel_service = SentinelService(window_minutes=60)

        # Subscribe to Trade Events (Fire-and-Forget)
        bus.subscribe(TradeEvent, sentinel_service.ingest_trade_async)
        logger.info(
            "Sentinel Service ACTIVE: Monitoring for Market Abuse (MiCA Art. 16)"
        )

        yield

        # Stop all services
        await stop_services(app)


# Create FastAPI app
openapi_config = get_openapi_config()

app = FastAPI(
    title=openapi_config["title"],
    description=openapi_config["description"],
    version=openapi_config["version"],
    lifespan=lifespan,
    default_response_class=PolarsInternalResponse,
    docs_url="/docs" if os.getenv("NODE_ENV") != "production" else None,
    redoc_url=None,
)


def _custom_openapi():
    return custom_openapi(app)


app.openapi = _custom_openapi  # type: ignore

# Register Middleware
setup_all_middleware(app)

# Register Error Handlers (RFC 9457)
setup_exception_handlers(app)

# Register Security Headers (Top Priority)
app.add_middleware(SecurityHeadersMiddleware)

# Register Regulatory Filter
app.add_middleware(RegulatoryFilterMiddleware)  # type: ignore


# Health Check
@app.get("/health")
async def health_check() -> dict[str, str]:
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
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CryptoOrchestrator API", "version": "1.0.0"}


# Add parent directory to Python path if running from server_fastapi directory
from pathlib import Path

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
with suppress(ImportError, AttributeError):
    from server_fastapi.middleware.health_check import (
        router as middleware_health_router,
    )

    app.include_router(middleware_health_router, tags=["Middleware Health"])
    logger.info("Middleware health check routes loaded")

# API Versioning Stub (Special case, keeps v1/v2 tags intact)
with suppress(ImportError):
    from server_fastapi.routes.api_versioning import router_v1, router_v2

    app.include_router(router_v1, tags=["API v1"])
    app.include_router(router_v2, tags=["API v2"])
    logger.info("API versioning routes loaded")

logger.info("Router loading complete")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    is_development = os.getenv("NODE_ENV") == "development"

    # Performance optimizations for production
    uvicorn.run(
        "server_fastapi.main:app",
        host=host,
        port=port,
        reload=is_development,
        log_level="debug" if is_development else "info",
        access_log=is_development,
        workers=1,
        loop="asyncio",
        http="auto",
    )
