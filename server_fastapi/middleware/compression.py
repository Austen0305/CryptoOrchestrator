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
            logger.debug(f"Already compressed, skipping: {request_path}")
            return False

        # Check content type (be lenient - compress if type matches OR if path suggests JSON/API)
        content_type = response.headers.get("Content-Type", "").lower()
        path_suggests_json = any(
            ext in request_path.lower() 
            for ext in [".json", "/openapi", "/api/", "/docs"]
        )
        
        logger.debug(f"Content type check: type='{content_type}', path='{request_path}', suggests_json={path_suggests_json}")
        
        # If content type is set, check if it's compressible
        if content_type:
            is_compressible = any(ct in content_type for ct in self.COMPRESSIBLE_TYPES)
            if not is_compressible:
                logger.debug(f"Content type '{content_type}' not compressible")
                return False
        # If content type is not set, allow compression if path suggests JSON/API
        elif not path_suggests_json:
            # No content type and path doesn't suggest JSON - be conservative
            logger.debug(f"No content type and path doesn't suggest JSON, skipping: {request_path}")
            return False

        # Check size - use body_size if provided, otherwise check Content-Length header
        if body_size > 0:
            if body_size < self.minimum_size:
                logger.debug(f"Body size {body_size} < minimum {self.minimum_size}, skipping")
                return False
        else:
            # Fallback to Content-Length header if body not read yet
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) < self.minimum_size:
                logger.debug(f"Content-Length {content_length} < minimum {self.minimum_size}, skipping")
                return False

        logger.debug(f"All checks passed, will compress: {request_path}")
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
        try:
            logger.info(f"Compression middleware called for {request.url.path}")
            response: Response = await call_next(request)
            logger.info(f"Got response for {request.url.path}, status={response.status_code}")

            # Get preferred encoding first (before reading body)
            encoding = self._get_encoding(request)
            accept_encoding = request.headers.get("Accept-Encoding", "not set")
            logger.info(f"Encoding check for {request.url.path}: encoding={encoding}, Accept-Encoding={accept_encoding}")
            if not encoding:
                logger.info(f"Compression skipped: no Accept-Encoding header for {request.url.path}")
                return response

            # Read response body
            body = b""
            try:
                async for chunk in response.body_iterator:
                    body += chunk
            except Exception as e:
                logger.warning(f"Error reading response body for compression: {e}", exc_info=True)
                return response

            body_size = len(body)
            logger.info(
                f"Compression middleware active: path={request.url.path}, size={body_size}, "
                f"content_type={response.headers.get('Content-Type', 'not set')}, encoding={encoding}"
            )

            # Check if we should compress (now that we know body size)
            should_compress = self._should_compress(response, body_size=body_size, request_path=str(request.url.path))
            logger.info(f"Should compress: {should_compress} for {request.url.path}")
            
            if not should_compress:
                logger.debug(f"Compression skipped: should_compress=False for {request.url.path}")
                # Return original response if shouldn't compress
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("Content-Type"),
                )
        except Exception as e:
            logger.error(f"Error in compression middleware: {e}", exc_info=True)
            # Return original response on error - re-call to get response
            try:
                response = await call_next(request)
                return response
            except Exception as e2:
                logger.error(f"Failed to get response after compression error: {e2}", exc_info=True)
                # Last resort - return error response
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error in compression middleware"}
                )

        # Compress based on encoding
        logger.info(f"Compression decision: encoding={encoding}, body_size={len(body)}, minimum_size={self.minimum_size}, BROTLI_AVAILABLE={BROTLI_AVAILABLE}")
        
        if encoding == "br" and BROTLI_AVAILABLE and len(body) >= self.minimum_size:
            try:
                logger.info(f"Attempting Brotli compression for {request.url.path}")
                compressed = brotli.compress(body, quality=self.compress_level)
                if len(compressed) < len(body):
                    logger.info(f"Brotli compression successful: {len(body)} -> {len(compressed)} bytes ({len(compressed)/len(body)*100:.1f}%)")
                    # Build new headers - remove Content-Length and Transfer-Encoding (Starlette will set them)
                    new_headers = {}
                    for key, value in response.headers.items():
                        # Skip headers that Starlette manages automatically
                        if key.lower() not in ("content-length", "transfer-encoding", "content-encoding"):
                            new_headers[key] = value
                    
                    # Add compression headers
                    new_headers["Content-Encoding"] = "br"
                    new_headers["Vary"] = "Accept-Encoding"
                    
                    # Create new response with compressed body (2026 fix)
                    return Response(
                        content=compressed,
                        status_code=response.status_code,
                        headers=new_headers,
                        media_type=response.headers.get("Content-Type") or "application/json",
                    )
                else:
                    logger.warning(f"Brotli compression didn't reduce size: {len(body)} -> {len(compressed)} bytes")
            except Exception as e:
                logger.warning(f"Brotli compression failed: {e}", exc_info=True)
                # Fall through to gzip
        elif encoding == "br" and not BROTLI_AVAILABLE:
            # Brotli requested but not available, fall back to gzip
            logger.debug("Brotli not available, falling back to gzip")
            encoding = "gzip"

        if encoding == "gzip" and len(body) >= self.minimum_size:
            try:
                logger.info(f"Attempting Gzip compression for {request.url.path} (size: {len(body)} bytes)")
                compressed = gzip.compress(body, compresslevel=self.compress_level)
                compressed_size = len(compressed)
                original_size = len(body)
                if compressed_size < original_size:
                    ratio = compressed_size / original_size * 100
                    logger.info(f"Gzip compression successful: {original_size} -> {compressed_size} bytes ({ratio:.1f}%)")
                    # Create new response with compressed body (2026 fix)
                    # Build new headers - remove Content-Length and Transfer-Encoding (Starlette will set them)
                    new_headers = {}
                    for key, value in response.headers.items():
                        # Skip headers that Starlette manages automatically
                        if key.lower() not in ("content-length", "transfer-encoding", "content-encoding"):
                            new_headers[key] = value
                    
                    # Add compression headers
                    new_headers["Content-Encoding"] = "gzip"
                    new_headers["Vary"] = "Accept-Encoding"
                    
                    compressed_response = Response(
                        content=compressed,
                        status_code=response.status_code,
                        headers=new_headers,
                        media_type=response.headers.get("Content-Type") or "application/json",
                    )
                    logger.info(f"Returning compressed response with Content-Encoding: gzip")
                    return compressed_response
                else:
                    logger.warning(f"Gzip compression didn't reduce size: {original_size} -> {compressed_size} bytes, returning original")
            except Exception as e:
                logger.error(f"Gzip compression failed: {e}", exc_info=True)

        # Return original response if compression wasn't applied
        logger.debug(f"Returning uncompressed response for {request.url.path} (encoding={encoding}, body_size={len(body)})")
        # Clean headers for uncompressed response too
        new_headers = {}
        for key, value in response.headers.items():
            # Skip headers that Starlette manages automatically
            if key.lower() not in ("content-length", "transfer-encoding"):
                new_headers[key] = value
        
        return Response(
            content=body,
            status_code=response.status_code,
            headers=new_headers,
            media_type=response.headers.get("Content-Type") or "application/json",
        )
