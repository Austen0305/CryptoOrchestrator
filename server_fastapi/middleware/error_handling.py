"""
Enhanced error handling middleware for better error responses and logging.
"""

import os
import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def error_handler_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    Global error handling middleware that catches all exceptions
    and returns standardized error responses.
    """
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        # Handle Pydantic validation errors
        logger.warning(f"Validation error on {request.url.path}: {e.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": e.errors(),
                "path": str(request.url.path),
            },
        )
    except HTTPException as e:
        # Handle HTTP exceptions
        logger.info(f"HTTP {e.status_code} on {request.url.path}: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "HTTP Error",
                "message": e.detail,
                "status_code": e.status_code,
                "path": str(request.url.path),
            },
        )
    except ValidationError as e:
        # Handle Pydantic validation errors (non-request)
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation Error",
                "message": "Invalid data format",
                "details": str(e),
                "path": str(request.url.path),
            },
        )
    except ValueError as e:
        # Handle value errors
        logger.warning(f"Value error on {request.url.path}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "message": str(e),
                "path": str(request.url.path),
            },
        )
    except KeyError as e:
        # Handle missing key errors
        logger.warning(f"Missing key on {request.url.path}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "message": f"Missing required field: {str(e)}",
                "path": str(request.url.path),
            },
        )
    except Exception as e:
        # Handle all other exceptions
        error_traceback = traceback.format_exc()
        logger.error(
            f"Unhandled exception on {request.url.path}: {str(e)}\n{error_traceback}",
            exc_info=True
        )
        
        # In production, don't expose internal error details
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if is_production else str(e),
                "path": str(request.url.path),
                "traceback": error_traceback if not is_production else None,
            },
        )


def setup_error_handling(app):
    """
    Setup error handling middleware and exception handlers.
    """
    import os
    
    # Add global error handler middleware
    app.middleware("http")(error_handler_middleware)
    
    # Register exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.info(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.info(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        error_traceback = traceback.format_exc()
        logger.error(
            f"Unhandled exception on {request.url.path}: {str(exc)}\n{error_traceback}",
            exc_info=True
        )
        
        # In production, don't expose internal error details
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if is_production else str(exc),
                "path": str(request.url.path),
                "traceback": error_traceback if not is_production else None,
            },
        )

