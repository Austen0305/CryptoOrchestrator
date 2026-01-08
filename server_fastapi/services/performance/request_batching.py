"""
Request Batching Service
Implements JSON-RPC style request batching for reduced latency
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class BatchRequest:
    """Represents a single request in a batch"""

    def __init__(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        id: str | None = None,
    ):
        self.method = method
        self.params = params or {}
        self.id = id or f"req_{datetime.utcnow().timestamp()}"
        self.result: Any | None = None
        self.error: dict[str, Any] | None = None


class RequestBatchingService:
    """
    Service for handling batched API requests

    Allows clients to send multiple API requests in a single HTTP request,
    reducing latency and overhead for high-frequency trading applications.

    Supports JSON-RPC 2.0 style batching.
    """

    def __init__(self):
        self.max_batch_size = 100
        self.max_batch_timeout = 5.0  # seconds
        self.registered_handlers: dict[str, callable] = {}

    def register_handler(self, method: str, handler: callable):
        """Register a handler for a batch method"""
        self.registered_handlers[method] = handler
        logger.info(f"Registered batch handler for method: {method}")

    async def process_batch(
        self,
        requests: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Process a batch of requests

        Args:
            requests: List of request dictionaries
            context: Optional context (e.g., current_user, db_session)

        Returns:
            List of response dictionaries
        """
        if len(requests) > self.max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Batch size exceeds maximum of {self.max_batch_size}",
            )

        # Parse requests
        batch_requests = []
        for req in requests:
            if not isinstance(req, dict):
                raise HTTPException(status_code=400, detail="Invalid request format")

            method = req.get("method")
            if not method:
                raise HTTPException(
                    status_code=400, detail="Missing 'method' in request"
                )

            batch_req = BatchRequest(
                method=method,
                params=req.get("params", {}),
                id=req.get("id"),
            )
            batch_requests.append(batch_req)

        # Process requests concurrently
        tasks = [self._process_single_request(req, context) for req in batch_requests]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build responses
        responses = []
        for i, result in enumerate(results):
            req = batch_requests[i]

            if isinstance(result, Exception):
                responses.append(
                    {
                        "jsonrpc": "2.0",
                        "id": req.id,
                        "error": {
                            "code": -32000,
                            "message": str(result),
                        },
                    }
                )
            else:
                responses.append(
                    {
                        "jsonrpc": "2.0",
                        "id": req.id,
                        "result": result,
                    }
                )

        return responses

    async def _process_single_request(
        self,
        request: BatchRequest,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Process a single request in the batch"""
        handler = self.registered_handlers.get(request.method)

        if not handler:
            raise ValueError(f"Unknown method: {request.method}")

        try:
            # Call handler with params and context
            if asyncio.iscoroutinefunction(handler):
                result = await handler(request.params, context)
            else:
                result = handler(request.params, context)

            return result
        except Exception as e:
            logger.error(
                f"Error processing batch request {request.method}: {e}", exc_info=True
            )
            raise


# Global instance
request_batching_service = RequestBatchingService()
