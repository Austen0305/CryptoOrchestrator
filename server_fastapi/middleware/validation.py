from __future__ import annotations

import html
import re
from typing import Any

import bleach  # type: ignore
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, field_validator


class SanitizedBaseModel(BaseModel):
    """Base model with built-in input sanitization"""

    model_config = ConfigDict(validate_assignment=True, strict=True)

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_string_inputs(cls, v: Any) -> Any:
        """
        Sanitize string inputs; if lists/dicts are provided,
        sanitize their string contents recursively.
        """
        if isinstance(v, str):
            return sanitize_input(v)
        if isinstance(v, list):
            return [
                sanitize_input(item) if isinstance(item, str) else item for item in v
            ]
        if isinstance(v, dict):
            return {
                k: sanitize_input(val) if isinstance(val, str) else val
                for k, val in v.items()
            }
        return v


def sanitize_input(input_str: Any) -> str:
    """
    Sanitize input string to prevent XSS and other injection attacks
    """
    if not isinstance(input_str, str):
        return str(input_str)

    # HTML escape
    sanitized = html.escape(input_str)

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'`]', "", sanitized)

    # Limit length to prevent DoS
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]

    return sanitized


def sanitize_html_content(content: str) -> str:
    """
    Sanitize HTML content while preserving safe tags
    """
    allowed_tags = ["p", "br", "strong", "em", "u", "h1", "h2", "h3"]
    allowed_attributes: dict[str, Any] = {}

    return str(
        bleach.clean(
            content, tags=allowed_tags, attributes=allowed_attributes, strip=True
        )
    )


def validate_email_format(email: str) -> bool:
    """
    Validate email format with additional security checks
    """
    if not email or len(email) > 254:
        return False

    # Basic regex check
    email_regex = r"^[a-zA-Z\d._%+-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        return False

    # Additional security checks
    return not (".." in email or email.startswith(".") or email.endswith("."))


def validate_password_strength(password: str) -> dict[str, Any]:
    """
    Validate password strength according to security checklist requirements.
    Requirements:
    - Minimum 12 characters (security checklist requirement)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    - No spaces
    """
    if not password:
        return {
            "valid": False,
            "message": "Password is required",
        }

    # Security checklist requirement: minimum 12 characters
    if len(password) < 12:
        return {
            "valid": False,
            "message": "Password must be at least 12 characters long",
        }

    checks = {
        "length": len(password) >= 12,  # Updated to 12 characters
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "numbers": bool(re.search(r"\d", password)),
        "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        "no_spaces": " " not in password,
    }

    score = sum(checks.values())

    if score < 4:
        return {
            "valid": False,
            "message": (
                "Password must contain uppercase, lowercase, numbers, "
                "and special characters"
            ),
        }
    if not checks["no_spaces"]:
        return {"valid": False, "message": "Password cannot contain spaces"}

    return {"valid": True, "strength": "strong" if score >= 5 else "medium"}


def validate_input_length(value: Any, max_length: int = 1000) -> bool:
    """
    Validate input length to prevent DoS attacks
    """
    if isinstance(value, str):
        return len(value) <= max_length
    elif isinstance(value, (list, dict)):
        return len(str(value)) <= max_length
    return True


class InputValidationMiddleware:
    """Middleware for comprehensive input validation"""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create a custom receive function that validates input
        async def validated_receive() -> dict[str, Any]:
            message = await receive()
            if message["type"] == "http.request":
                # Validate query parameters
                query_string = scope.get("query_string", b"").decode()
                if len(query_string) > 2048:  # Prevent query string DoS
                    raise HTTPException(status_code=400, detail="Query string too long")

                # Validate headers
                headers = dict(scope.get("headers", []))
                for header_name, header_value in headers.items():
                    header_name = header_name.decode().lower()
                    header_value = header_value.decode()
                    if len(header_value) > 4096:  # Prevent header DoS
                        raise HTTPException(
                            status_code=400, detail=f"Header {header_name} too long"
                        )

            return message  # type: ignore

        await self.app(scope, validated_receive, send)
