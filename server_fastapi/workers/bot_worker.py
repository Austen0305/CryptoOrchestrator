"""
Celery Worker for Cloud Bot Execution
Runs trading bots in isolated worker processes
"""

import logging
import os
from datetime import UTC, datetime

from celery import Celery, Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..billing import SubscriptionService

# Import models and services
from ..database import DATABASE_URL
from ..models.bot import Bot
from ..services.trading.bot_service import BotService

logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    "bot_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Create async database session for worker
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class DatabaseTask(Task):
    """Celery task with database session"""

    def __call__(self, *args, **kwargs):
        async def run_async():
            async with async_session() as session:
                try:
                    result = await self.run(*args, session=session, **kwargs)
                    await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Task error: {e}", exc_info=True)
                    raise

        # Run async task synchronously
        import asyncio

        return asyncio.run(run_async())


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="bot_worker.execute_bot",
    max_retries=3,
    default_retry_delay=60,
)
async def execute_bot(self, bot_id: str, user_id: int, session: AsyncSession = None):
    """
    Execute a trading bot strategy
    Runs in isolated worker process
    """
    try:
        # Check subscription status
        subscription_service = SubscriptionService()
        is_active = await subscription_service.check_subscription_active(
            db=session, user_id=user_id
        )

        if not is_active:
            logger.warning(
                f"User {user_id} subscription inactive. Stopping bot {bot_id}"
            )
            await stop_bot(bot_id, user_id, session)
            return {
                "success": False,
                "error": "Subscription inactive",
                "bot_id": bot_id,
            }

        # Get bot
        result = await session.execute(
            select(Bot).where(and_(Bot.id == bot_id, Bot.user_id == user_id))
        )
        bot = result.scalar_one_or_none()

        if not bot:
            logger.error(f"Bot {bot_id} not found for user {user_id}")
            return {"success": False, "error": "Bot not found", "bot_id": bot_id}

        if not bot.active:
            logger.info(f"Bot {bot_id} is not active")
            return {"success": False, "error": "Bot is not active", "bot_id": bot_id}

        # Execute bot strategy
        logger.info(f"Executing bot {bot_id} for user {user_id}")

        # Bot service bound to the worker session
        bot_service = BotService(db_session=session)

        # Execute strategy
        result = await bot_service.execute_strategy(
            bot_id=bot_id,
            user_id=user_id,
            strategy=bot.strategy,
            config=bot.parameters or {},
        )

        # Update bot status
        bot.status = "running"
        bot.last_started_at = datetime.now(UTC)

        # Store performance data if available
        if result and isinstance(result, dict):
            import json

            bot.performance_data = json.dumps(result.get("performance", {}))

        await session.commit()

        logger.info(f"Bot {bot_id} executed successfully")
        return {"success": True, "bot_id": bot_id, "result": result}

    except Exception as e:
        logger.error(f"Error executing bot {bot_id}: {e}", exc_info=True)

        # Retry if needed
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            # Update bot status to error
            if bot:
                bot.status = "error"
                await session.commit()

            return {"success": False, "error": str(e), "bot_id": bot_id}


@celery_app.task(
    bind=True, base=DatabaseTask, name="bot_worker.stop_bot", max_retries=3
)
async def stop_bot(self, bot_id: str, user_id: int, session: AsyncSession = None):
    """Stop a running bot"""
    try:
        result = await session.execute(
            select(Bot).where(and_(Bot.id == bot_id, Bot.user_id == user_id))
        )
        bot = result.scalar_one_or_none()

        if not bot:
            return {"success": False, "error": "Bot not found"}

        bot.active = False
        bot.status = "stopped"
        bot.last_stopped_at = datetime.now(UTC)

        await session.commit()

        logger.info(f"Bot {bot_id} stopped")
        return {"success": True, "bot_id": bot_id}

    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="bot_worker.check_subscriptions", ignore_result=True)
async def check_subscriptions(session: AsyncSession = None):
    """
    Periodic task to check subscription status and stop bots for inactive subscriptions
    Runs every hour
    """
    try:
        from sqlalchemy import select

        # Get all active bots
        result = await session.execute(select(Bot).where(Bot.active))
        active_bots = result.scalars().all()

        subscription_service = SubscriptionService()
        stopped_count = 0

        for bot in active_bots:
            is_active = await subscription_service.check_subscription_active(
                db=session, user_id=bot.user_id
            )

            if not is_active:
                logger.info(f"Stopping bot {bot.id} due to inactive subscription")
                bot.active = False
                bot.status = "stopped"
                stopped_count += 1

        if stopped_count > 0:
            await session.commit()
            logger.info(f"Stopped {stopped_count} bots due to inactive subscriptions")

        return {"checked": len(active_bots), "stopped": stopped_count}

    except Exception as e:
        logger.error(f"Error checking subscriptions: {e}", exc_info=True)
        return {"error": str(e)}


# Import missing 'and_' in execute_bot
from sqlalchemy import and_
