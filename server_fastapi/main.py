# Set environment variables to disable CUDA/GPU before any imports
# This prevents CUDA initialization errors on systems without GPU
import os
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')  # Suppress TensorFlow warnings
os.environ.setdefault('TORCH_CUDA_ARCH_LIST', '')
os.environ.setdefault('NUMBA_DISABLE_JIT', '1')

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

# Import validation middleware
try:
    from .middleware.validation import InputValidationMiddleware
except ImportError:
    InputValidationMiddleware = None

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
    try:
        from . import database as _db_module  # Prefer module over package directory
        init_database = getattr(_db_module, 'init_database', None)
    except Exception:
        init_database = None
except ImportError:
    db_pool = None

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

# Configure logging - enhanced for desktop app usage
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console logging
        logging.FileHandler('logs/fastapi.log', mode='a') if os.path.exists('logs') else logging.StreamHandler()
    ]
)
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
    
    # Initialize distributed rate limiter
    try:
        from .middleware.distributed_rate_limiter import get_rate_limiter
        rate_limiter = get_rate_limiter()
        await rate_limiter.connect()
        app.state.rate_limiter = rate_limiter
        logger.info("✅ Distributed rate limiter initialized")
    except Exception as e:
        logger.warning(f"Distributed rate limiter initialization failed: {e}")
        app.state.rate_limiter = None
    
    # Initialize Redis cache manager with fallback
    if redis_available and cache_manager:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            cache_manager.redis_url = redis_url
            await cache_manager.connect()
            if cache_manager.available:
                logger.info(f"✅ Redis cache initialized at {redis_url}")
            else:
                logger.info("⚠️  Redis unavailable, using in-memory cache fallback")
        except Exception as e:
            logger.warning(f"Redis initialization failed, using in-memory cache: {e}")
    
    # Initialize Redis for caching if available (legacy)
    if redis_available and init_redis:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            # Add timeout to prevent blocking startup
            redis_client = await asyncio.wait_for(
                aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True),
                timeout=2.0
            )
            await asyncio.wait_for(redis_client.ping(), timeout=1.0)
            init_redis(redis_client)
            logger.info(f"Redis cache initialized at {redis_url}")
        except asyncio.TimeoutError:
            logger.warning("Redis connection timeout - caching disabled")
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {e}")
    
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
            environment = os.getenv("ENVIRONMENT", "development")
            if init_sentry(environment=environment):
                logger.info(f"✅ Sentry error tracking initialized for {environment}")
            else:
                logger.info("⚠️  Sentry DSN not provided, error tracking disabled")
        except Exception as e:
            logger.warning(f"Sentry initialization failed: {e}")
    
    # Register health checks
    try:
        from .routes.health_advanced import health_checker
        logger.info("Health check system initialized")
    except ImportError:
        logger.warning("Advanced health checks not available")
    
    # Start market data streaming service
    try:
        from .services.websocket_manager import connection_manager
        from .services.market_streamer import get_market_streamer
        
        streamer = get_market_streamer(connection_manager)
        streamer.start()
        app.state.market_streamer = streamer
        logger.info("✅ Market data streaming service started")
    except Exception as e:
        logger.warning(f"Market data streaming not available: {e}")
    
    # Export OpenAPI JSON schema to docs/openapi.json
    try:
        os.makedirs("docs", exist_ok=True)
        openapi_schema = app.openapi()
        with open("docs/openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        logger.info("✅ OpenAPI schema exported to docs/openapi.json")
    except Exception as e:
        logger.warning(f"Failed to export OpenAPI schema: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI server...")
    
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
    
    # Close database connections
    if db_pool:
        try:
            await db_pool.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

# Create FastAPI app - optimized for desktop app performance
app = FastAPI(
    title="CryptoOrchestrator API",
    description="Professional AI-Powered Crypto Trading Platform API",
    version="1.0.0",
    lifespan=lifespan,
    # Performance optimizations for desktop app
    debug=False,  # Disable debug mode for production performance
    docs_url="/docs" if os.getenv("NODE_ENV") == "development" else None,  # Hide docs in production
    redoc_url="/redoc" if os.getenv("NODE_ENV") == "development" else None,  # Hide redoc in production
)

# Add rate limiting middleware unless running under pytest (disable for tests)
if limiter and not os.getenv("PYTEST_CURRENT_TEST"):
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add distributed rate limiter middleware (optional, controlled by env var)
if os.getenv("ENABLE_DISTRIBUTED_RATE_LIMIT", "false").lower() == "true":
    try:
        from .middleware.rate_limit_middleware import RateLimitMiddleware
        # Rate limiter will be available after lifespan startup
        app.add_middleware(RateLimitMiddleware, rate_limiter=None)
        logger.info("Distributed rate limiting middleware enabled")
    except Exception as e:
        logger.warning(f"Could not enable distributed rate limiting: {e}")

# Enhanced security headers middleware
try:
    from .middleware.enhanced_security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Enhanced security headers middleware enabled")
except ImportError:
    # Fallback to basic security headers
    logger.warning("Enhanced security headers not available, using basic headers")
    @app.middleware("http")
    async def add_basic_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

# Add monitoring middleware
if MonitoringMiddleware:
    app.add_middleware(MonitoringMiddleware)

# Add performance monitoring middleware
try:
    from .middleware.performance_monitor import PerformanceMonitoringMiddleware, performance_monitor
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.state.performance_monitor = performance_monitor
    logger.info("Performance monitoring middleware enabled")
except ImportError:
    logger.warning("Performance monitoring middleware not available")

# Add input validation middleware
if InputValidationMiddleware:
    app.add_middleware(InputValidationMiddleware)

# Add audit logging middleware
try:
    from .middleware.audit_logger import AuditLoggerMiddleware
    app.add_middleware(AuditLoggerMiddleware)
    logger.info("Audit logging middleware enabled")
except ImportError:
    logger.warning("Audit logging middleware not available")

# Add request ID middleware for request tracking
try:
    from .middleware.request_id import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)
    logger.info("Request ID middleware enabled")
