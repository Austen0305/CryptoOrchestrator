"""
Task Batching Utilities
Implements efficient batching of Celery tasks to reduce overhead and improve throughput.
"""

import asyncio
import logging
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskBatcher:
    """
    Batches multiple task calls into single executions to reduce overhead.
    """

    def __init__(self, batch_size: int = 100, batch_timeout_seconds: float = 5.0):
        """
        Initialize task batcher.

        Args:
            batch_size: Maximum number of items per batch
            batch_timeout_seconds: Maximum time to wait before flushing batch
        """
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.batches: dict[str, deque] = {}
        self.batch_timestamps: dict[str, datetime] = {}
        self.batch_callbacks: dict[str, Callable] = {}
        self.locks: dict[str, asyncio.Lock] = {}

    async def add_to_batch(
        self,
        batch_key: str,
        item: Any,
        batch_callback: Callable[[list[Any]], Any],
        force_flush: bool = False,
    ) -> Any:
        """
        Add item to batch and execute callback when batch is full or timeout reached.

        Args:
            batch_key: Unique key for this batch type
            item: Item to add to batch
            batch_callback: Callback function that processes the batch
            force_flush: Force immediate batch execution

        Returns:
            Result from batch callback
        """
        if batch_key not in self.batches:
            self.batches[batch_key] = deque()
            self.batch_timestamps[batch_key] = datetime.now(UTC)
            self.batch_callbacks[batch_key] = batch_callback
            self.locks[batch_key] = asyncio.Lock()

        async with self.locks[batch_key]:
            batch = self.batches[batch_key]
            batch.append(item)

            # Check if batch should be flushed
            should_flush = (
                force_flush
                or len(batch) >= self.batch_size
                or (
                    datetime.now(UTC) - self.batch_timestamps[batch_key]
                ).total_seconds()
                >= self.batch_timeout_seconds
            )

            if should_flush and len(batch) > 0:
                # Flush batch
                items_to_process = list(batch)
                batch.clear()
                self.batch_timestamps[batch_key] = datetime.now(UTC)

                # Execute batch callback
                try:
                    result = await batch_callback(items_to_process)
                    logger.debug(
                        f"Batch {batch_key} executed: {len(items_to_process)} items",
                        extra={
                            "batch_key": batch_key,
                            "batch_size": len(items_to_process),
                        },
                    )
                    return result
                except Exception as e:
                    logger.error(
                        f"Error executing batch {batch_key}: {e}",
                        exc_info=True,
                        extra={
                            "batch_key": batch_key,
                            "batch_size": len(items_to_process),
                        },
                    )
                    raise

    async def flush_batch(self, batch_key: str) -> Any | None:
        """
        Force flush a specific batch.

        Args:
            batch_key: Batch key to flush

        Returns:
            Result from batch callback or None if batch is empty
        """
        if batch_key not in self.batches:
            return None

        async with self.locks[batch_key]:
            batch = self.batches[batch_key]
            if len(batch) == 0:
                return None

            items_to_process = list(batch)
            batch.clear()
            callback = self.batch_callbacks[batch_key]

            try:
                result = await callback(items_to_process)
                logger.debug(
                    f"Batch {batch_key} flushed: {len(items_to_process)} items"
                )
                return result
            except Exception as e:
                logger.error(f"Error flushing batch {batch_key}: {e}", exc_info=True)
                raise

    async def flush_all_batches(self) -> dict[str, Any]:
        """
        Flush all pending batches.

        Returns:
            Dictionary of batch_key to result
        """
        results = {}
        for batch_key in list(self.batches.keys()):
            try:
                result = await self.flush_batch(batch_key)
                if result is not None:
                    results[batch_key] = result
            except Exception as e:
                logger.error(f"Error flushing batch {batch_key}: {e}", exc_info=True)
                results[batch_key] = {"error": str(e)}

        return results

    def get_batch_stats(self) -> dict[str, Any]:
        """
        Get statistics about current batches.

        Returns:
            Dictionary with batch statistics
        """
        stats = {}
        for batch_key, batch in self.batches.items():
            stats[batch_key] = {
                "size": len(batch),
                "age_seconds": (
                    datetime.now(UTC) - self.batch_timestamps[batch_key]
                ).total_seconds(),
            }
        return stats


class TaskDeduplicator:
    """
    Prevents duplicate task execution using idempotency keys.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize task deduplicator.

        Args:
            ttl_seconds: Time to live for idempotency keys
        """
        self.idempotency_keys: dict[str, datetime] = {}
        self.results: dict[str, Any] = {}
        self.ttl_seconds = ttl_seconds

    def generate_idempotency_key(
        self, task_name: str, *args: Any, **kwargs: Any
    ) -> str:
        """
        Generate idempotency key from task name and arguments.

        Args:
            task_name: Task name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Idempotency key string
        """
        import hashlib
        import json

        key_data = {
            "task": task_name,
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else [],
        }
        key_string = json.dumps(key_data, default=str, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        return f"idempotency:{task_name}:{key_hash[:16]}"

    def check_duplicate(self, idempotency_key: str) -> Any | None:
        """
        Check if task with this idempotency key was already executed.

        Args:
            idempotency_key: Idempotency key to check

        Returns:
            Cached result if duplicate, None otherwise
        """
        # Clean expired keys
        self._cleanup_expired()

        if idempotency_key in self.idempotency_keys:
            # Check if result is cached
            if idempotency_key in self.results:
                logger.debug(f"Duplicate task detected: {idempotency_key}")
                return self.results[idempotency_key]

        return None

    def record_execution(self, idempotency_key: str, result: Any) -> None:
        """
        Record task execution with result.

        Args:
            idempotency_key: Idempotency key
            result: Task result
        """
        self.idempotency_keys[idempotency_key] = datetime.now(UTC)
        self.results[idempotency_key] = result

    def _cleanup_expired(self) -> None:
        """Remove expired idempotency keys"""
        cutoff = datetime.now(UTC) - timedelta(seconds=self.ttl_seconds)
        expired_keys = [
            key
            for key, timestamp in self.idempotency_keys.items()
            if timestamp < cutoff
        ]

        for key in expired_keys:
            self.idempotency_keys.pop(key, None)
            self.results.pop(key, None)


# Global instances
_task_batcher = TaskBatcher()
_task_deduplicator = TaskDeduplicator()


def get_task_batcher() -> TaskBatcher:
    """Get singleton task batcher instance"""
    return _task_batcher


def get_task_deduplicator() -> TaskDeduplicator:
    """Get singleton task deduplicator instance"""
    return _task_deduplicator
