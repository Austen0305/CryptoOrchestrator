"""
Trading service dependencies for proper dependency injection.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.trading.bot_trading_service import BotTradingService
from ..services.trading.dex_trading_service import DEXTradingService
from ..services.trading.real_money_service import RealMoneyTradingService
from ..services.trading.safe_trading_system import SafeTradingSystem


async def get_safe_trading_system(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SafeTradingSystem:
    """Provide safe trading system bound to the current DB session."""
    return SafeTradingSystem(db_session=db)


async def get_real_money_trading_service() -> RealMoneyTradingService:
    """Provide real money trading service (stateless)."""
    return RealMoneyTradingService()


async def get_dex_trading_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DEXTradingService:
    """Provide DEX trading service bound to the current DB session."""
    return DEXTradingService(db_session=db)


async def get_bot_trading_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BotTradingService:
    """Provide bot trading service bound to the current DB session."""
    return BotTradingService(session=db)