except ImportError:
    logger.warning("Request ID middleware not available")

# Add enhanced error handling middleware
try:
    from .middleware.error_handling import setup_error_handling
    setup_error_handling(app)
    logger.info("Enhanced error handling middleware enabled")
except ImportError as e:
    logger.warning(f"Enhanced error handling not available: {e}")

# Enhanced security headers middleware (already added above)

# CORS middleware - optimized for desktop app usage with proper origin validation
def validate_origin(origin: str) -> bool:
    """Validate CORS origins for security"""
    allowed_origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # FastAPI server
        "http://127.0.0.1:3000", # Alternative localhost
        "http://127.0.0.1:5173", # Alternative localhost
        "http://127.0.0.1:8000", # Alternative localhost
        "file://",               # Electron file protocol
        "null",                  # Electron null origin
        # Mobile app origins (for physical devices)
        "exp://",                # Expo dev server
        "http://192.168.1.1:8000",  # Common local network
        "http://10.0.2.2:8000",     # Android emulator
    ]

    # Additional production origins from environment
    production_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if production_origins:
        allowed_origins.extend([origin.strip() for origin in production_origins if origin.strip()])

    return origin in allowed_origins

# Get allowed origins from environment or use defaults
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # Parse comma-separated origins from environment
    cors_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    # Default origins including Render domains
    cors_origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # FastAPI server
        "http://127.0.0.1:5173",  # Vite alternative
        "http://127.0.0.1:8000",  # FastAPI alternative
        "exp://",                 # Expo dev server
        "http://10.0.2.2:8000",   # Android emulator
        "http://127.0.0.1:3000", # Alternative localhost
        "http://127.0.0.1:5173", # Alternative localhost
        "http://127.0.0.1:8000", # Alternative localhost
        "file://",               # Electron file protocol
        "null",                  # Electron null origin
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.onrender\.com$|https://.*\.crypto-orchestrator\.com$",  # Render and production domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"],
    max_age=86400,  # Cache preflight for 24 hours
)

# Trusted host middleware (for production)
if os.getenv("NODE_ENV") == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# Register structured error handlers
try:
    from .middleware.error_handler import register_error_handlers
    register_error_handlers(app)
    logger.info("Structured error handlers registered")
except ImportError:
    logger.warning("Structured error handlers not available, using default")

# Keep default exception handler as fallback
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # This will be caught by structured error handler if available
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    # Return more detailed error info in development
    if os.getenv("NODE_ENV") == "development":
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "status_code": 500,
                    "details": {
                        "error": str(exc),
                        "type": type(exc).__name__
                    }
                }
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "status_code": 500
                }
            }
        )

# Health check endpoint with database status
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "CryptoOrchestrator API",
        "database": "unknown"
    }
    
    # Check database connection if available
    if db_pool:
        try:
            is_healthy = await db_pool.health_check()
            health_status["database"] = "healthy" if is_healthy else "unhealthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
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

import importlib

def _safe_include(module: str, attr: str, prefix: str, tags: list[str]):
    try:
        mod = importlib.import_module(module)
        router = getattr(mod, attr)
        app.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"Loaded router {module} at {prefix}")
    except Exception as e:
        logger.warning(f"Skipping router {module}: {e}")

logger.info("Loading routers with resilient strategy...")

