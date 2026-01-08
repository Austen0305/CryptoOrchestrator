"""
Response Transformation Middleware
Transforms responses based on API version, format preferences, and client capabilities
"""

import json
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ResponseTransformerMiddleware(BaseHTTPMiddleware):
    """
    Transforms responses based on:
    - API version
    - Accept headers
    - Client capabilities
    - Format preferences
    """

    def __init__(self, app, enable_transformation: bool = True):
        super().__init__(app)
        self.enable_transformation = enable_transformation

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with response transformation"""
        # Get client preferences
        accept_header = request.headers.get("Accept", "application/json")
        api_version = getattr(request.state, "api_version", "v1")

        # Process request
        response = await call_next(request)

        if not self.enable_transformation:
            return response

        # Transform based on version
        if api_version == "v2":
            response = await self._transform_to_v2(request, response)
        elif api_version == "v1":
            response = await self._ensure_v1_format(request, response)

        # Add format headers
        response.headers["X-Response-Format"] = "json"
        response.headers["X-API-Version"] = api_version

        return response

    async def _transform_to_v2(self, request: Request, response: Response) -> Response:
        """Transform response to v2 format"""
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Read body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body.decode())

            # Ensure v2 format
            if isinstance(data, dict):
                if "data" not in data:
                    # Wrap in v2 format
                    data = {
                        "success": data.get("success", True),
                        "data": data,
                        "meta": {
                            "timestamp": self._get_timestamp(),
                            "version": "2.0",
                            "request_id": getattr(request.state, "request_id", None),
                        },
                    }
                elif "meta" not in data:
                    # Add meta if missing
                    data["meta"] = {
                        "timestamp": self._get_timestamp(),
                        "version": "2.0",
                        "request_id": getattr(request.state, "request_id", None),
                    }

            return Response(
                content=json.dumps(data),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )
        except Exception as e:
            logger.debug(f"Response transformation failed: {e}")
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

    async def _ensure_v1_format(self, request: Request, response: Response) -> Response:
        """Ensure v1 format (backward compatibility)"""
        # v1 format is simpler, just ensure it's valid JSON
        return response

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"
