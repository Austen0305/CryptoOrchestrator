"""
Middleware Setup Module
Centralized middleware registration and configuration
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from .config import middleware_manager
from .registry import MiddlewareRegistry

# Try unified error handler first, fallback to enhanced
try:
    from .unified_error_handler import register_unified_error_handlers
    register_error_handlers = register_unified_error_handlers
except ImportError:
    try:
        from .enhanced_error_handler import register_enhanced_error_handlers
        register_error_handlers = register_enhanced_error_handlers
    except ImportError:
        register_error_handlers = None

logger = logging.getLogger(__name__)


def get_cors_origins() -> list:
    """Get allowed CORS origins from environment or defaults"""
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    
    if allowed_origins_env:
        parsed_origins = [
            origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()
        ]
        cors_origins = []
        for origin in parsed_origins:
            if origin in ["null", "file://", "exp://"]:
                cors_origins.append(origin)
            elif origin.startswith(("http://", "https://")):
                cors_origins.append(origin)
            else:
                logger.warning(f"Skipping invalid CORS origin from environment: {origin}")
        
        if cors_origins:
            return cors_origins
    
    # Default origins
    return [
        "http://localhost:3000", "http://localhost:5173", "http://localhost:8000",
        "http://127.0.0.1:5173", "http://127.0.0.1:8000", "exp://",
        "http://10.0.2.2:8000", "http://127.0.0.1:3000",
        "file://", "null",
    ]


def add_cors_headers(
    response: JSONResponse, request: Request, allowed_origins: list
) -> JSONResponse:
    """Add CORS headers to a response if origin is allowed (utility function)"""
    origin = request.headers.get("origin")
    if origin and "Access-Control-Allow-Origin" not in response.headers:
        origin_allowed = origin in allowed_origins
        if not origin_allowed:
            import re
            origin_allowed = bool(
                re.match(
                    r"https://.*\.onrender\.com$|https://.*\.crypto-orchestrator\.com$|https://.*\.vercel\.app$",
                    origin,
                )
            )
        if origin_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-Requested-With, Accept, Origin"
            )
    return response


def setup_cors_middleware(app: FastAPI) -> None:
    """Setup CORS middleware with proper configuration"""
    cors_origins = get_cors_origins()
    
    if not cors_origins:
        # Default origins including Render domains
        cors_origins = [
            "http://localhost:3000",  # React dev server
            "http://localhost:5173",  # Vite dev server
            "http://localhost:8000",  # FastAPI server
            "http://127.0.0.1:5173",  # Vite alternative
            "http://127.0.0.1:8000",  # FastAPI alternative
            "exp://",  # Expo dev server
            "http://10.0.2.2:8000",  # Android emulator
            "http://127.0.0.1:3000",  # Alternative localhost
            "file://",  # Electron file protocol
            "null",  # Electron null origin
        ]

    # Handle OPTIONS preflight requests explicitly
    @app.middleware("http")
    async def cors_preflight_handler(request: Request, call_next):
        """Handle OPTIONS preflight requests before other middleware"""
        try:
            if request.method == "OPTIONS":
                origin = request.headers.get("origin")
                logger.debug(f"CORS preflight request from origin: {origin}")
                
                if origin:
                    # Check if origin is in allowed list
                    origin_allowed = origin in cors_origins
                    
                    # If not in list, check regex patterns
                    if not origin_allowed:
                        import re
                        origin_allowed = bool(
                            re.match(
                                r"https://.*\.onrender\.com$|https://.*\.crypto-orchestrator\.com$|https://.*\.vercel\.app$|https://.*\.trycloudflare\.com$",
                                origin,
                            )
                        )
                    
                    if origin_allowed:
                        logger.debug(f"Origin {origin} is allowed, returning CORS headers")
                        response = JSONResponse(content={}, status_code=200)
                        response.headers["Access-Control-Allow-Origin"] = origin
                        response.headers["Access-Control-Allow-Credentials"] = "true"
                        response.headers["Access-Control-Allow-Methods"] = (
                            "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                        )
                        response.headers["Access-Control-Allow-Headers"] = (
                            "Authorization, Content-Type, X-Requested-With, Accept, Origin, X-API-Version"
                        )
                        response.headers["Access-Control-Max-Age"] = "86400"
                        return response
                    else:
                        logger.debug(f"Origin {origin} is not allowed")
                
                # If origin not allowed or no origin, still return 200 with no CORS headers
                logger.debug("Returning 200 for OPTIONS without CORS headers")
                return JSONResponse(content={}, status_code=200)
            
            # For non-OPTIONS requests, continue to next middleware
            return await call_next(request)
        except Exception as e:
            logger.error(f"Error in CORS preflight handler: {e}", exc_info=True)
            # Return a safe response even on error
            try:
                return JSONResponse(content={"error": "CORS preflight error"}, status_code=500)
            except Exception as e2:
                logger.error(f"Failed to create error response: {e2}", exc_info=True)
                # Last resort - return a basic response
                from fastapi import Response
                return Response(status_code=500)
    
    # Additional CORS middleware to ensure all responses (including errors) have CORS headers
    @app.middleware("http")
    async def cors_headers_middleware(request: Request, call_next):
        """Ensure all responses have CORS headers, even error responses"""
        try:
            response = await call_next(request)
            # If response doesn't have CORS headers, add them
            origin = request.headers.get("origin")
            if origin and "Access-Control-Allow-Origin" not in response.headers:
                origin_allowed = origin in cors_origins
                if not origin_allowed:
                    import re
                    origin_allowed = bool(
                        re.match(
                            r"https://.*\.onrender\.com$|https://.*\.crypto-orchestrator\.com$|https://.*\.vercel\.app$|https://.*\.trycloudflare\.com$",
                            origin,
                        )
                    )
                if origin_allowed:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = (
                        "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                    )
                    response.headers["Access-Control-Allow-Headers"] = (
                        "Authorization, Content-Type, X-Requested-With, Accept, Origin, X-API-Version"
                    )
            return response
        except Exception as e:
            # Handle exceptions that occur during request processing
            logger.error(f"Exception in CORS middleware: {e}", exc_info=True)
            origin = request.headers.get("origin")
            origin_allowed = False
            if origin:
                origin_allowed = origin in cors_origins
                if not origin_allowed:
                    import re
                    origin_allowed = bool(
                        re.match(
                            r"https://.*\.onrender\.com$|https://.*\.crypto-orchestrator\.com$|https://.*\.vercel\.app$",
                            origin,
                        )
                    )

            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

            if origin_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, X-Requested-With, Accept, Origin"
                )

            return response

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"https://.*\.onrender\.com$|https://.*\.crypto-orchestrator\.com$|https://.*\.vercel\.app$|https://.*\.trycloudflare\.com$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "X-API-Version",
        ],
        max_age=86400,  # Cache preflight for 24 hours
    )
    
    logger.info("CORS middleware configured")


def setup_rate_limiting(app: FastAPI) -> None:
    """Setup rate limiting middleware"""
    try:
        from ..rate_limit_config import limiter, _rate_limit_exceeded_handler

        if limiter:
            app.state.limiter = limiter
            app.add_middleware(SlowAPIMiddleware)
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
            logger.info("Rate limiting middleware enabled")
        else:
            logger.warning("Rate limiter not available")
    except ImportError:
        logger.warning("Rate limiting not available (slowapi not installed)")


def setup_trusted_hosts(app: FastAPI) -> None:
    """Setup trusted host middleware (production only)"""
    is_production = os.getenv("NODE_ENV") == "production"
    is_testing = os.getenv("TESTING", "false").lower() == "true"
    
    if is_production and not is_testing:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1"]
        )
        logger.info("Trusted host middleware enabled")


def setup_all_middleware(app: FastAPI) -> dict:
    """
    Setup all middleware components in the correct order
    
    Returns:
        Dictionary with setup statistics
    """
    # Add profiling middleware first (if enabled)
    profiling_enabled = os.getenv("ENABLE_MIDDLEWARE_PROFILING", "false").lower() == "true"
    if profiling_enabled:
        try:
            from .profiling import ProfilingMiddleware, enable_profiling
            app.add_middleware(ProfilingMiddleware, enabled=True)
            enable_profiling()
            logger.info("Middleware profiling enabled")
        except Exception as e:
            logger.warning(f"Failed to enable profiling middleware: {e}")
    
    registry = MiddlewareRegistry(app)
    
    # Get enabled middleware configurations (sorted by priority)
    enabled_middlewares = middleware_manager.get_enabled_middlewares()
    
    # Register all middleware
    stats = registry.register_all(enabled_middlewares)
    
    # Setup special middleware (CORS, rate limiting, etc.)
    setup_cors_middleware(app)
    setup_rate_limiting(app)
    setup_trusted_hosts(app)
    
    # Register error handlers
    if register_error_handlers:
        try:
            register_error_handlers(app)
        except Exception as e:
            logger.warning(f"Failed to register error handlers: {e}")
    else:
        logger.warning("No error handlers available")
    
    # Initialize API analytics if available
    try:
        from .api_analytics import api_analytics
        app.state.api_analytics = api_analytics
        logger.info("API analytics initialized")
    except Exception as e:
        logger.debug(f"API analytics not available: {e}")
    
    return {
        **stats,
        "summary": registry.get_registration_summary(),
    }

