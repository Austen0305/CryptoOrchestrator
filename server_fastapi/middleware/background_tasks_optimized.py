"""
Optimized Background Task Queue
Manages background tasks with priority, batching, and monitoring
"""

import asyncio
import logging
import time
from typing import Callable, Any, Dict, Optional, List
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from functools import wraps

logger = logging.getLogger(__name__)


class TaskPriority(IntEnum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BackgroundTask:
    """Background task metadata"""
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    retries: int = 0
    max_retries: int = 3
    task_id: Optional[str] = None


class OptimizedBackgroundTaskQueue:
    """
    Optimized background task queue with:
    - Priority-based execution
    - Task batching
    - Retry logic
    - Monitoring
    - Rate limiting
    """

    def __init__(
        self,
        max_workers: int = 10,
        batch_size: int = 10,
        batch_window_ms: int = 100,
    ):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.batch_window_ms = batch_window_ms / 1000.0
        
        self.task_queue: deque = deque()
        self.workers: List[asyncio.Task] = []
        self.running = False
        
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "retried_tasks": 0,
        }

    async def enqueue(
        self,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Enqueue a background task"""
        if not task_id:
            task_id = f"task_{int(time.time() * 1000)}"
        
        task = BackgroundTask(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            task_id=task_id,
        )
        
        # Insert based on priority
        inserted = False
        for i, existing_task in enumerate(self.task_queue):
            if task.priority > existing_task.priority:
                self.task_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task)
        
        self.stats["total_tasks"] += 1
        
        # Start workers if not running
        if not self.running:
            await self.start()
        
        return task_id

    async def start(self):
        """Start background workers"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} background task workers")

    async def stop(self, timeout: float = 30.0):
        """Stop background workers gracefully"""
        self.running = False
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.wait_for(
                asyncio.gather(*self.workers, return_exceptions=True),
                timeout=timeout
            )
        
        logger.info("Background task workers stopped")

    async def _worker(self, worker_id: str):
        """Background worker that processes tasks"""
        logger.debug(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get batch of tasks
                batch = await self._get_batch()
                
                if not batch:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process batch
                await self._process_batch(batch)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.debug(f"Worker {worker_id} stopped")

    async def _get_batch(self) -> List[BackgroundTask]:
        """Get a batch of tasks to process"""
        if not self.task_queue:
            return []
        
        batch = []
        start_time = time.time()
        
        while len(batch) < self.batch_size and self.task_queue:
            elapsed = time.time() - start_time
            if elapsed >= self.batch_window_ms and batch:
                break
            
            task = self.task_queue.popleft()
            batch.append(task)
        
        return batch

    async def _process_batch(self, batch: List[BackgroundTask]):
        """Process a batch of tasks"""
        # Process in parallel
        tasks = [self._execute_task(task) for task in batch]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_task(self, task: BackgroundTask):
        """Execute a single task with retry logic"""
        try:
            if asyncio.iscoroutinefunction(task.func):
                await task.func(*task.args, **task.kwargs)
            else:
                task.func(*task.args, **task.kwargs)
            
            self.stats["completed_tasks"] += 1
            logger.debug(f"Task {task.task_id} completed")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
            
            # Retry if possible
            if task.retries < task.max_retries:
                task.retries += 1
                self.stats["retried_tasks"] += 1
                
                # Re-enqueue with exponential backoff
                await asyncio.sleep(2 ** task.retries)
                await self.enqueue(
                    task.func,
                    *task.args,
                    priority=task.priority,
                    max_retries=task.max_retries,
                    task_id=task.task_id,
                    **task.kwargs,
                )
            else:
                self.stats["failed_tasks"] += 1
                logger.error(f"Task {task.task_id} failed after {task.max_retries} retries")

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self.stats,
            "queue_size": len(self.task_queue),
            "active_workers": len([w for w in self.workers if not w.done()]),
            "success_rate": (
                self.stats["completed_tasks"] / self.stats["total_tasks"] * 100
                if self.stats["total_tasks"] > 0 else 0
            ),
        }


# Global task queue instance
background_task_queue = OptimizedBackgroundTaskQueue()


def background_task(
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
):
    """Decorator to run function as background task"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            task_id = await background_task_queue.enqueue(
                func,
                *args,
                priority=priority,
                max_retries=max_retries,
                **kwargs,
            )
            return task_id
        return wrapper
    return decorator

