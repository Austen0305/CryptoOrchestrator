"""
DEX Trading Routes
Endpoints for decentralized exchange trading via aggregators
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.real_money_transaction_manager import real_money_transaction_manager
from ..services.trading.dex_trading_service import DEXTradingService
from ..utils.route_helpers import _get_user_id
from ..utils.validation_2026 import (
    ValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class DEXQuoteRequest(BaseModel):
    """Request model for getting a DEX quote"""

    sell_token: str = Field(..., description="Token to sell (address or symbol)")
    buy_token: str = Field(..., description="Token to buy (address or symbol)")
    sell_amount: str | None = Field(None, description="Amount to sell (in token units)")
    buy_amount: str | None = Field(
        None, description="Amount to buy (alternative to sell_amount)"
    )
    chain_id: int = Field(
        1, description="Source blockchain ID (1=Ethereum, 8453=Base, etc.)"
    )
    slippage_percentage: float = Field(
        0.5, ge=0, le=50, description="Max slippage percentage"
    )
    cross_chain: bool = Field(False, description="Whether this is a cross-chain swap")
    to_chain_id: int | None = Field(
        None, description="Destination chain ID (for cross-chain)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                "buy_token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "sell_amount": "1000000000",  # 1000 USDC (6 decimals)
                "chain_id": 1,
                "slippage_percentage": 0.5,
            }
        }
    }


class DEXSwapRequest(BaseModel):
    """Request model for executing a DEX swap"""

    sell_token: str = Field(..., description="Token to sell")
    buy_token: str = Field(..., description="Token to buy")
    sell_amount: str = Field(..., description="Amount to sell (in token units)")
    chain_id: int = Field(1, description="Source blockchain ID")
    slippage_percentage: float = Field(
        0.5, ge=0, le=50, description="Max slippage percentage"
    )
    custodial: bool = Field(
        True,
        description="Whether to use custodial wallet (True) or user wallet (False)",
    )
    user_wallet_address: str | None = Field(
        None, description="User wallet address (for non-custodial)"
    )
    signature: str | None = Field(
        None, description="EIP-712 signature (for non-custodial authorization)"
    )
    cross_chain: bool = Field(False, description="Whether this is a cross-chain swap")
    to_chain_id: int | None = Field(
        None, description="Destination chain ID (for cross-chain)"
    )
    idempotency_key: str = Field(
        ..., description="Unique key to prevent duplicate swaps"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                "buy_token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "sell_amount": "1000000000",  # 1000 USDC
                "chain_id": 1,
                "slippage_percentage": 0.5,
                "custodial": True,
            }
        }
    }


class DEXQuoteResponse(BaseModel):
    """Response model for DEX quote"""

    aggregator: str
    sell_token: str
    buy_token: str
    sell_amount: str | None
    buy_amount: str | None
    price: float | None
    estimated_gas: str | None
    sources: list[dict[str, Any]] | None
    chain_id: int
    to_chain_id: int | None = None

    model_config = {"from_attributes": True}


class DEXSwapResponse(BaseModel):
    """Response model for DEX swap execution"""

    success: bool
    trade_id: str | None = None
    sell_token: str
    buy_token: str
    sell_amount: str
    buy_amount: str | None
    fee_amount: str | None
    aggregator: str
    transaction_hash: str | None = None
    swap_calldata: dict[str, Any] | None = None
    chain_id: int
    status: str

    model_config = {"from_attributes": True}


class SupportedChain(BaseModel):
    """Model for supported blockchain"""

    chain_id: int
    name: str
    symbol: str

    model_config = {"from_attributes": True}


# Dependency to get DEX trading service
def get_dex_trading_service() -> DEXTradingService:
    """Dependency to get DEX trading service instance"""
    return DEXTradingService()


@router.post("/quote", response_model=DEXQuoteResponse, tags=["DEX Trading"])
@cached(
    ttl=10, prefix="dex_quote"
)  # 10s TTL for DEX quotes (very short due to volatility)
async def get_dex_quote(
    request: DEXQuoteRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXTradingService, Depends(get_dex_trading_service)],
) -> DEXQuoteResponse:
    """
    Get a quote for a DEX swap from the best aggregator

    Compares quotes from multiple DEX aggregators (0x, OKX, Rubic)
    and returns the best price.
    """
    try:
        if not request.sell_amount and not request.buy_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either sell_amount or buy_amount must be provided",
            )

        quote = await service.get_quote(
            sell_token=request.sell_token,
            buy_token=request.buy_token,
            sell_amount=request.sell_amount,
            buy_amount=request.buy_amount,
            chain_id=request.chain_id,
            slippage_percentage=request.slippage_percentage,
            user_wallet_address=None,  # Quote doesn't need wallet address
            cross_chain=request.cross_chain,
            to_chain_id=request.to_chain_id,
        )

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to get quote from DEX aggregators",
            )

        # Extract price if available
        price = None
        if "buyAmount" in quote and "sellAmount" in quote:
            try:
                buy_amount = float(quote["buyAmount"])
                sell_amount = float(quote["sellAmount"])
                if sell_amount > 0:
                    price = buy_amount / sell_amount
            except (ValueError, TypeError):
                pass

        return DEXQuoteResponse(
            aggregator=quote.get("aggregator", "unknown"),
            sell_token=request.sell_token,
            buy_token=request.buy_token,
            sell_amount=request.sell_amount or quote.get("sellAmount"),
            buy_amount=request.buy_amount or quote.get("buyAmount"),
            price=price,
            estimated_gas=quote.get("estimatedGas") or quote.get("gas"),
            sources=quote.get("sources") or quote.get("routes"),
            chain_id=quote.get("chain_id", request.chain_id),
            to_chain_id=quote.get("to_chain_id") if request.cross_chain else None,
        )

    except (HTTPException, ValidationError):
        raise
    except ValueError as e:
        # Validation errors from validation utilities
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(
            f"Error getting DEX quote: {e}",
            exc_info=True,
            extra={
                "user_id": _get_user_id(current_user),
                "sell_token": request.sell_token,
                "buy_token": request.buy_token,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting quote",
        )


@router.post("/swap", response_model=DEXSwapResponse, tags=["DEX Trading"])
async def execute_dex_swap(
    request: DEXSwapRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXTradingService, Depends(get_dex_trading_service)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    http_request: Request,  # For IP extraction
) -> DEXSwapResponse:
    """
    Execute a DEX swap (custodial or non-custodial)

    - **Custodial**: Platform executes swap on behalf of user (requires deposit)
    - **Non-custodial**: Returns swap calldata for user to execute from their wallet

    For real money trades, IP whitelisting is enforced if enabled.
    """
    try:
        user_id = _get_user_id(current_user)

        # Check IP whitelist for real money trades (if custodial swap)
        if request.custodial:
            try:
                from ..services.security.ip_whitelist_service import (
                    ip_whitelist_service,
                )

                # Check if this is a real money trade
                # In production, you'd check trading mode from user settings
                # For now, assume custodial swaps are real money
                whitelist = await ip_whitelist_service.get_whitelist(int(user_id))
                if whitelist and len(whitelist) > 0:
                    # IP whitelisting is enabled - verify IP
                    client_ip = (
                        http_request.client.host if http_request.client else None
                    )
                    if client_ip:
                        is_whitelisted = await ip_whitelist_service.is_ip_whitelisted(
                            int(user_id), client_ip
                        )
                        if not is_whitelisted:
                            logger.warning(
                                f"IP whitelist violation for user {user_id}, IP {client_ip}",
                                extra={
                                    "user_id": user_id,
                                    "ip": client_ip,
                                    "endpoint": "/api/dex/swap",
                                },
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"IP address {client_ip} is not whitelisted. Please add it to your IP whitelist to execute real money trades.",
                            )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"IP whitelist check failed (may not be enabled): {e}")

        if request.custodial:
            # Execute custodial swap with idempotency enforcement
            async def operation(db_session):
                return await service.execute_custodial_swap(
                    user_id=str(user_id),
                    sell_token=request.sell_token,
                    buy_token=request.buy_token,
                    sell_amount=request.sell_amount,
                    chain_id=request.chain_id,
                    slippage_percentage=request.slippage_percentage,
                    db=db_session,
                )

            result = await real_money_transaction_manager.execute_idempotent_operation(
                idempotency_key=request.idempotency_key,
                user_id=int(user_id),
                operation_name="dex_swap_custodial",
                operation=operation,
                operation_details={
                    "sell_token": request.sell_token,
                    "buy_token": request.buy_token,
                    "sell_amount": request.sell_amount,
                    "chain_id": request.chain_id,
                },
            )

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to execute custodial swap",
                )

            return DEXSwapResponse(
                success=result.get("success", False),
                trade_id=result.get("trade_id"),
                sell_token=result.get("sell_token"),
                buy_token=result.get("buy_token"),
                sell_amount=result.get("sell_amount"),
                buy_amount=result.get("buy_amount"),
                fee_amount=result.get("fee_amount"),
                aggregator=result.get("aggregator"),
                transaction_hash=result.get("transaction_hash"),
                chain_id=request.chain_id,
                status=result.get("status", "pending"),
            )

        else:
            # Prepare non-custodial swap
            if not request.user_wallet_address:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_wallet_address is required for non-custodial swaps",
                )

            result = await service.prepare_non_custodial_swap(
                user_id=str(user_id),
                sell_token=request.sell_token,
                buy_token=request.buy_token,
                sell_amount=request.sell_amount,
                chain_id=request.chain_id,
                slippage_percentage=request.slippage_percentage,
                user_wallet_address=request.user_wallet_address,
                signature=request.signature,
            )

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to prepare non-custodial swap",
                )

            return DEXSwapResponse(
                success=result.get("success", False),
                sell_token=result.get("sell_token"),
                buy_token=result.get("buy_token"),
                sell_amount=result.get("sell_amount"),
                buy_amount=result.get("buy_amount"),
                fee_amount=result.get("fee_amount"),
                aggregator=result.get("aggregator"),
                swap_calldata=result.get("swap_calldata"),
                chain_id=result.get("chain_id", request.chain_id),
                status="ready",
            )

    except (HTTPException, ValidationError):
        raise
    except ValueError as e:
        # Validation errors from validation utilities
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(
            f"Error executing DEX swap: {e}",
            exc_info=True,
            extra={
                "user_id": user_id,
                "sell_token": request.sell_token,
                "buy_token": request.buy_token,
                "custodial": request.custodial,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while executing swap",
        )


@router.get(
    "/supported-chains", response_model=list[SupportedChain], tags=["DEX Trading"]
)
async def get_supported_chains(
    service: Annotated[DEXTradingService, Depends(get_dex_trading_service)],
) -> list[SupportedChain]:
    """
    Get list of supported blockchain networks

    Returns all chains supported by at least one DEX aggregator.
    """
    try:
        chains = await service.get_supported_chains()

        return [
            SupportedChain(
                chain_id=chain.get("chainId"),
                name=chain.get("name"),
                symbol=chain.get("symbol"),
            )
            for chain in chains
        ]

    except Exception as e:
        logger.error(f"Error getting supported chains: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting supported chains",
        )


class DEXTradeStatusResponse(BaseModel):
    """Response model for DEX trade status"""

    trade_id: int
    transaction_hash: str
    status: str
    success: bool | None = None
    block_number: int | None = None
    confirmations: int | None = None
    gas_used: int | None = None
    message: str | None = None

    model_config = {"from_attributes": True}


@router.get(
    "/trades/{trade_id}/status",
    response_model=DEXTradeStatusResponse,
    tags=["DEX Trading"],
)
async def get_dex_trade_status(
    trade_id: int,
    chain_id: int,
    transaction_hash: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXTradingService, Depends(get_dex_trading_service)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DEXTradeStatusResponse:
    """
    Get status of a DEX trade transaction

    Queries the blockchain for transaction status and updates the trade record.
    """
    try:
        _get_user_id(current_user)

        # Get swap status from service
        status_result = await service.get_swap_status(
            trade_id=trade_id,
            chain_id=chain_id,
            transaction_hash=transaction_hash,
            db=db,
        )

        if not status_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade not found",
            )

        return DEXTradeStatusResponse(
            trade_id=trade_id,
            transaction_hash=transaction_hash,
            status=status_result.get("status", "unknown"),
            success=status_result.get("success"),
            block_number=status_result.get("block_number"),
            confirmations=status_result.get("confirmations"),
            gas_used=status_result.get("gas_used"),
            message=status_result.get("message"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DEX trade status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting trade status",
        )
