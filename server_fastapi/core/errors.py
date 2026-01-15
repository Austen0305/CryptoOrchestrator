from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def setup_exception_handlers(app: FastAPI):
    """
    Register RFC 9457 compliant exception handlers.
    Aligned with 2026 API standards.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "about:blank",
                "title": "HTTP Error",
                "status": exc.status_code,
                "detail": exc.detail,
                "instance": str(request.url),
            },
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "type": "about:blank",
                "title": "Validation Error",
                "status": 422,
                "detail": "Input validation failed",
                "errors": exc.errors(),
                "instance": str(request.url),
            },
            media_type="application/problem+json",
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # In production, likely hide details or use Sentry ID
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": str(exc),  # Warning: Be careful exposing this in prod
                "instance": str(request.url),
            },
            media_type="application/problem+json",
        )
