"""
Advanced orders service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.trading.advanced_orders import AdvancedOrdersService
from ..repositories.order_repository import OrderRepository


async def get_advanced_orders_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdvancedOrdersService:
    """Provide advanced orders service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    order_repository = OrderRepository()

    return AdvancedOrdersService(
        db=db,
        order_repository=order_repository,
    )
