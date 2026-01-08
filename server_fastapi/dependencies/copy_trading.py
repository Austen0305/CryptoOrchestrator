"""
Copy trading service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..repositories.copy_trading_repository import CopyTradingRepository
from ..repositories.follow_repository import FollowRepository
from ..repositories.trade_repository import TradeRepository
from ..repositories.user_repository import UserRepository
from ..services.copy_trading_service import CopyTradingService


async def get_copy_trading_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CopyTradingService:
    """Provide copy trading service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    follow_repository = FollowRepository()
    copy_trading_repository = CopyTradingRepository()
    trade_repository = TradeRepository()
    user_repository = UserRepository()

    return CopyTradingService(
        db=db,
        follow_repository=follow_repository,
        copy_trading_repository=copy_trading_repository,
        trade_repository=trade_repository,
        user_repository=user_repository,
    )
