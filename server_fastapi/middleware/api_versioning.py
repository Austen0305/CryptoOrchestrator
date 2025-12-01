"""
API Versioning Middleware
Handles API versioning via headers and URL paths
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning"""
    
    DEFAULT_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1", "v2"]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Extract version from header or URL
        version = self._extract_version(request)
        
        # Store version in request state
        request.state.api_version = version
        
        # Add version header to response
        response = await call_next(request)
        response.headers["X-API-Version"] = version
        response.headers["X-Supported-Versions"] = ",".join(self.SUPPORTED_VERSIONS)
        
        return response
    
    def _extract_version(self, request: Request) -> str:
        """Extract API version from request"""
        # Check Accept header: application/vnd.api+json;version=v2
        accept_header = request.headers.get("Accept", "")
        if "version=" in accept_header:
            for part in accept_header.split(";"):
                if "version=" in part:
                    version = part.split("=")[1].strip()
                    if version in self.SUPPORTED_VERSIONS:
                        return version
        
        # Check X-API-Version header
        version_header = request.headers.get("X-API-Version", "")
        if version_header in self.SUPPORTED_VERSIONS:
            return version_header
        
        # Check URL path: /api/v2/...
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3 and path_parts[2] in self.SUPPORTED_VERSIONS:
            return path_parts[2]
        
        # Default version
        return self.DEFAULT_VERSION

