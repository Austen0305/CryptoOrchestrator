"""
API Versioning Middleware
Handles API versioning via headers and URL paths with deprecation warnings
"""

import logging
from datetime import date, datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning with deprecation support"""

    DEFAULT_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1", "v2"]

    # Version metadata
    VERSION_INFO = {
        "v1": {
            "status": "stable",
            "deprecated": False,
            "deprecation_date": None,
            "sunset_date": None,
            "migration_guide": "https://docs.cryptoorchestrator.com/api/migration/v1-to-v2",
        },
        "v2": {
            "status": "beta",
            "deprecated": False,
            "deprecation_date": None,
            "sunset_date": None,
            "migration_guide": None,
        },
    }

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Extract version from header or URL
        version = self._extract_version(request)

        # Store version in request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers
        response.headers["X-API-Version"] = version
        response.headers["X-Supported-Versions"] = ",".join(self.SUPPORTED_VERSIONS)

        # Add deprecation warnings if applicable
        version_info = self.VERSION_INFO.get(version, {})
        if version_info.get("deprecated", False):
            response.headers["X-API-Deprecated"] = "true"
            if version_info.get("deprecation_date"):
                response.headers["X-API-Deprecation-Date"] = str(
                    version_info["deprecation_date"]
                )
            if version_info.get("sunset_date"):
                response.headers["X-API-Sunset-Date"] = str(version_info["sunset_date"])
            if version_info.get("migration_guide"):
                response.headers["X-API-Migration-Guide"] = version_info[
                    "migration_guide"
                ]

        # Check if version is sunset (return 410 Gone)
        if version_info.get("sunset_date"):
            sunset_date = version_info["sunset_date"]
            if isinstance(sunset_date, str):
                sunset_date = datetime.fromisoformat(sunset_date).date()
            if isinstance(sunset_date, date) and sunset_date <= date.today():
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=410,
                    detail=f"API version {version} has been sunset. Please migrate to a supported version.",
                    headers={
                        "X-API-Sunset": "true",
                        "X-API-Migration-Guide": version_info.get(
                            "migration_guide", ""
                        ),
                    },
                )

        return response

    def _extract_version(self, request: Request) -> str:
        """Extract API version from request"""
        # Check URL path: /api/v2/...
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3:
            # Check for /api/v1/ or /api/v2/
            if path_parts[1] == "api" and path_parts[2] in self.SUPPORTED_VERSIONS:
                return path_parts[2]

        # Check Accept header: application/vnd.api+json;version=v2
        accept_header = request.headers.get("Accept", "")
        if "version=" in accept_header:
            for part in accept_header.split(";"):
                if "version=" in part:
                    version = part.split("=")[1].strip()
                    # Normalize version (v2, 2.0, 2 -> v2)
                    version = self._normalize_version(version)
                    if version in self.SUPPORTED_VERSIONS:
                        return version

        # Check X-API-Version header
        version_header = request.headers.get("X-API-Version", "")
        if version_header:
            version = self._normalize_version(version_header)
            if version in self.SUPPORTED_VERSIONS:
                return version

        # Default version
        return self.DEFAULT_VERSION

    def _normalize_version(self, version: str) -> str:
        """Normalize version string to v1, v2, etc."""
        version = version.strip().lower()
        # Remove 'v' prefix if present, then add it back
        if version.startswith("v"):
            version = version[1:]
        # Handle version numbers like "2.0" -> "2"
        if "." in version:
            version = version.split(".")[0]
        return f"v{version}"

    @classmethod
    def deprecate_version(cls, version: str, deprecation_date: str, sunset_date: str):
        """Mark a version as deprecated"""
        if version in cls.VERSION_INFO:
            cls.VERSION_INFO[version]["deprecated"] = True
            cls.VERSION_INFO[version]["deprecation_date"] = deprecation_date
            cls.VERSION_INFO[version]["sunset_date"] = sunset_date
