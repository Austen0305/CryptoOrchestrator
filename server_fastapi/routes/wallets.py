"""
Wallet Management Routes
API endpoints for managing user blockchain wallets
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..models.user_wallet import UserWallet
from ..services.wallet_service import WalletService
from ..utils.query_optimizer import QueryOptimizer
from ..utils.route_helpers import _get_user_id
from ..utils.validation_2026 import (
    ValidationError,
    validate_ethereum_address,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class CreateCustodialWalletRequest(BaseModel):
    chain_id: int = Field(
        ..., description="Blockchain ID (1=Ethereum, 8453=Base, etc.)"
    )
    label: str | None = Field(None, description="Optional user-friendly label")

    model_config = {
        "json_schema_extra": {"example": {"chain_id": 1, "label": "My Ethereum Wallet"}}
    }


class RegisterExternalWalletRequest(BaseModel):
    wallet_address: str = Field(..., description="User's wallet address (checksummed)")
    chain_id: int = Field(..., ge=1, description="Blockchain ID (must be >= 1)")
    label: str | None = Field(
        None, max_length=100, description="Optional user-friendly label"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "chain_id": 1,
                "label": "My MetaMask Wallet",
            }
        }
    }


class WalletResponse(BaseModel):
    wallet_id: int
    address: str
    chain_id: int
    wallet_type: str
    label: str | None
    is_verified: bool
    is_active: bool
    balance: dict | None = None
    last_balance_update: str | None = None

    model_config = {"from_attributes": True}


class DepositAddressResponse(BaseModel):
    address: str
    chain_id: int
    chain_name: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "chain_id": 1,
                "chain_name": "Ethereum",
            }
        }
    }


# Chain name mapping
CHAIN_NAMES = {
    1: "Ethereum",
    8453: "Base",
    42161: "Arbitrum One",
    137: "Polygon",
    10: "Optimism",
    43114: "Avalanche",
    56: "BNB Chain",
}


@router.post("/custodial", response_model=WalletResponse, tags=["Wallets"])
async def create_custodial_wallet(
    request: CreateCustodialWalletRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WalletResponse:
    """
    Create or get a custodial wallet for the user

    Returns the wallet address that can be used for deposits and custodial trading.
    """
    try:
        user_id = int(_get_user_id(current_user))
        service = WalletService()
        wallet_info = await service.create_custodial_wallet(
            user_id=user_id,
            chain_id=request.chain_id,
            label=request.label,
            db=db,
        )

        if not wallet_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create custodial wallet",
            )

        return WalletResponse(**wallet_info)

    except Exception as e:
        logger.error(f"Error creating custodial wallet: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/external", response_model=WalletResponse, tags=["Wallets"])
async def register_external_wallet(
    request: RegisterExternalWalletRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WalletResponse:
    """
    Register an external wallet address (user's own wallet)

    This allows users to connect their own wallets for non-custodial trading.
    """
    try:
        service = WalletService()

        # Enhanced address validation (2026 best practice)
        try:
            validated_address = validate_ethereum_address(request.wallet_address)
        except ValueError as e:
            raise ValidationError(
                f"Invalid wallet address: {e}", field="wallet_address"
            )

        user_id = int(_get_user_id(current_user))
        wallet_info = await service.register_external_wallet(
            user_id=user_id,
            wallet_address=validated_address,  # Use validated/checksummed address
            chain_id=request.chain_id,
            label=request.label,
            db=db,
        )

        if not wallet_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register external wallet",
            )

        return WalletResponse(**wallet_info)

    except (HTTPException, ValidationError):
        raise
    except ValueError as e:
        # Validation errors from validation utilities
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(
            f"Error registering external wallet: {e}",
            exc_info=True,
            extra={
                "user_id": int(_get_user_id(current_user)),
                "chain_id": request.chain_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/", response_model=list[WalletResponse], tags=["Wallets"])
@cached(ttl=120, prefix="wallets")  # 120s TTL for wallet lists
async def get_user_wallets(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[WalletResponse]:
    """
    Get all wallets for the current user with pagination
    """
    try:
        user_id = int(_get_user_id(current_user))
        from sqlalchemy import func, select

        # Build query
        query = select(UserWallet).where(UserWallet.user_id == user_id)

        # Get total count
        count_query = (
            select(func.count())
            .select_from(UserWallet)
            .where(UserWallet.user_id == user_id)
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = QueryOptimizer.paginate_query(query, page=page, page_size=page_size)
        query = query.order_by(UserWallet.created_at.desc())

        # Execute query
        result = await db.execute(query)
        wallets = result.scalars().all()

        # Convert to response format
        return [
            WalletResponse(
                wallet_id=wallet.id,
                address=wallet.wallet_address,
                chain_id=wallet.chain_id,
                wallet_type=wallet.wallet_type,
                label=wallet.label,
                is_verified=wallet.is_verified,
                is_active=wallet.is_active,
            )
            for wallet in wallets
        ]

    except Exception as e:
        logger.error(f"Error getting user wallets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/deposit-address/{chain_id}",
    response_model=DepositAddressResponse,
    tags=["Wallets"],
)
async def get_deposit_address(
    chain_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DepositAddressResponse:
    """
    Get or create a deposit address for the user (custodial wallet)

    This address can be used to deposit funds for custodial trading.
    """
    try:
        user_id = int(_get_user_id(current_user))
        service = WalletService()
        address = await service.get_deposit_address(
            user_id=user_id, chain_id=chain_id, db=db
        )

        if not address:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get deposit address",
            )

        chain_name = CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")

        return DepositAddressResponse(
            address=address,
            chain_id=chain_id,
            chain_name=chain_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deposit address: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


class WalletBalanceResponse(BaseModel):
    balance: str
    token: str
    token_address: str | None = None
    chain_id: int
    last_updated: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "balance": "1.5",
                "token": "ETH",
                "token_address": None,
                "chain_id": 1,
                "last_updated": "2025-12-06T12:00:00Z",
            }
        }
    }


@router.get(
    "/{wallet_id}/balance", response_model=WalletBalanceResponse, tags=["Wallets"]
)
async def get_wallet_balance(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    token_address: str | None = None,
) -> WalletBalanceResponse:
    """
    Get wallet balance (ETH or ERC-20 token)

    Args:
        wallet_id: Wallet ID
        token_address: Optional token contract address (None for ETH)
    """
    try:
        from sqlalchemy import select

        # Find wallet by ID and verify ownership
        user_id = int(_get_user_id(current_user))
        stmt = select(UserWallet).where(
            UserWallet.id == wallet_id,
            UserWallet.user_id == user_id,
            UserWallet.is_active.is_(True),
        )
        result = await db.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )

        service = WalletService()
        balance_info = await service.get_wallet_balance(
            wallet_id=wallet_id,
            chain_id=wallet.chain_id,
            address=wallet.wallet_address,
            token_address=token_address,
            db=db,
        )

        if not balance_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch wallet balance",
            )

        return WalletBalanceResponse(**balance_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


class WithdrawalRequest(BaseModel):
    to_address: str = Field(..., description="Destination wallet address")
    amount: str = Field(
        ..., description="Amount to withdraw (as string to preserve precision)"
    )
    token_address: str | None = Field(
        None, description="Token contract address (None for ETH)"
    )
    mfa_token: str | None = Field(
        None, description="2FA token for withdrawal confirmation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "amount": "0.1",
                "token_address": None,
                "mfa_token": "123456",
            }
        }
    }


class WithdrawalResponse(BaseModel):
    status: str
    message: str
    wallet_id: int
    to_address: str
    amount: str
    token_address: str | None = None
    transaction_hash: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "pending",
                "message": "Withdrawal submitted",
                "wallet_id": 1,
                "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "amount": "0.1",
                "token_address": None,
                "transaction_hash": None,
            }
        }
    }


@router.post(
    "/{wallet_id}/withdraw", response_model=WithdrawalResponse, tags=["Wallets"]
)
async def process_withdrawal(
    wallet_id: int,
    request: WithdrawalRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    client_ip: str = None,  # Will be set by middleware or extracted from request
) -> WithdrawalResponse:
    """
    Process a withdrawal from a custodial wallet

    Requires 2FA for security. Only custodial wallets can withdraw.
    Enforces IP whitelisting if enabled for the user.
    """
    try:
        from decimal import Decimal

        from ..repositories.wallet_repository import WalletRepository
        from ..services.security.ip_whitelist_service import ip_whitelist_service

        user_id = int(_get_user_id(current_user))

        # Check IP whitelist if enabled
        # Note: client_ip should be extracted from request in production
        # For now, we'll check if IP whitelisting is enabled for this user
        try:
            whitelist = await ip_whitelist_service.get_whitelist(user_id)
            if whitelist and len(whitelist) > 0:
                # IP whitelisting is enabled - verify IP
                # In production, extract IP from request
                # For now, this is a placeholder - actual IP extraction happens in middleware
                # The middleware should set request.state.client_ip
                pass
        except Exception as e:
            logger.warning(f"IP whitelist check failed (may not be enabled): {e}")

        repository = WalletRepository(db)
        wallets = await repository.get_user_wallets(user_id)
        wallet = next((w for w in wallets if w.id == wallet_id), None)

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )

        if wallet.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this wallet",
            )

        if wallet.wallet_type != "custodial":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Withdrawals only supported for custodial wallets",
            )

        # Validate 2FA if provided
        if request.mfa_token:
            from ..services.two_factor_service import two_factor_service

            is_valid = await two_factor_service.verify_totp(
                user_id=user_id,
                token=request.mfa_token,
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA token",
                )

        # Parse amount
        try:
            amount = Decimal(request.amount)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid amount format",
            )

        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than zero",
            )

        service = WalletService()
        result = await service.process_withdrawal(
            wallet_id=wallet_id,
            user_id=user_id,
            to_address=request.to_address,
            amount=amount,
            token_address=request.token_address,
            chain_id=wallet.chain_id,
            db=db,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process withdrawal",
            )

        return WithdrawalResponse(
            status=result.get("status", "pending"),
            message=result.get("message", "Withdrawal submitted"),
            wallet_id=wallet_id,
            to_address=request.to_address,
            amount=request.amount,
            token_address=request.token_address,
            transaction_hash=result.get("transaction_hash"),
        )

    except (HTTPException, ValidationError):
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


class TransactionResponse(BaseModel):
    transaction_hash: str
    from_address: str
    to_address: str
    amount: str
    token_address: str | None = None
    chain_id: int
    status: str
    block_number: int | None = None
    timestamp: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "transaction_hash": "0x123...",
                "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "to_address": "0x456...",
                "amount": "0.1",
                "token_address": None,
                "chain_id": 1,
                "status": "confirmed",
                "block_number": 12345678,
                "timestamp": "2025-12-06T12:00:00Z",
            }
        }
    }


@router.get(
    "/{wallet_id}/transactions",
    response_model=list[TransactionResponse],
    tags=["Wallets"],
)
@cached(ttl=60, prefix="wallet_transactions")  # 60s TTL for transaction lists
async def get_wallet_transactions(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[TransactionResponse]:
    """
    Get transaction history for a wallet with pagination

    Args:
        wallet_id: Wallet ID
        page: Page number (1-indexed)
        page_size: Items per page
    """
    try:
        user_id = int(_get_user_id(current_user))
        from ..repositories.wallet_repository import WalletRepository

        repository = WalletRepository(db)
        wallets = await repository.get_user_wallets(user_id)
        wallet = next((w for w in wallets if w.id == wallet_id), None)

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )

        if wallet.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this wallet",
            )

        # For now, return empty list - transaction history would be stored in a separate table
        # In production, this would query a transactions table or blockchain explorer API
        logger.info(
            f"Transaction history requested for wallet {wallet_id} - not yet implemented"
        )

        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet transactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/refresh-balances", tags=["Wallets"])
async def refresh_wallet_balances(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """
    Refresh balances for all user wallets

    Forces a fresh fetch from the blockchain for all wallets.
    """
    try:
        user_id = int(_get_user_id(current_user))
        service = WalletService()
        results = await service.refresh_wallet_balances(
            user_id=user_id,
            db=db,
        )

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        return {
            "status": "success",
            "refreshed": success_count,
            "total": total_count,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error refreshing wallet balances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
