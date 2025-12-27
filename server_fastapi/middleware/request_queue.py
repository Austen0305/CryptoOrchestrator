"""
Request Queue Middleware
Implements request queuing for high-load scenarios with priority support
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Callable
from enum import IntEnum
from collections import deque
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestPriority(IntEnum):
    """Request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class RequestQueueMiddleware(BaseHTTPMiddleware):
    """
    Queues requests when system is under high load
    
    Features:
    - Priority-based queuing
    - Max queue size
    - Queue timeout
    - Load-based activation
    """

    def __init__(
        self,
        app,
        max_queue_size: int = 1000,
        queue_timeout: float = 30.0,
        max_concurrent: int = 100,
        enable_load_based: bool = True,
        load_threshold: float = 0.8,  # Activate queue at 80% capacity
    ):
        super().__init__(app)
        self.max_queue_size = max_queue_size
        self.queue_timeout = queue_timeout
        self.max_concurrent = max_concurrent
        self.enable_load_based = enable_load_based
        self.load_threshold = load_threshold
        
        # Queue state
        self.queue: deque = deque()
        self.active_requests = 0
        self.queue_processor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "queued": 0,
            "processed": 0,
            "timeouts": 0,
            "rejected": 0,
        }

    def _get_priority(self, request: Request) -> RequestPriority:
        """Determine request priority"""
        path = request.url.path
        
        # Critical paths
        if path in ["/health", "/healthz", "/api/health"]:
            return RequestPriority.CRITICAL
        
        # High priority paths
        if path.startswith(("/api/auth", "/api/trades", "/api/orders")):
            return RequestPriority.HIGH
        
        # Low priority paths (analytics, logs, etc.)
        if path.startswith(("/api/analytics", "/api/logs", "/api/metrics")):
            return RequestPriority.LOW
        
        return RequestPriority.NORMAL

    def _should_queue(self) -> bool:
        """Determine if requests should be queued"""
        if not self.enable_load_based:
            return False
        
        load_ratio = self.active_requests / self.max_concurrent
        return load_ratio >= self.load_threshold

    async def _process_queue(self):
        """Process queued requests"""
        while True:
            try:
                await asyncio.sleep(0.1)  # Check queue every 100ms
                
                async with self._lock:
                    if not self.queue or self.active_requests >= self.max_concurrent:
                        continue
                    
                    # Get highest priority request
                    if self.queue:
                        # Sort by priority (highest first)
                        self.queue = deque(
                            sorted(self.queue, key=lambda x: x[0], reverse=True)
                        )
                        priority, request, future, start_time = self.queue.popleft()
                        
                        # Check timeout
                        if time.time() - start_time > self.queue_timeout:
                            self.stats["timeouts"] += 1
                            if not future.done():
                                future.set_exception(
                                    HTTPException(
                                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                        detail="Request timeout in queue"
                                    )
                                )
                            continue
                        
                        # Process request
                        self.active_requests += 1
                        asyncio.create_task(
                            self._handle_queued_request(request, future)
                        )
                        
            except Exception as e:
                logger.error(f"Error processing queue: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _handle_queued_request(self, request: Request, future: asyncio.Future):
        """Handle a queued request"""
        try:
            # This would call the actual handler
            # For now, we'll need to integrate with the app
            # In a real implementation, this would use call_next
            pass
        except Exception as e:
            if not future.done():
                future.set_exception(e)
        finally:
            async with self._lock:
                self.active_requests -= 1
                self.stats["processed"] += 1

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with queuing support"""
        # Check if we should queue
        should_queue = self._should_queue()
        
        if not should_queue:
            # Normal processing
            async with self._lock:
                self.active_requests += 1
            
            try:
                return await call_next(request)
            finally:
                async with self._lock:
                    self.active_requests -= 1
        
        # Queue the request
        priority = self._get_priority(request)
        
        async with self._lock:
            # Check queue size
            if len(self.queue) >= self.max_queue_size:
                self.stats["rejected"] += 1
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Request queue is full"
                )
            
            # Add to queue
            future = asyncio.Future()
            self.queue.append((priority, request, future, time.time()))
            self.stats["queued"] += 1
            
            # Start queue processor if not running
            if self.queue_processor_task is None or self.queue_processor_task.done():
                self.queue_processor_task = asyncio.create_task(self._process_queue())
        
        # Wait for queue processing
        try:
            result = await asyncio.wait_for(future, timeout=self.queue_timeout)
            return result
        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request timeout in queue"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self.stats,
            "queue_size": len(self.queue),
            "active_requests": self.active_requests,
            "queue_utilization": len(self.queue) / self.max_queue_size if self.max_queue_size > 0 else 0,
        }

