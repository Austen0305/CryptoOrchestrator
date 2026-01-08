"""
Request/Response Interceptor Middleware
Provides hooks for request/response transformation and inspection
"""

import logging
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestInterceptor:
    """
    Request/response interceptor

    Features:
    - Request preprocessing hooks
    - Response postprocessing hooks
    - Request/response transformation
    - Custom validation
    - Data enrichment
    """

    def __init__(self):
        self.request_hooks: list[Callable] = []
        self.response_hooks: list[Callable] = []
        self.transformers: dict[str, Callable] = {}

    def register_request_hook(self, hook: Callable):
        """Register request preprocessing hook"""
        self.request_hooks.append(hook)
        logger.debug("Request hook registered")

    def register_response_hook(self, hook: Callable):
        """Register response postprocessing hook"""
        self.response_hooks.append(hook)
        logger.debug("Response hook registered")

    def register_transformer(self, endpoint: str, transformer: Callable):
        """Register response transformer for endpoint"""
        self.transformers[endpoint] = transformer
        logger.debug(f"Response transformer registered for {endpoint}")

    async def process_request(self, request: Request) -> Request:
        """Process request through hooks"""
        for hook in self.request_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    request = await hook(request) or request
                else:
                    request = hook(request) or request
            except Exception as e:
                logger.error(f"Error in request hook: {e}")
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process response through hooks"""
        # Check for transformer
        transformer = self.transformers.get(request.url.path)
        if transformer:
            try:
                if asyncio.iscoroutinefunction(transformer):
                    response = await transformer(request, response) or response
                else:
                    response = transformer(request, response) or response
            except Exception as e:
                logger.error(f"Error in response transformer: {e}")

        # Process through hooks
        for hook in self.response_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    response = await hook(request, response) or response
                else:
                    response = hook(request, response) or response
            except Exception as e:
                logger.error(f"Error in response hook: {e}")

        return response


import asyncio


class RequestInterceptorMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response interception"""

    def __init__(self, app, interceptor: RequestInterceptor | None = None):
        super().__init__(app)
        self.interceptor = interceptor or RequestInterceptor()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with interception"""
        # Process request
        request = await self.interceptor.process_request(request)

        # Process request
        response = await call_next(request)

        # Process response
        response = await self.interceptor.process_response(request, response)

        return response


# Global interceptor instance
request_interceptor = RequestInterceptor()
