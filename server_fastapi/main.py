# Set environment variables to disable CUDA/GPU before any imports
# This prevents CUDA initialization errors on systems without GPU
import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")  # Suppress TensorFlow warnings
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uvicorn
import sys
import asyncio
import json

# Feature flag to turn heavy middleware on/off for debugging
ENABLE_HEAVY_MIDDLEWARE = (
    os.getenv("ENABLE_HEAVY_MIDDLEWARE", "false").lower() == "true"
)

# Import validation middleware
try:
    from .middleware.validation import InputValidationMiddleware, validate_email_format
except ImportError:
    InputValidationMiddleware = None
    validate_email_format = None

# Import monitoring middleware
try:
    from .middleware.monitoring import MonitoringMiddleware
except ImportError:
    MonitoringMiddleware = None

# Import Sentry integration for error tracking
try:
    from .services.monitoring.sentry_integration import init_sentry

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    init_sentry = None

# Import database connection pool
try:
    from .database.connection_pool import db_pool
    from . import database as _db_module  # Prefer module over package directory

    init_database = getattr(_db_module, "init_database", None)
except ImportError:
    db_pool = None
    init_database = None
except Exception as e:
    # Logger not yet defined, use basic logging
    import logging

    logging.warning(f"Database import issue: {e}")
    db_pool = None
    init_database = None

# Import Redis cache
try:
    from .middleware.cache_manager import init_redis
    from .middleware.redis_manager import cache_manager
    import redis.asyncio as aioredis

    redis_available = True
except ImportError:
    redis_available = False
    init_redis = None
    cache_manager = None

# Import circuit breaker
try:
    from .middleware.circuit_breaker import exchange_breaker, database_breaker
except ImportError:
    exchange_breaker = None
    database_breaker = None

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if dotenv not available
    def load_dotenv():
        pass


import logging
from contextlib import asynccontextmanager

# Suppress logging errors during testing to avoid file lock issues
_is_testing = os.getenv("TESTING", "false").lower() == "true"
if _is_testing:
    # Override the logging error handler to suppress PermissionErrors during testing
    # This prevents file locking errors from crashing the application during tests
    _original_handle_error = logging.Handler.handleError
    def _suppress_file_lock_errors(self, record):
        """Suppress PermissionErrors (file locks) during testing"""
        try:
            _original_handle_error(self, record)
        except (PermissionError, OSError) as e:
            # Suppress file locking errors during testing - these are non-critical
            if "WinError 32" in str(e) or "being used by another process" in str(e):
                pass  # Silently ignore file lock errors during testing
            else:
                raise
    logging.Handler.handleError = _suppress_file_lock_errors
    
    # Also override the root logger's callHandlers to catch errors there
    _original_call_handlers = logging.Logger.callHandlers
    def _call_handlers_safe(self, record):
        """Safely call handlers, suppressing file lock errors during testing"""
        try:
            _original_call_handlers(self, record)
        except (PermissionError, OSError) as e:
            # Suppress file locking errors - log to console instead
            if "WinError 32" in str(e) or "being used by another process" in str(e):
                import sys
                sys.stderr.write(f"[Warning] Log file locked, using console only: {e}\n")
            else:
                raise
    logging.Logger.callHandlers = _call_handlers_safe

# Do NOT modify sys.path here. Running with `server_fastapi.main:app` ensures
# proper package context for relative imports within the `server_fastapi` package.

# Load environment variables
load_dotenv()

# Import rate limiting configuration
try:
    from .rate_limit_config import limiter
except ImportError:
    # Fallback if rate limiting not available
    limiter = None

# Configure comprehensive logging
try:
    from .services.logging_config import setup_logging
    from .config.settings import get_settings

    settings = get_settings()
    # Disable file logging during testing to avoid file locking issues
    is_testing = os.getenv("TESTING", "false").lower() == "true"
    # Construct log file path from log_dir
    log_file_path = (
        os.path.join(settings.log_dir, "app.log") if settings.log_dir and not is_testing else None
    )
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        log_file=log_file_path,
        enable_file=not is_testing,  # Disable file logging during tests
    )
    logging.info("[OK] Comprehensive logging configured")
