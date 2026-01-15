"""
Cache Warmer Service
Pre-populates cache with frequently accessed data to reduce cache misses
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

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
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    error_count: int = 0


class CacheWarmerService:
    """Service for warming up cache with frequently accessed data"""

    def __init__(self):
        self.tasks: dict[str, CacheWarmupTask] = {}
        self._running = False
        self._warmup_task: asyncio.Task | None = None

    def register_task(
        self,
        name: str,
        function: Callable,
        ttl: int = 300,
        interval: int = 60,
        enabled: bool = True,
    ):
        """Register a cache warmup task"""
        task = CacheWarmupTask(
            name=name,
            function=function,
            ttl=ttl,
            interval=interval,
            enabled=enabled,
            next_run=datetime.now(UTC) + timedelta(seconds=interval),
        )
        self.tasks[name] = task
        logger.info(f"Registered cache warmup task: {name} (interval: {interval}s)")

    async def warmup_task(self, task: CacheWarmupTask) -> bool:
        """Execute a single warmup task"""
        try:
            start_time = datetime.now(UTC)

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
            task.next_run = datetime.now(UTC) + timedelta(seconds=task.interval)
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

        now = datetime.now(UTC)
        tasks_to_run = [
            task
            for task in self.tasks.values()
            if task.enabled and (task.next_run is None or task.next_run <= now)
        ]

        if not tasks_to_run:
            return

        logger.info(f"Running cache warmup cycle for {len(tasks_to_run)} tasks")

        # Run tasks concurrently
        results = await asyncio.gather(
            *[self.warmup_task(task) for task in tasks_to_run], return_exceptions=True
        )

        success_count = sum(1 for r in results if r is True)
        logger.info(
            f"Cache warmup cycle completed: {success_count}/{len(tasks_to_run)} successful"
        )

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
            with contextlib.suppress(asyncio.CancelledError):
                await self._warmup_task
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

    def get_status(self) -> dict[str, Any]:
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
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                }
                for task in self.tasks.values()
            ],
        }

    async def warmup_now(self, task_name: str | None = None) -> dict[str, bool]:
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
    """Warmup market data cache using MarketDataService"""
    try:
        from ..services.market_data_service import get_market_data_service

        market_data_service = get_market_data_service()

        # Warmup popular trading pairs
        popular_pairs = ["BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD"]
        pairs_warmed = 0
        for pair in popular_pairs:
            try:
                # Get market data from MarketDataService
                market_data = await market_data_service.get_market_data(pair)
                if market_data:
                    cache_key = f"market_data:{pair}"
                    await cache_service.set(cache_key, market_data, ttl=60)
                    pairs_warmed += 1
            except Exception as e:
                logger.warning(f"Failed to warmup {pair}: {e}")

        return {"pairs_warmed": pairs_warmed}
    except Exception as e:
        logger.error(f"Market data warmup failed: {e}")
        return {}


async def warmup_staking_options():
    """Warmup staking options cache"""
    try:
        from ..database import get_db_context
        from ..services.staking_service import StakingService

        async with get_db_context() as db:
            staking_service = StakingService(db)
            options = await staking_service.get_staking_options()

            cache_key = "staking:options"
            await cache_service.set(cache_key, options, ttl=600)  # 10 minutes

        return {"options_count": len(options)}
    except Exception as e:
        logger.error(f"Staking options warmup failed: {e}")
        return {}


async def warmup_popular_token_prices():
    """Warmup popular token prices from MarketDataService"""
    try:
        from ..services.market_data_service import get_market_data_service

        market_data_service = get_market_data_service()

        # Popular tokens for trading
        popular_tokens = [
            "BTC/USD",
            "ETH/USD",
            "SOL/USD",
            "ADA/USD",
            "DOT/USD",
            "MATIC/USD",
            "AVAX/USD",
            "LINK/USD",
            "UNI/USD",
            "AAVE/USD",
        ]

        prices_warmed = 0
        for pair in popular_tokens:
            try:
                price = await market_data_service.get_price(pair)
                if price is not None:
                    cache_key = f"markets:get_price:{pair}"
                    await cache_service.set(
                        cache_key, {"pair": pair, "price": price}, ttl=30
                    )
                    prices_warmed += 1
            except Exception as e:
                logger.warning(f"Failed to warmup price for {pair}: {e}")

        logger.info(f"Warmed up {prices_warmed} popular token prices")
        return {"prices_warmed": prices_warmed}
    except Exception as e:
        logger.error(f"Popular token prices warmup failed: {e}")
        return {}


async def warmup_active_bot_statuses():
    """Warmup active bot statuses for users with active bots"""
    try:
        from sqlalchemy import select

        from ..database import get_db_context
        from ..models.bot import Bot
        from ..repositories.bot_repository import BotRepository

        async with get_db_context() as db:
            # Get all active bots
            stmt = select(Bot).where(Bot.active).limit(100)
            result = await db.execute(stmt)
            active_bots = result.scalars().all()

            bot_repo = BotRepository()
            bots_warmed = 0

            for bot in active_bots:
                try:
                    # Get bot config to warm cache
                    bot_config = await bot_repo.get_by_id(db, bot.id)
                    if bot_config:
                        cache_key = f"bots:get_bot:{bot.id}"
                        # Convert to dict for caching
                        bot_dict = {
                            "id": str(bot_config.id),
                            "user_id": bot_config.user_id,
                            "name": bot_config.name,
                            "symbol": bot_config.symbol,
                            "strategy": bot_config.strategy,
                            "is_active": bot_config.is_active,
                        }
                        await cache_service.set(cache_key, bot_dict, ttl=120)
                        bots_warmed += 1
                except Exception as e:
                    logger.warning(f"Failed to warmup bot {bot.id}: {e}")

            logger.info(f"Warmed up {bots_warmed} active bot statuses")
            return {"bots_warmed": bots_warmed}
    except Exception as e:
        logger.error(f"Active bot statuses warmup failed: {e}")
        return {}


async def warmup_user_portfolios():
    """Warmup portfolios for active users"""
    try:
        from sqlalchemy import func, select

        from ..database import get_db_context
        from ..models.trade import Trade
        from ..models.user import User

        async with get_db_context() as db:
            # Get users with recent trades (active users)
            stmt = (
                select(User.id, func.count(Trade.id).label("trade_count"))
                .join(Trade, User.id == Trade.user_id)
                .group_by(User.id)
                .having(func.count(Trade.id) > 0)
                .limit(50)  # Warm up top 50 active users
            )
            result = await db.execute(stmt)
            active_users = result.all()

            portfolios_warmed = 0
            for user_row in active_users:
                try:
                    user_id = user_row.id
                    # Warm up both paper and real portfolios
                    for mode in ["paper", "real"]:
                        cache_key = f"portfolio:get_portfolio:{mode}:{user_id}"
                        # Set placeholder - actual portfolio will be computed on first request
                        await cache_service.set(
                            cache_key,
                            {"user_id": user_id, "mode": mode, "warmed": True},
                            ttl=300,
                        )
                    portfolios_warmed += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to warmup portfolio for user {user_row.id}: {e}"
                    )

            logger.info(f"Warmed up {portfolios_warmed} user portfolios")
            return {"portfolios_warmed": portfolios_warmed}
    except Exception as e:
        logger.error(f"User portfolios warmup failed: {e}")
        return {}


# Register default warmup tasks
def register_default_warmup_tasks():
    """Register default cache warmup tasks"""
    cache_warmer_service.register_task(
        name="market_data",
        function=warmup_market_data,
        ttl=60,  # 1 minute
        interval=30,  # Run every 30 seconds
    )

    cache_warmer_service.register_task(
        name="popular_token_prices",
        function=warmup_popular_token_prices,
        ttl=30,  # 30 seconds (matches price endpoint TTL)
        interval=20,  # Run every 20 seconds
    )

    cache_warmer_service.register_task(
        name="active_bot_statuses",
        function=warmup_active_bot_statuses,
        ttl=120,  # 2 minutes (matches bot status endpoint TTL)
        interval=60,  # Run every minute
    )

    cache_warmer_service.register_task(
        name="user_portfolios",
        function=warmup_user_portfolios,
        ttl=300,  # 5 minutes (matches portfolio endpoint TTL)
        interval=180,  # Run every 3 minutes
    )

    cache_warmer_service.register_task(
        name="staking_options",
        function=warmup_staking_options,
        ttl=600,  # 10 minutes
        interval=300,  # Run every 5 minutes
    )
