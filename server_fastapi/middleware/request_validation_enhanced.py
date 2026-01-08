"""
Enhanced Request/Response Validation Middleware
Provides comprehensive validation, sanitization, and transformation
"""

import asyncio
import json
import logging
import re
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class ValidationRule:
    """Validation rule definition"""

    def __init__(
        self,
        field: str,
        validator: Callable,
        error_message: str,
        required: bool = True,
    ):
        self.field = field
        self.validator = validator
        self.error_message = error_message
        self.required = required


class EnhancedRequestValidator:
    """
    Enhanced request validator with:
    - Field-level validation
    - Type checking
    - Sanitization
    - Custom validators
    - Error aggregation
    """

    def __init__(self):
        self.rules: dict[str, list[ValidationRule]] = {}
        self.sanitizers: dict[str, Callable] = {}

    def register_rule(self, endpoint: str, rule: ValidationRule):
        """Register validation rule for endpoint"""
        if endpoint not in self.rules:
            self.rules[endpoint] = []
        self.rules[endpoint].append(rule)

    def register_sanitizer(self, field: str, sanitizer: Callable):
        """Register sanitizer for field"""
        self.sanitizers[field] = sanitizer

    def validate(self, endpoint: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate data against rules"""
        errors = []
        rules = self.rules.get(endpoint, [])

        for rule in rules:
            value = data.get(rule.field)

            # Check required
            if rule.required and value is None:
                errors.append(f"{rule.field}: {rule.error_message}")
                continue

            # Skip if not required and not present
            if not rule.required and value is None:
                continue

            # Validate
            try:
                if not rule.validator(value):
                    errors.append(f"{rule.field}: {rule.error_message}")
            except Exception as e:
                errors.append(f"{rule.field}: Validation error: {e}")

        return len(errors) == 0, errors

    def sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize data"""
        sanitized = data.copy()

        for field, sanitizer in self.sanitizers.items():
            if field in sanitized:
                try:
                    sanitized[field] = sanitizer(sanitized[field])
                except Exception as e:
                    logger.warning(f"Sanitization error for {field}: {e}")

        return sanitized


# Common validators
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def sanitize_string(value: str) -> str:
    """Sanitize string input"""
    # Remove null bytes
    value = value.replace("\x00", "")
    # Trim whitespace
    value = value.strip()
    # Limit length
    if len(value) > 10000:
        value = value[:10000]
    return value


def sanitize_html(value: str) -> str:
    """Sanitize HTML input"""
    # Remove script tags
    value = re.sub(
        r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL
    )
    # Remove event handlers
    value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)
    return value


# Global validator instance
request_validator = EnhancedRequestValidator()

# Register common sanitizers
request_validator.register_sanitizer(
    "email", lambda x: x.lower().strip() if isinstance(x, str) else x
)
request_validator.register_sanitizer("username", sanitize_string)
request_validator.register_sanitizer("name", sanitize_string)
request_validator.register_sanitizer("description", sanitize_html)


class EnhancedRequestValidationMiddleware(BaseHTTPMiddleware):
    """Enhanced request validation middleware"""

    def __init__(
        self, app, enable_validation: bool = True, enable_sanitization: bool = True
    ):
        super().__init__(app)
        self.enable_validation = enable_validation
        self.enable_sanitization = enable_sanitization
        self.validator = request_validator

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with validation"""
        # Skip validation for certain paths (including auth to prevent hangs)
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths or request.url.path.startswith("/api/auth"):
            return await call_next(request)

        # Only validate POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            # Read body with timeout to prevent hangs
            try:
                body = await asyncio.wait_for(
                    request.body(),
                    timeout=2.0,  # 2 second timeout for body reading
                )
            except TimeoutError:
                logger.warning(f"Request body read timeout for {request.url.path}")
                # Continue without validation if body read times out
                return await call_next(request)

            if body:
                try:
                    data = json.loads(body.decode())

                    # Sanitize
                    if self.enable_sanitization:
                        data = self.validator.sanitize(data)

                    # Validate
                    if self.enable_validation:
                        endpoint = request.url.path
                        is_valid, errors = self.validator.validate(endpoint, data)

                        if not is_valid:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"validation_errors": errors},
                            )

                    # Replace request body with sanitized data
                    request._body = json.dumps(data).encode()

                except json.JSONDecodeError:
                    # Invalid JSON, let FastAPI handle it
                    pass
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Validation error: {e}", exc_info=True)

        return await call_next(request)


from collections.abc import Callable
