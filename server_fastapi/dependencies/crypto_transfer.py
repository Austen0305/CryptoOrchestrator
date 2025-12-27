"""
Crypto transfer service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.crypto_transfer_service import CryptoTransferService
from ..repositories.wallet_balance_repository import WalletBalanceRepository
from ..repositories.transaction_repository import TransactionRepository


async def get_crypto_transfer_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CryptoTransferService:
    """Provide crypto transfer service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    wallet_repository = WalletBalanceRepository()
    transaction_repository = TransactionRepository()

    return CryptoTransferService(
        db=db,
        wallet_repository=wallet_repository,
        transaction_repository=transaction_repository,
    )
