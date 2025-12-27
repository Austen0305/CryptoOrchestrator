"""
Enhanced API Versioning Middleware
Advanced versioning with backward compatibility, transformation, and migration support
"""

import logging
from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)


class EnhancedAPIVersioningMiddleware(BaseHTTPMiddleware):
    """
    Enhanced API versioning with:
    - Backward compatibility transformations
    - Automatic response transformation
    - Version negotiation
    - Migration helpers
    - Version-specific features
    """

    DEFAULT_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1", "v2"]
    LATEST_VERSION = "v2"

    VERSION_INFO = {
        "v1": {
            "status": "stable",
            "deprecated": False,
            "deprecation_date": None,
            "sunset_date": None,
            "migration_guide": "https://docs.cryptoorchestrator.com/api/migration/v1-to-v2",
            "features": ["basic", "trading", "portfolio"],
        },
        "v2": {
            "status": "stable",
            "deprecated": False,
            "deprecation_date": None,
            "sunset_date": None,
            "migration_guide": None,
            "features": ["basic", "trading", "portfolio", "advanced", "analytics"],
        },
    }

    def __init__(self, app, enable_transformation: bool = True):
        super().__init__(app)
        self.enable_transformation = enable_transformation

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with enhanced versioning"""
        # Extract version
        version = self._extract_version(request)
        
        # Store in request state
        request.state.api_version = version
        request.state.version_info = self.VERSION_INFO.get(version, {})
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        response.headers["X-API-Version"] = version
        response.headers["X-Supported-Versions"] = ",".join(self.SUPPORTED_VERSIONS)
        response.headers["X-Latest-Version"] = self.LATEST_VERSION
        
        # Add deprecation warnings
        version_info = self.VERSION_INFO.get(version, {})
        if version_info.get("deprecated", False):
            response.headers["X-API-Deprecated"] = "true"
            if version_info.get("deprecation_date"):
                response.headers["X-API-Deprecation-Date"] = str(version_info["deprecation_date"])
            if version_info.get("sunset_date"):
                response.headers["X-API-Sunset-Date"] = str(version_info["sunset_date"])
            if version_info.get("migration_guide"):
                response.headers["X-API-Migration-Guide"] = version_info["migration_guide"]
        
        # Transform response if needed (v1 to v2 format)
        if self.enable_transformation and version == "v1":
            response = await self._transform_response(request, response)
        
        # Check sunset
        if version_info.get("sunset_date"):
            sunset_date = version_info["sunset_date"]
            if isinstance(sunset_date, str):
                sunset_date = datetime.fromisoformat(sunset_date).date()
            if isinstance(sunset_date, date) and sunset_date <= date.today():
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=410,
                    detail=f"API version {version} has been sunset",
                    headers={
                        "X-API-Sunset": "true",
                        "X-API-Migration-Guide": version_info.get("migration_guide", ""),
                    },
                )
        
        return response

    def _extract_version(self, request: Request) -> str:
        """Extract API version with multiple strategies"""
        # 1. URL path: /api/v2/...
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3:
            if path_parts[1] == "api" and path_parts[2] in self.SUPPORTED_VERSIONS:
                return path_parts[2]
        
        # 2. Accept header: application/vnd.api+json;version=v2
        accept_header = request.headers.get("Accept", "")
        if "version=" in accept_header:
            for part in accept_header.split(";"):
                if "version=" in part:
                    version = self._normalize_version(part.split("=")[1].strip())
                    if version in self.SUPPORTED_VERSIONS:
                        return version
        
        # 3. X-API-Version header
        version_header = request.headers.get("X-API-Version", "")
        if version_header:
            version = self._normalize_version(version_header)
            if version in self.SUPPORTED_VERSIONS:
                return version
        
        # 4. Default
        return self.DEFAULT_VERSION

    def _normalize_version(self, version: str) -> str:
        """Normalize version string"""
        version = version.strip().lower()
        if version.startswith("v"):
            version = version[1:]
        if "." in version:
            version = version.split(".")[0]
        return f"v{version}"

    async def _transform_response(self, request: Request, response: Response) -> Response:
        """Transform v1 response to v2 format for backward compatibility"""
        # Only transform JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response
        
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        try:
            data = json.loads(body.decode())
            
            # Transform to v2 format if needed
            if isinstance(data, dict) and "data" not in data:
                # Wrap in v2 format
                transformed = {
                    "success": data.get("success", True),
                    "data": data,
                    "meta": {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "version": "1.0",
                        "request_id": getattr(request.state, "request_id", None),
                    },
                }
                
                # Recreate response
                return Response(
                    content=json.dumps(transformed),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json",
                )
        except Exception as e:
            logger.debug(f"Response transformation failed: {e}")
        
        # Return original if transformation fails
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    @classmethod
    def deprecate_version(cls, version: str, deprecation_date: str, sunset_date: str):
        """Mark a version as deprecated"""
        if version in cls.VERSION_INFO:
            cls.VERSION_INFO[version]["deprecated"] = True
            cls.VERSION_INFO[version]["deprecation_date"] = deprecation_date
            cls.VERSION_INFO[version]["sunset_date"] = sunset_date
            logger.info(f"API version {version} marked as deprecated")

