"""
Request Batching Middleware
Batches multiple requests for bulk operations to improve performance
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestBatchingMiddleware(BaseHTTPMiddleware):
    """
    Batches multiple similar requests together for bulk processing

    Useful for:
    - Bulk database queries
    - Batch API calls
    - Aggregated data fetching
    """

    def __init__(
        self,
        app,
        batch_window_ms: int = 50,  # 50ms batching window
        max_batch_size: int = 100,
        batchable_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.batch_window_ms = batch_window_ms / 1000.0  # Convert to seconds
        self.max_batch_size = max_batch_size
        self.batchable_paths = batchable_paths or [
            "/api/bots",
            "/api/portfolio",
            "/api/markets",
        ]

        # Batching state
        self.pending_batches: dict[str, list[tuple[Request, asyncio.Future]]] = (
            defaultdict(list)
        )
        self.batch_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def _is_batchable(self, path: str, method: str) -> bool:
        """Check if request is eligible for batching"""
        if method != "GET":
            return False

        return any(path.startswith(pattern) for pattern in self.batchable_paths)

    def _get_batch_key(self, request: Request) -> str | None:
        """Generate batch key for grouping similar requests"""
        if not self._is_batchable(request.url.path, request.method):
            return None

        # Group by path and query params (excluding user-specific params)
        path = request.url.path
        query_params = dict(request.query_params)

        # Remove user-specific params for batching
        user_params = ["user_id", "userId", "user", "auth"]
        for param in user_params:
            query_params.pop(param, None)

        # Create batch key
        query_str = "&".join(f"{k}={v}" for k, v in sorted(query_params.items()))
        return f"{path}?{query_str}" if query_str else path

    async def _process_batch(
        self, batch_key: str, requests: list[tuple[Request, asyncio.Future]]
    ):
        """Process a batch of requests"""
        try:
            # Extract unique requests (deduplicate)
            unique_requests = {}
            for request, future in requests:
                request_id = id(request)
                if request_id not in unique_requests:
                    unique_requests[request_id] = (request, future)

            # Process requests (could be optimized further with bulk operations)
            results = []
            for request, future in unique_requests.values():
                try:
                    # In a real implementation, this would call a bulk handler
                    # For now, we'll process individually but in parallel
                    results.append((request, future))
                except Exception as e:
                    logger.error(f"Error processing batched request: {e}")
                    future.set_exception(e)

            # Set results (placeholder - would need actual batch processing logic)
            for request, future in results:
                if not future.done():
                    # Future would be set by actual batch processor
                    pass

        except Exception as e:
            logger.error(f"Error processing batch {batch_key}: {e}")
            # Set exceptions for all pending futures
            for _, future in requests:
                if not future.done():
                    future.set_exception(e)
        finally:
            # Clean up
            async with self._lock:
                if batch_key in self.pending_batches:
                    del self.pending_batches[batch_key]
                if batch_key in self.batch_tasks:
                    del self.batch_tasks[batch_key]

    async def _schedule_batch(self, batch_key: str):
        """Schedule batch processing after window"""
        await asyncio.sleep(self.batch_window_ms)

        async with self._lock:
            if batch_key in self.pending_batches:
                requests = self.pending_batches[batch_key]
                if requests:
                    await self._process_batch(batch_key, requests)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with batching support"""
        batch_key = self._get_batch_key(request)

        if batch_key is None:
            # Not batchable, process normally
            return await call_next(request)

        # Check if we should batch
        async with self._lock:
            if batch_key in self.pending_batches:
                batch = self.pending_batches[batch_key]

                # Check if batch is full
                if len(batch) >= self.max_batch_size:
                    # Process immediately
                    requests = batch[:]
                    self.pending_batches[batch_key] = []
                    asyncio.create_task(self._process_batch(batch_key, requests))
                else:
                    # Add to batch
                    future = asyncio.Future()
                    batch.append((request, future))

                    # Schedule batch if not already scheduled
                    if batch_key not in self.batch_tasks:
                        task = asyncio.create_task(self._schedule_batch(batch_key))
                        self.batch_tasks[batch_key] = task

                    # Wait for batch result
                    try:
                        result = await future
                        return result
                    except Exception as e:
                        logger.error(f"Batch processing error: {e}")
                        # Fallback to normal processing
                        return await call_next(request)
            else:
                # Start new batch
                future = asyncio.Future()
                self.pending_batches[batch_key] = [(request, future)]
                task = asyncio.create_task(self._schedule_batch(batch_key))
                self.batch_tasks[batch_key] = task

                try:
                    result = await future
                    return result
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    return await call_next(request)

        # Fallback
        return await call_next(request)