except Exception as e:
    # Fallback to basic logging
    # Disable file logging during testing to avoid file locking issues
    is_testing = os.getenv("TESTING", "false").lower() == "true"
    handlers = [logging.StreamHandler(sys.stdout)]  # Console logging always enabled
    if not is_testing:
        # Ensure logs directory exists only if not testing
        os.makedirs("logs", exist_ok=True)
        handlers.append(logging.FileHandler("logs/fastapi.log", mode="a"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # Override any existing configuration
    )
    logging.warning(f"Comprehensive logging not available, using basic: {e}")

logger = logging.getLogger(__name__)

# Set uvicorn loggers to match our level
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.INFO)
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.setLevel(logging.INFO)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FastAPI server...")
    
    # Setup graceful shutdown
    try:
        from .middleware.graceful_shutdown import setup_graceful_shutdown
        graceful_shutdown = setup_graceful_shutdown(app, shutdown_timeout=30)
        app.state.graceful_shutdown = graceful_shutdown
        logger.info("Graceful shutdown handler configured")
    except Exception as e:
        logger.warning(f"Failed to setup graceful shutdown: {e}")

    # Validate environment variables
    try:
        from .config.env_validator import validate_all

        # In test mode, don't exit on validation errors (just warn)
        exit_on_error = (
            os.getenv("TESTING") != "true" and os.getenv("NODE_ENV") == "production"
        )
        validate_all(exit_on_error=exit_on_error)
        logger.info("Environment variables validated")
    except SystemExit:
        raise
    except Exception as e:
        logger.warning(f"Environment validation failed: {e}")
        # Continue in development/test, but should fail in production
        if os.getenv("NODE_ENV") == "production" and os.getenv("TESTING") != "true":
            logger.error("Environment validation failed in production - exiting")
            sys.exit(1)

    # Initialize OpenTelemetry if enabled
    try:
        from .services.observability.opentelemetry_setup import (
            setup_opentelemetry,
            instrument_fastapi,
            instrument_sqlalchemy,
            instrument_requests,
        )

        if os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true":
            setup_success = setup_opentelemetry(
                service_name=os.getenv("OTEL_SERVICE_NAME", "cryptoorchestrator"),
                service_version=os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
                otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
                enable_console_exporter=os.getenv(
                    "OTEL_CONSOLE_EXPORTER", "false"
                ).lower()
                == "true",
                enable_prometheus=os.getenv("OTEL_PROMETHEUS", "true").lower()
                == "true",
            )

            if setup_success:
                instrument_fastapi(app)
                instrument_sqlalchemy()
                instrument_requests()
                logger.info("[OK] OpenTelemetry instrumentation complete")

    except Exception as e:
        logger.warning(f"OpenTelemetry initialization failed: {e}")

    # Initialize distributed rate limiter (skip in test mode)
    if os.getenv("ENABLE_DISTRIBUTED_RATE_LIMIT", "false").lower() == "true":
        try:
            from .middleware.distributed_rate_limiter import get_rate_limiter

            rate_limiter = get_rate_limiter()
            await rate_limiter.connect()
            app.state.rate_limiter = rate_limiter
            logger.info("Distributed rate limiter initialized")
        except Exception as e:
            logger.warning(f"Distributed rate limiter initialization failed: {e}")
            app.state.rate_limiter = None
    else:
        logger.info("Distributed rate limiter disabled (test mode or not configured)")
        app.state.rate_limiter = None

    # Initialize Redis cache manager with fallback
    if redis_available and cache_manager:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            cache_manager.redis_url = redis_url
            await cache_manager.connect()
            if cache_manager.available:
                logger.info(f"Redis cache initialized at {redis_url}")
            else:
                logger.info("[WARN] Redis unavailable, using in-memory cache fallback")
        except Exception as e:
            logger.warning(f"Redis initialization failed, using in-memory cache: {e}")

    # Initialize Redis for caching if available (legacy)
    if redis_available and init_redis:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            # Increased timeout to prevent connection errors (5.0s connection, 2.0s ping)
            redis_client = await asyncio.wait_for(
                aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True),
                timeout=5.0,  # Increased from 2.0 to prevent connection errors
            )
            await asyncio.wait_for(
                redis_client.ping(), timeout=2.0
            )  # Increased from 1.0
            init_redis(redis_client)
            logger.info(f"Redis cache initialized at {redis_url}")
        except asyncio.TimeoutError:
            logger.warning("Redis connection timeout - caching disabled")
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {e}")

    # Initialize cache warmer service (skip in test mode to speed up startup)
    if os.getenv("TESTING") != "true":
        try:
            from .services.cache_warmer_service import (
                cache_warmer_service,
                register_default_warmup_tasks,
            )

            register_default_warmup_tasks()
            await cache_warmer_service.start()
            app.state.cache_warmer = cache_warmer_service
            logger.info("Cache warmer service started")
        except Exception as e:
            logger.warning(f"Cache warmer service initialization failed: {e}")
            app.state.cache_warmer = None
    else:
        logger.info("Cache warmer service disabled in test mode")
        app.state.cache_warmer = None

    # Initialize database connection pool if available
    if db_pool and not db_pool._is_initialized:
        try:
            database_url = os.getenv(
                "DATABASE_URL", "sqlite+aiosqlite:///./data/app.db"
            )
            db_pool.initialize(database_url)
            logger.info("Database connection pool initialized")

            # Initialize pool monitor
            from .database.pool_monitoring import get_pool_monitor

            monitor = get_pool_monitor(db_pool.engine)
            app.state.pool_monitor = monitor
            logger.info("Connection pool monitor initialized")

            # Setup query profiling if OpenTelemetry enabled
            if os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true":
                try:
                    from .services.monitoring.performance_profiler import (
                        setup_query_profiling,
                    )

                    # Access sync engine from async engine for profiling
                    if hasattr(db_pool.engine, "sync_engine"):
                        setup_query_profiling(db_pool.engine.sync_engine)
                        logger.info("[OK] Query profiling enabled")
                except Exception as e:
                    logger.warning(f"Query profiling setup failed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")

    # Initialize AsyncPG pool for high-performance queries (PostgreSQL only)
    try:
        from .config.settings import settings
        from .database.asyncpg_pool import AsyncPGPool

        database_url = settings.database_url
        # Only initialize for PostgreSQL databases
        if database_url.startswith("postgresql"):
            try:
                await AsyncPGPool.create_pool(
                    database_url=database_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=30,
                )
                app.state.asyncpg_pool = AsyncPGPool
                logger.info(
                    "AsyncPG connection pool initialized for high-performance queries"
                )
            except ImportError:
                logger.warning(
                    "asyncpg not installed - skipping AsyncPG pool initialization"
                )
            except Exception as e:
                logger.warning(
                    f"AsyncPG pool initialization failed (non-critical): {e}"
                )
        else:
            logger.info("AsyncPG pool skipped (not PostgreSQL database)")
    except Exception as e:
        logger.warning(f"AsyncPG pool setup failed (non-critical): {e}")

    # Initialize read replicas if enabled
    try:
        from .config.settings import settings
        from .database.read_replica import read_replica_manager

        if settings.enable_read_replicas and settings.db_read_replica_urls:
            read_urls = [
                url.strip() for url in settings.db_read_replica_urls.split(",")
            ]
            read_replica_manager.initialize(
                write_url=settings.database_url, read_urls=read_urls
            )
            app.state.read_replica_manager = read_replica_manager
            logger.info(
                f"Read replica manager initialized with {len(read_urls)} replicas"
            )
        else:
            logger.info("Read replicas not enabled or not configured")
    except Exception as e:
        logger.warning(f"Read replica initialization failed: {e}")

    # Initialize database tables (persistent) even if connection pool abstraction unavailable
    if init_database:
        try:
            await init_database()
            logger.info("Database tables ensured (created if missing)")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")

    # Initialize Sentry error tracking
    if SENTRY_AVAILABLE and init_sentry:
        try:
            environment = os.getenv("ENVIRONMENT", os.getenv("NODE_ENV", "development"))
            sentry_dsn = os.getenv("SENTRY_DSN")
            if sentry_dsn:
                if init_sentry(dsn=sentry_dsn, environment=environment):
                    logger.info(f"Sentry error tracking initialized for {environment}")
                else:
                    logger.warning("[WARN] Sentry initialization failed")
            else:
                logger.info(
                    "[WARN] SENTRY_DSN not provided, error tracking disabled (set SENTRY_DSN env var to enable)"
                )
        except Exception as e:
            logger.warning(f"Sentry initialization failed: {e}")

    # Register health checks
    try:
        from .routes.health_advanced import health_checker

        logger.info("Health check system initialized")
    except ImportError:
        logger.warning("Advanced health checks not available")

    # Run startup validation
    try:
        from .utils.startup_validation import startup_validator
        
        validation_results = await startup_validator.validate_all()
        startup_validator.log_results(validation_results)
        
        if not validation_results["valid"]:
            logger.error("Startup validation failed - some errors may cause issues")
        else:
            logger.info("Startup validation passed successfully")
    except Exception as e:
        logger.warning(f"Startup validation failed: {e}")

    # Setup enhanced API documentation
    try:
        from .middleware.api_documentation_enhanced import setup_enhanced_documentation
        
        setup_enhanced_documentation(app)
        logger.info("Enhanced API documentation configured")
    except Exception as e:
        logger.warning(f"Enhanced API documentation not available: {e}")

    # Start market data streaming service (skip in test mode)
    if os.getenv("TESTING") != "true":
        try:
            from .services.websocket_manager import connection_manager
            from .services.market_streamer import get_market_streamer

            streamer = get_market_streamer(connection_manager)
            streamer.start()
            app.state.market_streamer = streamer
            logger.info("Market data streaming service started")
        except Exception as e:
            logger.warning(f"Market data streaming not available: {e}")
    else:
        logger.info("Market data streaming disabled in test mode")
        app.state.market_streamer = None

    # Export OpenAPI JSON schema to docs/openapi.json
    try:
        os.makedirs("docs", exist_ok=True)
        openapi_schema = app.openapi()
        with open("docs/openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        logger.info("OpenAPI schema exported to docs/openapi.json")
    except Exception as e:
        logger.warning(f"Failed to export OpenAPI schema: {e}")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI server...")

    # Stop monitoring system
    try:
        monitoring_system = getattr(app.state, "monitoring_system", None)
        if monitoring_system:
            await monitoring_system.stop_monitoring()
            logger.info("Monitoring system stopped")
    except Exception as e:
        logger.warning(f"Error stopping monitoring system: {e}")
    
    # Trigger graceful shutdown if configured
    if hasattr(app.state, "graceful_shutdown"):
        try:
            await app.state.graceful_shutdown.shutdown()
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")

    # Stop market data streaming service
    if hasattr(app.state, "market_streamer") and app.state.market_streamer:
        try:
            app.state.market_streamer.stop()
            logger.info("Market data streaming service stopped")
        except Exception as e:
            logger.error(f"Error stopping market streamer: {e}")

    # Close distributed rate limiter
    if hasattr(app.state, "rate_limiter") and app.state.rate_limiter:
        try:
            await app.state.rate_limiter.close()
            logger.info("Distributed rate limiter closed")
        except Exception as e:
            logger.error(f"Error closing rate limiter: {e}")

    # Close Redis cache manager
    if redis_available and cache_manager:
        try:
            await cache_manager.close()
            logger.info("Redis cache manager closed")
        except Exception as e:
            logger.error(f"Error closing Redis cache manager: {e}")

    # Close Redis connection (legacy)
    if redis_available and init_redis:
        try:
            # Close Redis gracefully
            logger.info("Closing Redis connection...")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")

    # Stop cache warmer service
    if hasattr(app.state, "cache_warmer") and app.state.cache_warmer:
        try:
            await app.state.cache_warmer.stop()
            logger.info("Cache warmer service stopped")
        except Exception as e:
            logger.error(f"Error stopping cache warmer: {e}")

    # Close database connections
    if db_pool:
        try:
            await db_pool.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

    # Close AsyncPG pool
    try:
        from .database.asyncpg_pool import AsyncPGPool

        await AsyncPGPool.close()
        logger.info("AsyncPG pool closed")
    except Exception as e:
        logger.warning(f"Error closing AsyncPG pool: {e}")


# Create FastAPI app - optimized for desktop app performance
# Enhanced OpenAPI documentation
try:
    from .config.openapi_config import get_openapi_config, custom_openapi

    openapi_config = get_openapi_config()
    app = FastAPI(
        title=openapi_config["title"],
        description=openapi_config["description"],
        version=openapi_config["version"],
        openapi_tags=openapi_config.get("tags", []),
        lifespan=lifespan,
        debug=False,
        docs_url="/docs" if os.getenv("NODE_ENV") == "development" else None,
        redoc_url="/redoc" if os.getenv("NODE_ENV") == "development" else None,
    )
    app.openapi = lambda: custom_openapi(app)
    logger.info("Enhanced OpenAPI documentation configured")
except Exception as e:
    logger.warning(f"Enhanced OpenAPI config not available, using defaults: {e}")
    app = FastAPI(
        title="CryptoOrchestrator API",
        description="Professional AI-Powered Crypto Trading Platform API",
        version="1.0.0",
        lifespan=lifespan,
        debug=False,
        docs_url="/docs" if os.getenv("NODE_ENV") == "development" else None,
        redoc_url="/redoc" if os.getenv("NODE_ENV") == "development" else None,
    )

# Rate limiting is now handled in middleware.setup module
# Keep limiter state for backward compatibility
if limiter:
    app.state.limiter = limiter

# Setup all middleware using centralized configuration
try:
    from .middleware.setup import setup_all_middleware
    
    middleware_stats = setup_all_middleware(app)
    logger.info(
        f"Middleware setup complete: {middleware_stats['registered']}/{middleware_stats['total']} "
        f"registered, {middleware_stats['failed']} failed"
    )
except Exception as e:
    logger.error(f"Failed to setup middleware: {e}", exc_info=True)
    # Fallback to basic security headers if setup fails
    @app.middleware("http")
    async def add_basic_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# CORS utility functions (used by registration shim)
# Import from middleware setup module
try:
    from .middleware.setup import add_cors_headers, get_cors_origins
    cors_origins = get_cors_origins()
except ImportError:
    # Fallback if middleware setup not available
    def add_cors_headers(response: JSONResponse, request: Request, allowed_origins: list) -> JSONResponse:
        """Fallback CORS headers function"""
        origin = request.headers.get("origin")
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With, Accept, Origin"
        return response
    
    # Default origins
    cors_origins = [
        "http://localhost:3000", "http://localhost:5173", "http://localhost:8000",
        "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8000",
        "file://", "null", "exp://", "http://10.0.2.2:8000"
    ]


# CORS middleware is now handled in middleware.setup module

# Note: Error handlers and timeout middleware are now registered via setup_all_middleware above
# Trusted host middleware is also handled in middleware setup


# Health check endpoint with database status
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "CryptoOrchestrator API",
        "database": "unknown",
    }

    # Check database connection - try multiple methods for robustness
    try:
        # Method 1: Try db_pool health_check if initialized
        if db_pool and db_pool._is_initialized and hasattr(db_pool, 'health_check'):
            try:
                is_healthy = await db_pool.health_check()
                if is_healthy:
                    health_status["database"] = "healthy"
                else:
                    raise Exception("db_pool health_check returned False")
            except Exception as e:
                logger.debug(f"db_pool health check failed, trying direct connection: {e}")
                # Fallback to direct connection check
                from .database import get_db_context
                from sqlalchemy import text
                async with get_db_context() as db:
                    await db.execute(text("SELECT 1"))
                health_status["database"] = "healthy"
        # Method 2: Try direct connection using get_db_context
        else:
            from .database import get_db_context
            from sqlalchemy import text
            async with get_db_context() as db:
                await db.execute(text("SELECT 1"))
            health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status


