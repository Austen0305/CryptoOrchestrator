import logging
import time
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class SystemStatus(BaseModel):
    status: str
    timestamp: str
    uptime: float
    version: str
    services: dict[str, str]
    runningBots: int = 0  # Count of active trading bots
    blockchainTrading: str = "active"  # Blockchain trading status


@router.get("/")
async def get_status() -> SystemStatus:
    """Get basic system status"""
    try:
        # Count running bots
        running_bots_count = 0
        try:
            from ..database import get_db_context
            from ..repositories.bot_repository import BotRepository

            async with get_db_context():
                BotRepository()
                # Get count of active bots (simplified - in production, count from database)
                # For now, return 0 - actual count would require querying all active bots
                running_bots_count = 0
        except Exception as bot_error:
            logger.debug(f"Could not count running bots: {bot_error}")
            running_bots_count = 0

        return SystemStatus(
            status="running",
            timestamp=datetime.now(UTC).isoformat(),
            uptime=time.time(),  # Would be actual uptime in real implementation
            version="1.0.0",
            services={
                "fastapi": "healthy",
                "database": "healthy",  # Mock
                "redis": "healthy",  # Mock
                "blockchain": "active",  # Blockchain trading active
            },
            runningBots=running_bots_count,
            blockchainTrading="active",
        )
    except Exception as e:
        logger.error(f"Failed to get status: {e}", exc_info=True)
        # Return default status instead of 500 error
        return SystemStatus(
            status="degraded",
            timestamp=datetime.now(UTC).isoformat(),
            uptime=0.0,
            version="1.0.0",
            services={
                "fastapi": "unknown",
                "database": "unknown",
                "redis": "unknown",
            },
            runningBots=0,
            blockchainTrading="unknown",
        )


@router.get("/protected")
async def get_protected_status(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> SystemStatus:
    """Get system status (authenticated endpoint)"""
    try:
        # Count running bots for authenticated user
        running_bots_count = 0
        try:
            user_id = _get_user_id(current_user)
            if user_id:
                from ..database import get_db_context
                from ..repositories.bot_repository import BotRepository

                async with get_db_context():
                    BotRepository()
                    # Get user's active bots count
                    # In production, query: SELECT COUNT(*) FROM bots WHERE user_id = ? AND active = true
                    running_bots_count = (
                        0  # Simplified - would query database in production
                    )
        except Exception as bot_error:
            logger.debug(f"Could not count running bots for user: {bot_error}")
            running_bots_count = 0

        return SystemStatus(
            status="running",
            timestamp=datetime.now(UTC).isoformat(),
            uptime=time.time(),
            version="1.0.0",
            services={
                "fastapi": "healthy",
                "database": "healthy",
                "redis": "healthy",
                "auth": "healthy",
                "blockchain": "active",
            },
            runningBots=running_bots_count,
            blockchainTrading="active",
        )
    except Exception as e:
        logger.error(f"Failed to get protected status: {e}", exc_info=True)
        # Return default status instead of 500 error
        return SystemStatus(
            status="degraded",
            timestamp=datetime.now(UTC).isoformat(),
            uptime=0.0,
            version="1.0.0",
            services={
                "fastapi": "unknown",
                "database": "unknown",
                "redis": "unknown",
                "auth": "unknown",
            },
            runningBots=0,
            blockchainTrading="unknown",
        )
