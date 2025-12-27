"""
P&L service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.pnl_service import PnLService
from ..repositories.trade_repository import TradeRepository


async def get_pnl_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PnLService:
    """Provide P&L service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    trade_repository = TradeRepository()

    return PnLService(
        db=db,
        trade_repository=trade_repository,
    )
