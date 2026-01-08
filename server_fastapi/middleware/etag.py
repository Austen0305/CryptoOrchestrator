"""
ETag Middleware
Implements HTTP ETag support for cache validation and conditional requests (304 Not Modified)
"""

import hashlib
import logging

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class ETagMiddleware(BaseHTTPMiddleware):
    """Middleware to add ETag headers and handle conditional requests"""

    def __init__(self, app: ASGIApp, weak: bool = False):
        """
        Initialize ETag middleware

        Args:
            app: ASGI application
            weak: If True, use weak ETags (W/"..."). Default: False (strong ETags)
        """
        super().__init__(app)
        self.weak = weak

    def _generate_etag(self, body: bytes) -> str:
        """
        Generate ETag from response body

        Args:
            body: Response body bytes

        Returns:
            ETag string (with or without W/ prefix for weak ETags)
        """
        # Generate MD5 hash of body
        etag_value = hashlib.md5(body).hexdigest()

        # Add weak prefix if needed
        if self.weak:
            return f'W/"{etag_value}"'
        return f'"{etag_value}"'

    def _should_add_etag(self, response: Response) -> bool:
        """
        Check if ETag should be added to response

        Args:
            response: Response object

        Returns:
            True if ETag should be added
        """
        # Don't add ETag if already present
        if "etag" in response.headers:
            return False

        # Only add ETag for successful GET/HEAD requests
        if response.status_code not in (200, 201, 204):
            return False

        # Don't add ETag if response has no body
        if not hasattr(response, "body") or not response.body:
            return False

        # Don't add ETag for streaming responses
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type or "multipart" in content_type:
            return False

        return True

    async def dispatch(self, request: Request, call_next):
        """
        Process request and add ETag if appropriate

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with ETag header if applicable
        """
        # Only process GET and HEAD requests
        if request.method not in ("GET", "HEAD"):
            response = await call_next(request)
            return response

        # Check for If-None-Match header (conditional request)
        if_none_match = request.headers.get("if-none-match")

        # Process request
        response = await call_next(request)

        # Generate ETag if appropriate
        if self._should_add_etag(response):
            # Get response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Generate ETag
            etag = self._generate_etag(body)

            # Handle conditional request (304 Not Modified)
            if if_none_match:
                # Remove quotes and weak prefix for comparison
                client_etags = [
                    tag.strip().strip('"').lstrip("W/").strip('"')
                    for tag in if_none_match.split(",")
                ]
                server_etag = etag.strip('"').lstrip("W/").strip('"')

                if server_etag in client_etags:
                    # Resource not modified - return 304
                    return Response(
                        status_code=status.HTTP_304_NOT_MODIFIED,
                        headers={
                            "ETag": etag,
                            "Cache-Control": response.headers.get(
                                "cache-control", "public, max-age=300"
                            ),
                        },
                    )

            # Add ETag header
            response.headers["ETag"] = etag

            # Restore body (create new response with body)
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response
