"""
Optimized Response Compression Middleware
Intelligent compression with content-type detection and size optimization
"""

import gzip
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class OptimizedCompressionMiddleware(BaseHTTPMiddleware):
    """
    Optimized compression with:
    - Content-type detection
    - Size-based compression
    - Compression level optimization
    - Already-compressed detection
    """

    # Content types that benefit from compression
    COMPRESSIBLE_TYPES = {
        "application/json",
        "application/javascript",
        "application/xml",
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
    }

    # Content types that are already compressed
    ALREADY_COMPRESSED = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "video/mp4",
        "application/zip",
        "application/gzip",
    }

    def __init__(
        self,
        app,
        minimum_size: int = 1024,  # 1KB minimum
        compress_level: int = 6,  # Balanced compression
        enable_for_types: set | None = None,
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = compress_level
        self.compressible_types = enable_for_types or self.COMPRESSIBLE_TYPES

        self.stats = {
            "compressed": 0,
            "skipped_size": 0,
            "skipped_type": 0,
            "bytes_saved": 0,
        }

    def _should_compress(self, response: Response) -> bool:
        """Determine if response should be compressed"""
        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()

        if content_type in self.ALREADY_COMPRESSED:
            self.stats["skipped_type"] += 1
            return False

        if content_type not in self.compressible_types:
            self.stats["skipped_type"] += 1
            return False

        # Check if already compressed
        if "content-encoding" in response.headers:
            return False

        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with optimized compression"""
        # Check Accept-Encoding header
        accept_encoding = request.headers.get("accept-encoding", "")
        supports_gzip = "gzip" in accept_encoding

        if not supports_gzip:
            return await call_next(request)

        response = await call_next(request)

        # Check if should compress
        if not self._should_compress(response):
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Check minimum size
        if len(body) < self.minimum_size:
            self.stats["skipped_size"] += 1
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        # Compress
        try:
            compressed = gzip.compress(body, compresslevel=self.compress_level)

            # Only use if compression is beneficial (>20% reduction)
            if len(compressed) < len(body) * 0.8:
                self.stats["compressed"] += 1
                self.stats["bytes_saved"] += len(body) - len(compressed)

                headers = dict(response.headers)
                headers["Content-Encoding"] = "gzip"
                headers["Content-Length"] = str(len(compressed))
                headers["Vary"] = "Accept-Encoding"

                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers=headers,
                )
        except Exception as e:
            logger.debug(f"Compression failed: {e}")

        # Return original if compression failed or not beneficial
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    def get_stats(self) -> dict:
        """Get compression statistics"""
        return self.stats.copy()
