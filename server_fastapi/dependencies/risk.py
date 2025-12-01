"""
Risk service dependency bindings.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.risk_service import RiskService


async def get_risk_service(
    db: AsyncSession = Depends(get_db_session),
) -> RiskService:
    """Provide a risk service bound to the current request's DB session."""
    return RiskService(db_session=db)