# Simple health check endpoint for load balancers and monitoring
@app.get("/healthz")
async def healthz():
    """Simple health check endpoint returning status: ok"""
    return {"status": "ok"}


# Root endpoint
@app.get("/")
async def root():
    return {"message": "CryptoOrchestrator API", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Temporary registration shim middleware
# ---------------------------------------------------------------------------
# There is an intermittent hang affecting /api/* routes in the deeper
# middleware/route stack. To ensure the user can create an account and log in,
# we short‑circuit /api/auth/register here and handle it in a minimal,
# in‑memory way. This avoids touching the database or advanced middleware.
#
# NOTE: Once the underlying middleware issue is fully resolved, this shim
#       can be removed and the normal server_fastapi.routes.auth.register
#       endpoint will take over again.
@app.middleware("http")
async def registration_shim(request: Request, call_next):
    # Allow OPTIONS requests (CORS preflight) to pass through
    if request.method.upper() == "OPTIONS":
        return await call_next(request)

    # Only intercept the registration endpoint for POST requests
    if request.url.path == "/api/auth/register" and request.method.upper() == "POST":
        try:
            import json
            from server_fastapi.routes import auth as auth_module

            body_bytes = await request.body()
            try:
                data = json.loads(body_bytes.decode() if body_bytes else "{}")
            except json.JSONDecodeError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid JSON body"},
                )
                return add_cors_headers(response, request, cors_origins)

            email = data.get("email")
            password = data.get("password")
            username = data.get("username") or (
                email.split("@")[0][:40] if email else "user"
            )
            first_name = data.get("first_name")
            last_name = data.get("last_name")

            if not email or not password:
                response = JSONResponse(
                    status_code=422,
                    content={"detail": "Email and password are required"},
                )
                return add_cors_headers(response, request, cors_origins)

            # Normalize email: lowercase and strip whitespace (don't sanitize - it breaks emails)
            email = email.strip().lower() if isinstance(email, str) else email

            # Validate email format BEFORE processing
            # Try to get validate_email_format from imported module or auth_module
            email_validator = validate_email_format
            if not email_validator:
                email_validator = getattr(auth_module, "validate_email_format", None)
            if email_validator and not email_validator(email):
                response = JSONResponse(
                    status_code=422,
                    content={
                        "detail": "Invalid email format. Please check your email address."
                    },
                )
                return add_cors_headers(response, request, cors_origins)

            # Validate password strength BEFORE processing
            try:
                from server_fastapi.middleware.validation import (
                    validate_password_strength,
                )

                password_validation = validate_password_strength(password)
                if not password_validation.get("valid", False):
                    response = JSONResponse(
                        status_code=422,
                        content={
                            "detail": password_validation.get(
                                "message", "Password does not meet requirements"
                            )
                        },
                    )
                    return add_cors_headers(response, request, cors_origins)
            except ImportError:
                # Fallback: basic password length check if validation module not available
                if not password or len(password) < 8:
                    response = JSONResponse(
                        status_code=422,
                        content={
                            "detail": "Password must be at least 8 characters long"
                        },
                    )
                    return add_cors_headers(response, request, cors_origins)

            # Use shared in‑memory storage from auth module
            storage = getattr(auth_module, "storage", None)
            auth_service = getattr(auth_module, "auth_service", None)
            generate_token = getattr(auth_module, "generate_token", None)

            if storage is None or auth_service is None or generate_token is None:
                response = JSONResponse(
                    status_code=500,
                    content={"detail": "Auth services not available"},
                )
                return add_cors_headers(response, request, cors_origins)

            # Check if user already exists in memory (use normalized email)
            existing = storage.getUserByEmail(email)
            if existing:
                response = JSONResponse(
                    status_code=400,
                    content={
                        "detail": f"A user with email {email} already exists. Please try logging in instead."
                    },
                )
                return add_cors_headers(response, request, cors_origins)

            # Use AuthService for password hashing + user creation
            # Use normalized email (not sanitized - sanitization breaks emails)
            try:
                # Get database session for registration
                from server_fastapi.database import get_db_context
                
                async with get_db_context() as session:
                    # Build name from first_name/last_name if available, otherwise use username or email prefix
                    name = None
                    if first_name or last_name:
                        name = f"{first_name or ''} {last_name or ''}".strip()
                    if not name:
                        name = username or email.split("@")[0]
                    
                    result = await auth_service.register(
                        {
                            "email": email,
                            "password": password,
                            "name": name,
                            "username": username,  # Pass username explicitly if provided
                            "first_name": first_name,  # Pass first_name if provided
                            "last_name": last_name,  # Pass last_name if provided
                        },
                        session=session
                    )
            except ValueError as e:
                # Handle duplicate email or validation errors from auth service
                error_msg = str(e)
                if (
                    "already exists" in error_msg.lower()
                    or "duplicate" in error_msg.lower()
                ):
                    response = JSONResponse(
                        status_code=400,
                        content={
                            "detail": f"A user with email {email} already exists. Please try logging in instead."
                        },
                    )
                else:
                    response = JSONResponse(
                        status_code=422,
                        content={"detail": f"Registration failed: {error_msg}"},
                    )
                return add_cors_headers(response, request, cors_origins)
            user = result.get("user")
            if not user:
                response = JSONResponse(
                    status_code=500,
                    content={"detail": "Registration failed - no user returned"},
                )
                return add_cors_headers(response, request, cors_origins)

            # Generate access token using existing helper
            token = generate_token(user)

            response_payload = {
                "access_token": token,
                "refresh_token": None,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": username,
                    "role": user.get("role", "user"),
                    "is_active": user.get("is_active", True),
                    "is_email_verified": user.get("emailVerified", False),
                    "first_name": first_name,
                    "last_name": last_name,
                },
                "message": "Registration completed via shim. Email verification may be limited.",
            }

            response = JSONResponse(status_code=200, content=response_payload)
            return add_cors_headers(response, request, cors_origins)
        except ValueError as e:
            # Handle validation errors with clear messages
            error_msg = str(e)
            status_code = (
                422
                if "required" in error_msg.lower() or "invalid" in error_msg.lower()
                else 400
            )
            response = JSONResponse(
                status_code=status_code,
                content={"detail": f"Registration error: {error_msg}"},
            )
            return add_cors_headers(response, request, cors_origins)
        except Exception as e:
            # Last‑resort error: return a safe message instead of hanging
            logger.error(f"Registration shim error: {e}", exc_info=True)
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": f"Registration failed: {str(e)}. Please try again or contact support if the problem persists."
                },
            )
            return add_cors_headers(response, request, cors_origins)

    # For all other routes, fall back to normal processing
    return await call_next(request)


