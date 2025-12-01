"""
Bot service dependencies to ensure shared DB sessions per request.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.trading.bot_service import BotService
from ..services.trading.bot_trading_service import BotTradingService


async def get_bot_service(
    db: AsyncSession = Depends(get_db_session),
) -> BotService:
    """Provide bot service bound to the current DB session."""
    return BotService(db_session=db)


async def get_bot_trading_service(
    db: AsyncSession = Depends(get_db_session),
) -> BotTradingService:
    """Provide bot trading service bound to the current DB session."""
    return BotTradingService(session=db)

