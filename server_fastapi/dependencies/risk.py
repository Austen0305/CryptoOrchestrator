"""
Risk service dependency bindings.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.risk_service import RiskService


async def get_risk_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> RiskService:
    """Provide a risk service with injected repositories."""
    # ✅ RiskService creates its own repository internally, just pass db_session
    return RiskService(
        db_session=db,
    )
