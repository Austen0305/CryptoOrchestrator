"""
API Documentation Enhancements
Provides enhanced OpenAPI/Swagger documentation with examples and schemas
"""

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)


def enhance_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """
    Enhance OpenAPI schema with:
    - Better descriptions
    - Request/response examples
    - Error response schemas
    - Security schemes
    - Tags and categories
    """

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description or "CryptoOrchestrator API",
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authentication",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key authentication",
        },
    }

    # Add default security
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Enhance error responses
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "example": "VALIDATION_ERROR"},
                    "message": {
                        "type": "string",
                        "example": "Request validation failed",
                    },
                    "status_code": {"type": "integer", "example": 422},
                    "details": {"type": "object"},
                    "suggestion": {"type": "string"},
                },
            },
            "request_id": {
                "type": "string",
                "example": "123e4567-e89b-12d3-a456-426614174000",
            },
            "timestamp": {"type": "string", "format": "date-time"},
        },
    }

    # Add common response schemas
    openapi_schema["components"]["schemas"]["SuccessResponse"] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "data": {"type": "object"},
            "message": {"type": "string"},
        },
    }

    # Add pagination schema
    openapi_schema["components"]["schemas"]["Pagination"] = {
        "type": "object",
        "properties": {
            "page": {"type": "integer", "example": 1},
            "page_size": {"type": "integer", "example": 20},
            "total": {"type": "integer", "example": 100},
            "total_pages": {"type": "integer", "example": 5},
        },
    }

    app.openapi_schema = openapi_schema
    return openapi_schema


def add_api_examples(app: FastAPI):
    """Add examples to API endpoints"""
    # This would be called during app initialization
    # Examples would be added to route decorators
    pass
