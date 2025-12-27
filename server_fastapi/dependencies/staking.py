"""
Staking service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.staking_service import StakingService
from ..repositories.wallet_balance_repository import WalletBalanceRepository
from ..repositories.transaction_repository import TransactionRepository


async def get_staking_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> StakingService:
    """Provide staking service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    wallet_repository = WalletBalanceRepository()
    transaction_repository = TransactionRepository()

    return StakingService(
        db=db,
        wallet_repository=wallet_repository,
        transaction_repository=transaction_repository,
    )