import importlib
import sys
from pathlib import Path

# Add parent directory to Python path if running from server_fastapi directory
if Path.cwd().name == "server_fastapi" or str(Path.cwd()).endswith("server_fastapi"):
    parent_dir = Path.cwd().parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))


def _safe_include(module: str, attr: str, prefix: str, tags: list[str]):
    """Safely include router with fallback to relative imports."""
    try:
        # Try absolute import first
        mod = importlib.import_module(module)
        router = getattr(mod, attr)
        app.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"Loaded router {module} at {prefix}")
    except ImportError:
        # Fallback to relative import
        try:
            relative_module = module.replace("server_fastapi.", ".")
            mod = importlib.import_module(relative_module, package="server_fastapi")
            router = getattr(mod, attr)
            app.include_router(router, prefix=prefix, tags=tags)
            logger.info(f"Loaded router {relative_module} at {prefix}")
        except Exception as e:
            logger.warning(f"Skipping router {module}: {e}")
    except Exception as e:
        logger.warning(f"Skipping router {module}: {e}")


logger.info("Loading routers with resilient strategy...")

_safe_include("server_fastapi.routes.auth", "router", "/api/auth", ["Authentication"])
# NOTE: auth_saas.py router removed to eliminate duplicate Operation IDs
# All endpoints from auth_saas.py are now available in auth.py (including /me endpoint)
# _safe_include("server_fastapi.routes.auth_saas", "router", "/api", ["Authentication"])
# NOTE: exchange_keys.py removed - platform uses blockchain/DEX trading exclusively
# _safe_include("server_fastapi.routes.exchange_keys", "router", "/api", ["Exchange Keys"])
_safe_include("server_fastapi.routes.billing", "router", "/api", ["Billing"])
_safe_include("server_fastapi.routes.admin", "router", "/api", ["Admin"])
_safe_include("server_fastapi.routes.bots", "router", "/api/bots", ["Bots"])
_safe_include("server_fastapi.routes.bot_learning", "router", "", ["Bot Learning"])
_safe_include("server_fastapi.routes.grid_trading", "router", "/api", ["Grid Trading"])
_safe_include("server_fastapi.routes.dca_trading", "router", "/api", ["DCA Trading"])
_safe_include(
    "server_fastapi.routes.infinity_grid", "router", "/api", ["Infinity Grid"]
)
_safe_include("server_fastapi.routes.trailing_bot", "router", "/api", ["Trailing Bot"])
_safe_include(
    "server_fastapi.routes.futures_trading", "router", "/api", ["Futures Trading"]
)
_safe_include(
    "server_fastapi.routes.crash_reports", "router", "/api", ["Crash Reports"]
)
_safe_include(
    "server_fastapi.routes.trading_safety",
    "router",
    "/api/trading-safety",
    ["Trading Safety"],
)
_safe_include(
    "server_fastapi.routes.sl_tp", "router", "/api/sl-tp", ["Stop Loss / Take Profit"]
)
_safe_include("server_fastapi.routes.ml_training", "router", "/api/ml", ["ML Training"])
_safe_include("server_fastapi.routes.markets", "router", "/api/markets", ["Markets"])
_safe_include("server_fastapi.routes.trades", "router", "/api/trades", ["Trades"])
_safe_include(
    "server_fastapi.routes.advanced_orders",
    "router",
    "/api/advanced-orders",
    ["Advanced Orders"],
)
_safe_include("server_fastapi.routes.sentiment", "router", "", ["Sentiment"])
_safe_include("server_fastapi.routes.logs", "router", "/api/logs", ["Logs"])
_safe_include(
    "server_fastapi.routes.price_alerts",
    "router",
    "/api/price-alerts",
    ["Price Alerts"],
)
_safe_include(
    "server_fastapi.routes.analytics", "router", "/api/analytics", ["Analytics"]
)
_safe_include(
    "server_fastapi.routes.web_vitals", "router", "/api/analytics", ["Analytics"]
)
_safe_include(
    "server_fastapi.routes.portfolio", "router", "/api/portfolio", ["Portfolio"]
)
_safe_include(
    "server_fastapi.routes.preferences", "router", "/api/preferences", ["Preferences"]
)
_safe_include(
    "server_fastapi.routes.notifications",
    "router",
    "/api/notifications",
    ["Notifications"],
)
_safe_include(
    "server_fastapi.routes.backtesting", "router", "/api/backtesting", ["Backtesting"]
)
_safe_include(
    "server_fastapi.routes.risk_management", "router", "", ["Risk Management"]
)
_safe_include(
    "server_fastapi.routes.risk_scenarios",
    "router",
    "/api/risk-scenarios",
    ["Risk Scenarios"],
)
_safe_include(
    "server_fastapi.routes.monitoring", "router", "", ["Production Monitoring"]
)