_safe_include("server_fastapi.routes.auth", "router", "/api/auth", ["Authentication"])
_safe_include("server_fastapi.routes.auth_saas", "router", "/api", ["Authentication"])
_safe_include("server_fastapi.routes.billing", "router", "/api", ["Billing"])
_safe_include("server_fastapi.routes.admin", "router", "/api", ["Admin"])
_safe_include("server_fastapi.routes.exchange_keys_saas", "router", "/api", ["Exchange Keys"])
_safe_include("server_fastapi.routes.bots", "router", "/api/bots", ["Bots"])
_safe_include("server_fastapi.routes.bot_learning", "router", "", ["Bot Learning"])
_safe_include("server_fastapi.routes.markets", "router", "/api/markets", ["Markets"])
_safe_include("server_fastapi.routes.trades", "router", "/api/trades", ["Trades"])
_safe_include("server_fastapi.routes.analytics", "router", "/api/analytics", ["Analytics"])
_safe_include("server_fastapi.routes.web_vitals", "router", "", ["Web Vitals"])
_safe_include("server_fastapi.routes.portfolio", "router", "/api/portfolio", ["Portfolio"])
_safe_include("server_fastapi.routes.preferences", "router", "/api/preferences", ["Preferences"])
_safe_include("server_fastapi.routes.notifications", "router", "/api/notifications", ["Notifications"])
_safe_include("server_fastapi.routes.backtesting", "router", "/api/backtesting", ["Backtesting"])
_safe_include("server_fastapi.routes.risk_management", "router", "", ["Risk Management"])
_safe_include("server_fastapi.routes.risk_scenarios", "router", "/api/risk-scenarios", ["Risk Scenarios"])

# Integrations with fallback stub
try:
    mod = importlib.import_module("server_fastapi.routes.integrations")
    app.include_router(getattr(mod, "router"), prefix="/api/integrations", tags=["Integrations"])
    logger.info("Loaded integrations router")
except Exception as e:
    logger.warning(f"Failed to load integrations router ({e}); registering stub.")
    from fastapi import APIRouter
    integrations_stub = APIRouter()
    @integrations_stub.get("/status")
    async def integrations_status_stub():
        return {"started": False, "adapters": {}, "integrations": {}}
    app.include_router(integrations_stub, prefix="/api/integrations", tags=["Integrations (stub)"])

_safe_include("server_fastapi.routes.recommendations", "router", "/api/recommendations", ["Recommendations"])
_safe_include("server_fastapi.routes.exchange_keys", "router", "/api/exchange-keys", ["Exchange Keys"])
_safe_include("server_fastapi.routes.exchange_status", "router", "/api/exchange-status", ["Exchange Status"])
_safe_include("server_fastapi.routes.trading_mode", "router", "/api/trading", ["Trading Mode"])
_safe_include("server_fastapi.routes.audit_logs", "router", "/api/audit-logs", ["Audit Logs"])
_safe_include("server_fastapi.routes.fees", "router", "/api/fees", ["Fees"])
_safe_include("server_fastapi.routes.health", "router", "/api/health", ["Health"])
_safe_include("server_fastapi.routes.status", "router", "/api/status", ["Status"])
_safe_include("server_fastapi.routes.ws", "router", "", ["WebSocket"])
_safe_include("server_fastapi.routes.websocket_enhanced", "router", "", ["WebSocket Enhanced"])
_safe_include("server_fastapi.routes.circuit_breaker_metrics", "router", "", ["Circuit Breakers"])
_safe_include("server_fastapi.routes.ai_analysis", "router", "", ["AI Analysis"])
_safe_include("server_fastapi.routes.cache_management", "router", "", ["Cache Management"])
_safe_include("server_fastapi.routes.metrics_monitoring", "router", "", ["Metrics & Monitoring"])
_safe_include("server_fastapi.routes.metrics", "router", "", ["Prometheus Metrics"])
_safe_include("server_fastapi.routes.portfolio_rebalance", "router", "", ["Portfolio Rebalancing"])
_safe_include("server_fastapi.routes.backtesting_enhanced", "router", "", ["Enhanced Backtesting"])
_safe_include("server_fastapi.routes.marketplace", "router", "", ["API Marketplace"])
_safe_include("server_fastapi.routes.arbitrage", "router", "", ["Multi-Exchange Arbitrage"])
_safe_include("server_fastapi.routes.performance", "router", "/api/performance", ["Performance"])
_safe_include("server_fastapi.routes.strategies", "router", "", ["Strategies"])
_safe_include("server_fastapi.routes.payments", "router", "", ["Payments"])
_safe_include("server_fastapi.routes.licensing", "router", "", ["Licensing"])
_safe_include("server_fastapi.routes.demo_mode", "router", "", ["Demo Mode"])
_safe_include("server_fastapi.routes.ml_v2", "router", "", ["ML V2"])
_safe_include("server_fastapi.routes.exchanges", "router", "", ["Exchanges"])
_safe_include("server_fastapi.routes.ai_copilot", "router", "", ["AI Copilot"])
_safe_include("server_fastapi.routes.automation", "router", "", ["Automation"])

try:
    from server_fastapi.routes.health_advanced import router as health_advanced_router
    app.include_router(health_advanced_router, prefix="", tags=["Health"])
except Exception:
    logger.info("Advanced health checks not loaded")

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
