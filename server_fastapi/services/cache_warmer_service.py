"""
Cache Warmer Service
Pre-populates cache with frequently accessed data to reduce cache misses
"""
import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)


@dataclass
class CacheWarmupTask:
    """Cache warmup task definition"""
    name: str
    function: Callable
    ttl: int = 300  # Cache TTL in seconds
    interval: int = 60  # Warmup interval in seconds
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0


class CacheWarmerService:
    """Service for warming up cache with frequently accessed data"""
    
    def __init__(self):
        self.tasks: Dict[str, CacheWarmupTask] = {}
        self._running = False
        self._warmup_task: Optional[asyncio.Task] = None
    
    def register_task(
        self,
        name: str,
        function: Callable,
        ttl: int = 300,
        interval: int = 60,
        enabled: bool = True
    ):
        """Register a cache warmup task"""
        task = CacheWarmupTask(
            name=name,
            function=function,
            ttl=ttl,
            interval=interval,
            enabled=enabled,
            next_run=datetime.utcnow() + timedelta(seconds=interval)
        )
        self.tasks[name] = task
        logger.info(f"Registered cache warmup task: {name} (interval: {interval}s)")
    
    async def warmup_task(self, task: CacheWarmupTask) -> bool:
        """Execute a single warmup task"""
        try:
            start_time = datetime.utcnow()
            
            # Execute the warmup function
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function()
            else:
                result = task.function()
            
            # Cache the result
            cache_key = f"warmup:{task.name}"
            await cache_service.set(cache_key, result, ttl=task.ttl)
            
            # Update task stats
            task.last_run = start_time
            task.next_run = datetime.utcnow() + timedelta(seconds=task.interval)
            task.run_count += 1
            
            logger.debug(f"Cache warmup task '{task.name}' completed successfully")
            return True
            
        except Exception as e:
            task.error_count += 1
            logger.error(f"Cache warmup task '{task.name}' failed: {e}", exc_info=True)
            return False
    
    async def run_warmup_cycle(self):
        """Run warmup cycle for all enabled tasks"""
        if not self._running:
            return
        
        now = datetime.utcnow()
        tasks_to_run = [
            task for task in self.tasks.values()
            if task.enabled and (task.next_run is None or task.next_run <= now)
        ]
        
        if not tasks_to_run:
            return
        
        logger.info(f"Running cache warmup cycle for {len(tasks_to_run)} tasks")
        
        # Run tasks concurrently
        results = await asyncio.gather(
            *[self.warmup_task(task) for task in tasks_to_run],
            return_exceptions=True
        )
        
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Cache warmup cycle completed: {success_count}/{len(tasks_to_run)} successful")
    
    async def start(self):
        """Start the cache warmer service"""
        if self._running:
            logger.warning("Cache warmer service already running")
            return
        
        self._running = True
        logger.info("Starting cache warmer service")
        
        # Run initial warmup
        await self.run_warmup_cycle()
        
        # Start periodic warmup loop
        self._warmup_task = asyncio.create_task(self._warmup_loop())
    
    async def stop(self):
        """Stop the cache warmer service"""
        self._running = False
        if self._warmup_task:
            self._warmup_task.cancel()
            try:
                await self._warmup_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache warmer service stopped")
    
    async def _warmup_loop(self):
        """Main warmup loop"""
        while self._running:
            try:
                await self.run_warmup_cycle()
                # Wait 30 seconds before next cycle check
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in warmup loop: {e}", exc_info=True)
                await asyncio.sleep(30)
    
    def get_status(self) -> Dict[str, Any]:
        """Get cache warmer service status"""
        return {
            "running": self._running,
            "tasks_count": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "tasks": [
                {
                    "name": task.name,
                    "enabled": task.enabled,
                    "interval": task.interval,
                    "run_count": task.run_count,
                    "error_count": task.error_count,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None
                }
                for task in self.tasks.values()
            ]
        }
    
    async def warmup_now(self, task_name: Optional[str] = None) -> Dict[str, bool]:
        """Manually trigger warmup for specific task or all tasks"""
        if task_name:
            if task_name not in self.tasks:
                raise ValueError(f"Task '{task_name}' not found")
            task = self.tasks[task_name]
            success = await self.warmup_task(task)
            return {task_name: success}
        else:
            # Warmup all enabled tasks
            results = {}
            for task in self.tasks.values():
                if task.enabled:
                    results[task.name] = await self.warmup_task(task)
            return results


# Global cache warmer instance
cache_warmer_service = CacheWarmerService()


# Example warmup functions
async def warmup_market_data():
    """Warmup market data cache"""
    try:
        from ..services.exchange_service import ExchangeService
        exchange_service = ExchangeService()
        
        # Warmup popular trading pairs
        popular_pairs = ["BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD"]
        for pair in popular_pairs:
            try:
                ticker = await exchange_service.get_ticker(pair)
                cache_key = f"market_data:{pair}"
                await cache_service.set(cache_key, ticker, ttl=60)
            except Exception as e:
                logger.warning(f"Failed to warmup {pair}: {e}")
        
        return {"pairs_warmed": len(popular_pairs)}
    except Exception as e:
        logger.error(f"Market data warmup failed: {e}")
        return {}


async def warmup_staking_options():
    """Warmup staking options cache"""
    try:
        from ..services.staking_service import StakingService
        from ..database import get_db_context
        
        async with get_db_context() as db:
            staking_service = StakingService(db)
            options = await staking_service.get_staking_options()
            
            cache_key = "staking:options"
            await cache_service.set(cache_key, options, ttl=600)  # 10 minutes
        
        return {"options_count": len(options)}
    except Exception as e:
        logger.error(f"Staking options warmup failed: {e}")
        return {}


# Register default warmup tasks
def register_default_warmup_tasks():
    """Register default cache warmup tasks"""
    cache_warmer_service.register_task(
        name="market_data",
        function=warmup_market_data,
        ttl=60,  # 1 minute
        interval=30  # Run every 30 seconds
    )
    
    cache_warmer_service.register_task(
        name="staking_options",
        function=warmup_staking_options,
        ttl=600,  # 10 minutes
        interval=300  # Run every 5 minutes
    )