# Integrations with fallback stub
try:
    mod = importlib.import_module("server_fastapi.routes.integrations")
    app.include_router(
        getattr(mod, "router"), prefix="/api/integrations", tags=["Integrations"]
    )
    logger.info("Loaded integrations router")
except Exception as e:
    logger.warning(f"Failed to load integrations router ({e}); registering stub.")
    from fastapi import APIRouter

    integrations_stub = APIRouter()

    @integrations_stub.get("/status")
    async def integrations_status_stub():
        return {"started": False, "adapters": {}, "integrations": {}}

    app.include_router(
        integrations_stub, prefix="/api/integrations", tags=["Integrations (stub)"]
    )

_safe_include(
    "server_fastapi.routes.recommendations",
    "router",
    "/api/recommendations",
    ["Recommendations"],
)
_safe_include(
    "server_fastapi.routes.trading_mode", "router", "/api/trading", ["Trading Mode"]
)
_safe_include(
    "server_fastapi.routes.audit_logs", "router", "/api/audit-logs", ["Audit Logs"]
)
_safe_include("server_fastapi.routes.audit", "router", "", ["Audit Logs"])
_safe_include("server_fastapi.routes.fees", "router", "/api/fees", ["Fees"])
# Health routes consolidated into health_advanced.py (registered below)
_safe_include("server_fastapi.routes.status", "router", "/api/status", ["Status"])
_safe_include("server_fastapi.routes.ws", "router", "", ["WebSocket"])
_safe_include(
    "server_fastapi.routes.websocket_portfolio",
    "router",
    "/api/ws/portfolio",
    ["WebSocket Portfolio"],
)
_safe_include(
    "server_fastapi.routes.circuit_breaker_metrics", "router", "", ["Circuit Breakers"]
)
_safe_include("server_fastapi.routes.ai_analysis", "router", "", ["AI Analysis"])
_safe_include(
    "server_fastapi.routes.cache_management", "router", "", ["Cache Management"]
)
_safe_include("server_fastapi.routes.cache_warmer", "router", "", ["Cache Warmer"])
_safe_include(
    "server_fastapi.routes.metrics_monitoring", "router", "", ["Metrics & Monitoring"]
)
_safe_include(
    "server_fastapi.routes.business_metrics",
    "router",
    "/api/business-metrics",
    ["Business Metrics"],
)
_safe_include(
    "server_fastapi.routes.platform_health",
    "router",
    "",
    ["Platform Health"],
)
_safe_include(
    "server_fastapi.routes.nps_tracking",
    "router",
    "",
    ["NPS Tracking"],
)
_safe_include(
    "server_fastapi.routes.performance_profiling",
    "router",
    "/api/performance-profiling",
    ["Performance Profiling"],
)
_safe_include(
    "server_fastapi.routes.transaction_monitoring",
    "router",
    "",
    ["Transaction Monitoring"],
)
_safe_include("server_fastapi.routes.metrics", "router", "", ["Prometheus Metrics"])
_safe_include(
    "server_fastapi.routes.portfolio_rebalance", "router", "", ["Portfolio Rebalancing"]
)
_safe_include(
    "server_fastapi.routes.backtesting_enhanced", "router", "", ["Enhanced Backtesting"]
)
_safe_include("server_fastapi.routes.marketplace", "router", "/api/marketplace", ["API Marketplace"])
# NOTE: arbitrage.py route file removed - functionality consolidated into dex_trading.py
# _safe_include(
#     "server_fastapi.routes.arbitrage", "router", "", ["Multi-Exchange Arbitrage"]
# )
_safe_include("server_fastapi.routes.export", "router", "/api/export", ["Export"])
_safe_include(
    "server_fastapi.routes.advanced_risk", "router", "/api/risk", ["Advanced Risk"]
)
_safe_include(
    "server_fastapi.routes.favorites", "router", "/api/favorites", ["Favorites"]
)
_safe_include(
    "server_fastapi.routes.performance", "router", "/api/performance", ["Performance"]
)
_safe_include("server_fastapi.routes.strategies", "router", "", ["Strategies"])
_safe_include("server_fastapi.routes.payments", "router", "", ["Payments"])
_safe_include("server_fastapi.routes.licensing", "router", "", ["Licensing"])
_safe_include("server_fastapi.routes.demo_mode", "router", "", ["Demo Mode"])
_safe_include("server_fastapi.routes.ml_v2", "router", "", ["ML V2"])
_safe_include("server_fastapi.routes.ai_copilot", "router", "", ["AI Copilot"])
_safe_include("server_fastapi.routes.automation", "router", "", ["Automation"])
_safe_include(
    "server_fastapi.routes.copy_trading",
    "router",
    "/api/copy-trading",
    ["Copy Trading"],
)
_safe_include(
    "server_fastapi.routes.marketplace",
    "router",
    "/api/marketplace",
    ["Marketplace"],
)
_safe_include(
    "server_fastapi.routes.indicators",
    "router",
    "/api/indicators",
    ["Indicators"],
)
_safe_include(
    "server_fastapi.routes.leaderboard", "router", "/api/leaderboard", ["Leaderboard"]
)
_safe_include(
    "server_fastapi.routes.two_factor",
    "router",
    "/api/2fa",
    ["Two-Factor Authentication"],
)
_safe_include("server_fastapi.routes.kyc", "router", "/api/kyc", ["KYC Verification"])
_safe_include("server_fastapi.routes.wallet", "router", "/api/wallet", ["Wallet"])
_safe_include("server_fastapi.routes.institutional_wallets", "router", "/api/institutional-wallets", ["Institutional Wallets"])
_safe_include("server_fastapi.routes.staking", "router", "/api/staking", ["Staking"])
_safe_include("server_fastapi.routes.websocket_wallet", "router", "", ["WebSocket"])
# Health wallet routes consolidated into health_advanced.py
_safe_include(
    "server_fastapi.routes.payment_methods", "router", "", ["Payment Methods"]
)
_safe_include(
    "server_fastapi.routes.crypto_transfer", "router", "", ["Crypto Transfer"]
)
_safe_include("server_fastapi.routes.cold_storage", "router", "", ["Cold Storage"])
_safe_include(
    "server_fastapi.routes.query_optimization", "router", "", ["Query Optimization"]
)
_safe_include("server_fastapi.routes.activity", "router", "/api/activity", ["Activity"])
_safe_include(
    "server_fastapi.routes.background_jobs", "router", "", ["Background Jobs"]
)
_safe_include("server_fastapi.routes.deposit_safety", "router", "", ["Deposit Safety"])
_safe_include(
    "server_fastapi.routes.platform_revenue", "router", "", ["Platform Revenue"]
)
_safe_include("server_fastapi.routes.backups", "router", "", ["Backups"])
_safe_include("server_fastapi.routes.onboarding", "router", "", ["Onboarding"])
_safe_include("server_fastapi.routes.user_analytics", "router", "", ["User Analytics"])
_safe_include("server_fastapi.routes.disaster_recovery", "router", "", ["Disaster Recovery"])
_safe_include("server_fastapi.routes.social", "router", "", ["Social & Community"])
_safe_include("server_fastapi.routes.yield_farming", "router", "", ["Yield Farming"])
_safe_include("server_fastapi.routes.security_monitoring", "router", "", ["Security Monitoring"])
_safe_include("server_fastapi.routes.feature_flags", "router", "", ["Feature Flags"])
_safe_include("server_fastapi.routes.gdpr", "router", "", ["GDPR Compliance"])
_safe_include("server_fastapi.routes.webhooks", "router", "", ["Webhooks"])
_safe_include("server_fastapi.routes.api_keys", "router", "", ["API Keys"])
_safe_include("server_fastapi.services.wal_archiving_service", "WALArchivingService", "", [])
_safe_include("server_fastapi.routes.tax_reporting", "router", "", ["Tax Reporting"])
_safe_include(
    "server_fastapi.routes.security_whitelists", "router", "", ["Security Whitelists"]
)
_safe_include(
    "server_fastapi.routes.fraud_detection", "router", "", ["Fraud Detection"]
)
_safe_include(
    "server_fastapi.routes.dex_trading", "router", "/api/dex", ["DEX Trading"]
)
_safe_include("server_fastapi.routes.dex_positions", "router", "", ["DEX Positions"])
_safe_include("server_fastapi.routes.mev_protection", "router", "", ["MEV Protection"])
_safe_include("server_fastapi.routes.wallets", "router", "/api/wallets", ["Wallets"])
# institutional_wallets already included above (line 1509)
_safe_include("server_fastapi.routes.hft", "router", "", ["HFT"])
_safe_include("server_fastapi.routes.tax_reporting", "router", "", ["Tax Reporting"])
_safe_include("server_fastapi.routes.onboarding", "router", "", ["Onboarding"])
_safe_include("server_fastapi.routes.batch_api", "router", "", ["Batch API"])
_safe_include("server_fastapi.routes.observability", "router", "", ["Observability"])
_safe_include("server_fastapi.routes.treasury", "router", "", ["Treasury"])
_safe_include("server_fastapi.routes.security_auth", "router", "", ["Security Authentication"])
_safe_include("server_fastapi.routes.zkp", "router", "", ["Zero-Knowledge Proofs"])
_safe_include("server_fastapi.routes.mpc_tecdsa", "router", "", ["MPC & TECDSA"])
_safe_include("server_fastapi.routes.biometric_did", "router", "", ["Biometric & DID"])
_safe_include("server_fastapi.routes.hardware_wallet", "router", "", ["Hardware Wallet"])
_safe_include(
    "server_fastapi.routes.withdrawals", "router", "/api/withdrawals", ["Withdrawals"]
)
_safe_include(
    "server_fastapi.routes.security_audit",
    "router",
    "/api/security",
    ["Security Audit"],
)
_safe_include(
    "server_fastapi.routes.security_compliance",
    "router",
    "/api/security",
    ["Security Compliance"],
)
_safe_include("server_fastapi.routes.alerting", "router", "", ["Alerting"])
_safe_include(
    "server_fastapi.routes.database_performance", "router", "", ["Database Performance"]
)
_safe_include(
    "server_fastapi.routes.cache_management", "router", "", ["Cache Management"]
)

