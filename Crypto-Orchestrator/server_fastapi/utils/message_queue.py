"""
Message Queue Abstraction Layer
Provides unified interface for different message queue backends (Celery, Redis, RabbitMQ)
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class QueueBackend(str, Enum):
    """Message queue backend types"""
    CELERY = "celery"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    IN_MEMORY = "in_memory"


@dataclass
class QueueMessage:
    """Queue message"""
    id: str
    task: str
    payload: Dict[str, Any]
    priority: int = 5  # 1-10, higher is more important
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = None
    scheduled_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class MessageQueue:
    """
    Unified message queue interface
    
    Supports:
    - Celery (production)
    - Redis (simple queues)
    - RabbitMQ (advanced routing)
    - In-memory (testing)
    """

    def __init__(self, backend: QueueBackend = QueueBackend.CELERY):
        self.backend = backend
        self._handlers: Dict[str, Callable] = {}
        self._in_memory_queue: List[QueueMessage] = []
        self._running = False

    async def enqueue(
        self,
        task: str,
        payload: Dict[str, Any],
        priority: int = 5,
        delay: Optional[timedelta] = None,
        max_retries: int = 3,
    ) -> str:
        """Enqueue a task"""
        message_id = f"{task}:{datetime.utcnow().timestamp()}"

        if self.backend == QueueBackend.CELERY:
            return await self._enqueue_celery(task, payload, delay, max_retries)
        elif self.backend == QueueBackend.REDIS:
            return await self._enqueue_redis(task, payload, priority, delay)
        elif self.backend == QueueBackend.IN_MEMORY:
            return await self._enqueue_in_memory(task, payload, priority, delay)

        raise ValueError(f"Unsupported backend: {self.backend}")

    async def _enqueue_celery(
        self,
        task: str,
        payload: Dict[str, Any],
        delay: Optional[timedelta],
        max_retries: int,
    ) -> str:
        """Enqueue using Celery"""
        try:
            from ..celery_app import celery_app

            # Get task function
            celery_task = celery_app.tasks.get(task)
            if not celery_task:
                # Try to import task
                try:
                    celery_task = celery_app.tasks[f"server_fastapi.{task}"]
                except KeyError:
                    raise ValueError(f"Celery task not found: {task}")

            # Apply task
            if delay:
                result = celery_task.apply_async(
                    args=[payload],
                    countdown=delay.total_seconds(),
                    max_retries=max_retries,
                )
            else:
                result = celery_task.apply_async(
                    args=[payload],
                    max_retries=max_retries,
                )

            return result.id
        except ImportError:
            logger.warning("Celery not available, falling back to in-memory")
            return await self._enqueue_in_memory(task, payload, 5, delay)

    async def _enqueue_redis(
        self,
        task: str,
        payload: Dict[str, Any],
        priority: int,
        delay: Optional[timedelta],
    ) -> str:
        """Enqueue using Redis"""
        try:
            import redis.asyncio as redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(redis_url)

            message = QueueMessage(
                id=f"{task}:{datetime.utcnow().timestamp()}",
                task=task,
                payload=payload,
                priority=priority,
                scheduled_at=datetime.utcnow() + delay if delay else None,
            )

            # Use sorted set for priority queue
            score = priority * 1000000 + datetime.utcnow().timestamp()
            await client.zadd("queue:tasks", {json.dumps(asdict(message)): score})

            await client.close()
            return message.id
        except ImportError:
            logger.warning("Redis not available, falling back to in-memory")
            return await self._enqueue_in_memory(task, payload, priority, delay)

    async def _enqueue_in_memory(
        self,
        task: str,
        payload: Dict[str, Any],
        priority: int,
        delay: Optional[timedelta],
    ) -> str:
        """Enqueue in memory (for testing)"""
        message = QueueMessage(
            id=f"{task}:{datetime.utcnow().timestamp()}",
            task=task,
            payload=payload,
            priority=priority,
            scheduled_at=datetime.utcnow() + delay if delay else None,
        )

        self._in_memory_queue.append(message)
        self._in_memory_queue.sort(key=lambda m: (-m.priority, m.created_at))

        # Process immediately if no delay
        if not delay:
            asyncio.create_task(self._process_in_memory_message(message))

        return message.id

    async def _process_in_memory_message(self, message: QueueMessage):
        """Process in-memory message"""
        handler = self._handlers.get(message.task)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message.payload)
                else:
                    handler(message.payload)
            except Exception as e:
                logger.error(f"Error processing message {message.id}: {e}", exc_info=True)
                message.retries += 1
                if message.retries < message.max_retries:
                    await asyncio.sleep(2 ** message.retries)  # Exponential backoff
                    await self._process_in_memory_message(message)

    def register_handler(self, task: str, handler: Callable):
        """Register a task handler"""
        self._handlers[task] = handler
        logger.debug(f"Handler registered for task: {task}")

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        if self.backend == QueueBackend.CELERY:
            try:
                from ..celery_app import celery_app
                result = celery_app.AsyncResult(task_id)
                return {
                    "id": task_id,
                    "status": result.state,
                    "result": result.result if result.ready() else None,
                }
            except Exception as e:
                logger.error(f"Error getting Celery task status: {e}")
                return {"id": task_id, "status": "unknown", "error": str(e)}

        # For other backends, return basic info
        return {"id": task_id, "status": "unknown"}

    async def cancel(self, task_id: str) -> bool:
        """Cancel a task"""
        if self.backend == QueueBackend.CELERY:
            try:
                from ..celery_app import celery_app
                celery_app.control.revoke(task_id, terminate=True)
                return True
            except Exception as e:
                logger.error(f"Error cancelling Celery task: {e}")
                return False

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "backend": self.backend.value,
            "handlers": len(self._handlers),
            "in_memory_queue_size": len(self._in_memory_queue),
        }


# Global message queue instance
# Determine backend from environment
backend_str = os.getenv("QUEUE_BACKEND", "celery").lower()
try:
    backend = QueueBackend(backend_str)
except ValueError:
    backend = QueueBackend.CELERY
    logger.warning(f"Unknown queue backend: {backend_str}, using Celery")

message_queue = MessageQueue(backend=backend)

