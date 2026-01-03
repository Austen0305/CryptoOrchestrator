"""
Compression Middleware
Compresses responses using gzip or brotli for better performance
"""

import gzip
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Optional brotli support (2026: make optional to avoid import errors)
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger.info("Brotli compression not available, using gzip only")


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to compress responses"""

    # Content types that should be compressed
    COMPRESSIBLE_TYPES = {
        "text/",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/xhtml+xml",
        "image/svg+xml",
    }

    # Minimum size to compress (bytes)
    MIN_SIZE = 1024  # 1KB

    def __init__(self, app: ASGIApp, minimum_size: int = 1024, compress_level: int = 6):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = compress_level

    def _should_compress(self, response: Response, body_size: int = 0, request_path: str = "") -> bool:
        """
        Check if response should be compressed (2026: check actual body size)
        
        Args:
            response: The response object
            body_size: Size of the response body in bytes (0 if not yet read)
            request_path: The request path (for inferring content type)
        """
        # Don't compress if already compressed
        if "Content-Encoding" in response.headers:
            return False

        # Check content type (be lenient - compress if type matches OR if path suggests JSON/API)
        content_type = response.headers.get("Content-Type", "").lower()
        path_suggests_json = any(
            ext in request_path.lower() 
            for ext in [".json", "/openapi", "/api/", "/docs"]
        )
        
        # If content type is set, check if it's compressible
        if content_type:
            if not any(ct in content_type for ct in self.COMPRESSIBLE_TYPES):
                return False
        # If content type is not set, allow compression if path suggests JSON/API
        elif not path_suggests_json:
            # No content type and path doesn't suggest JSON - be conservative
            return False

        # Check size - use body_size if provided, otherwise check Content-Length header
        if body_size > 0:
            if body_size < self.minimum_size:
                return False
        else:
            # Fallback to Content-Length header if body not read yet
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) < self.minimum_size:
                return False

        return True

    def _get_encoding(self, request: Request) -> Optional[str]:
        """Get preferred encoding from Accept-Encoding header"""
        accept_encoding = request.headers.get("Accept-Encoding", "").lower()

        # Prefer brotli if supported
        if "br" in accept_encoding:
            return "br"
        # Fall back to gzip
        elif "gzip" in accept_encoding:
            return "gzip"

        return None

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Get preferred encoding first (before reading body)
        encoding = self._get_encoding(request)
        if not encoding:
            logger.debug(f"Compression skipped: no Accept-Encoding header for {request.url.path}")
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        body_size = len(body)
        logger.debug(
            f"Compression check: path={request.url.path}, size={body_size}, "
            f"content_type={response.headers.get('Content-Type', 'not set')}, encoding={encoding}"
        )

        # Check if we should compress (now that we know body size)
        if not self._should_compress(response, body_size=body_size, request_path=str(request.url.path)):
            logger.debug(f"Compression skipped: should_compress=False for {request.url.path}")
            # Return original response if shouldn't compress
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("Content-Type"),
            )

        # Compress based on encoding
        if encoding == "br" and BROTLI_AVAILABLE and len(body) >= self.minimum_size:
            try:
                compressed = brotli.compress(body, quality=self.compress_level)
                if len(compressed) < len(body):
                    # Create new response with compressed body (2026 fix)
                    return Response(
                        content=compressed,
                        status_code=response.status_code,
                        headers={
                            **dict(response.headers),
                            "Content-Encoding": "br",
                            "Content-Length": str(len(compressed)),
                            "Vary": "Accept-Encoding",
                        },
                        media_type=response.headers.get("Content-Type"),
                    )
            except Exception as e:
                logger.warning(f"Brotli compression failed: {e}")
                # Fall through to gzip
        elif encoding == "br" and not BROTLI_AVAILABLE:
            # Brotli requested but not available, fall back to gzip
            encoding = "gzip"

        if encoding == "gzip" and len(body) >= self.minimum_size:
            try:
                compressed = gzip.compress(body, compresslevel=self.compress_level)
                if len(compressed) < len(body):
                    # Create new response with compressed body (2026 fix)
                    return Response(
                        content=compressed,
                        status_code=response.status_code,
                        headers={
                            **dict(response.headers),
                            "Content-Encoding": "gzip",
                            "Content-Length": str(len(compressed)),
                            "Vary": "Accept-Encoding",
                        },
                        media_type=response.headers.get("Content-Type"),
                    )
            except Exception as e:
                logger.warning(f"Gzip compression failed: {e}")

        # Return original response if compression wasn't applied
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("Content-Type"),
        )