# Consolidated health check routes (includes all health checks from health.py, health_comprehensive.py, health_wallet.py)
try:
    from server_fastapi.routes.health_advanced import router as health_advanced_router

    app.include_router(health_advanced_router, prefix="", tags=["Health"])
    logger.info("Consolidated health check routes loaded")
except Exception as e:
    logger.warning(f"Health check routes not loaded: {e}")

# Add middleware health check routes
try:
    from .middleware.health_check import router as middleware_health_router
    
    app.include_router(middleware_health_router, tags=["Middleware Health"])
    logger.info("Middleware health check routes loaded")
except Exception as e:
    logger.warning(f"Middleware health check routes not loaded: {e}")

# Add middleware monitoring routes
try:
    from .routes.middleware_health import router as middleware_stats_router
    
    app.include_router(middleware_stats_router, tags=["Middleware Monitoring"])
    logger.info("Middleware monitoring routes loaded")
except Exception as e:
    logger.warning(f"Middleware monitoring routes not loaded: {e}")

# Add API analytics routes
try:
    from .routes.api_analytics import router as api_analytics_router
    
    app.include_router(api_analytics_router, tags=["API Analytics"])
    logger.info("API analytics routes loaded")
except Exception as e:
    logger.warning(f"API analytics routes not loaded: {e}")

