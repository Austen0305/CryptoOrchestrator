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

# Optional brotli support (2026: make optional to avoid import errors)
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.info("Brotli compression not available, using gzip only")

logger = logging.getLogger(__name__)


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

    def _should_compress(self, response: Response) -> bool:
        """Check if response should be compressed"""
        # Don't compress if already compressed
        if "Content-Encoding" in response.headers:
            return False

        # Check content type
        content_type = response.headers.get("Content-Type", "").lower()
        if not any(ct in content_type for ct in self.COMPRESSIBLE_TYPES):
            return False

        # Check content length
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

        # Check if we should compress
        if not self._should_compress(response):
            return response

        # Get preferred encoding
        encoding = self._get_encoding(request)
        if not encoding:
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Compress based on encoding
        if encoding == "br" and BROTLI_AVAILABLE and len(body) >= self.minimum_size:
            try:
                compressed = brotli.compress(body, quality=self.compress_level)
                if len(compressed) < len(body):
                    response.body = compressed
                    response.headers["Content-Encoding"] = "br"
                    response.headers["Content-Length"] = str(len(compressed))
                    response.headers["Vary"] = "Accept-Encoding"
                    return response
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
                    response.body = compressed
                    response.headers["Content-Encoding"] = "gzip"
                    response.headers["Content-Length"] = str(len(compressed))
                    response.headers["Vary"] = "Accept-Encoding"
            except Exception as e:
                logger.warning(f"Gzip compression failed: {e}")

        return response
