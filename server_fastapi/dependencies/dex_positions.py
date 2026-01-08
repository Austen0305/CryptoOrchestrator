"""
DEX positions service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..repositories.dex_position_repository import DEXPositionRepository
from ..services.trading.dex_position_service import DEXPositionService


async def get_dex_position_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DEXPositionService:
    """Provide DEX position service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    position_repository = DEXPositionRepository()

    return DEXPositionService(
        db_session=db,  # Note: service uses db_session parameter name
        position_repository=position_repository,
    )