# Add webhook management routes
try:
    from .routes.webhooks import router as webhooks_router
    
    app.include_router(webhooks_router)
    logger.info("Webhook management routes loaded")
except Exception as e:
    logger.warning(f"Webhook routes not loaded: {e}")

# Add feature flag routes
try:
    from .routes.feature_flags import router as feature_flags_router
    
    app.include_router(feature_flags_router)
    logger.info("Feature flag routes loaded")
except Exception as e:
    logger.warning(f"Feature flag routes not loaded: {e}")

# Add error recovery routes
try:
    from .routes.error_recovery import router as error_recovery_router
    
    app.include_router(error_recovery_router)
    logger.info("Error recovery routes loaded")
except Exception as e:
    logger.warning(f"Error recovery routes not loaded: {e}")

# Add monitoring routes
try:
    from .routes.monitoring import router as monitoring_router
    
    app.include_router(monitoring_router)
    logger.info("Monitoring routes loaded")
except Exception as e:
    logger.warning(f"Monitoring routes not loaded: {e}")

# Add security audit routes
try:
    from .routes.security_audit import router as security_audit_router
    
    app.include_router(security_audit_router)
    logger.info("Security audit routes loaded")
except Exception as e:
    logger.warning(f"Security audit routes not loaded: {e}")

# Add logging routes
try:
    from .routes.logging import router as logging_router
    
    app.include_router(logging_router)
    logger.info("Logging routes loaded")
except Exception as e:
    logger.warning(f"Logging routes not loaded: {e}")

# Add Prometheus metrics endpoint
try:
    from .middleware.prometheus_metrics import get_metrics_response
    
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return get_metrics_response()
    
    logger.info("Prometheus metrics endpoint loaded")
except Exception as e:
    logger.warning(f"Prometheus metrics not available: {e}")

try:
    from server_fastapi.routes.api_versioning import router_v1, router_v2

    app.include_router(router_v1, tags=["API v1"])
    app.include_router(router_v2, tags=["API v2"])
except Exception:
    logger.info("API versioning not loaded")

logger.info("Router loading complete")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    is_development = os.getenv("NODE_ENV") == "development"

    # Performance optimizations for production
    uvicorn_config = {
        "app": app,
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
