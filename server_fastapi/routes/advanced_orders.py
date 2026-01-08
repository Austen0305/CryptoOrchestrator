"""
Advanced Orders API Routes
Handles stop-loss, take-profit, trailing stops, and OCO orders
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..dependencies.advanced_orders import get_advanced_orders_service
from ..dependencies.auth import get_current_user
from ..services.trading.advanced_orders import AdvancedOrdersService
from ..utils.route_helpers import _get_user_id

# Exchange services removed - using blockchain/DEX only

logger = logging.getLogger(__name__)

router = APIRouter()


class StopLossOrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair (e.g., BTC/USD)")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    amount: float = Field(..., gt=0, description="Order amount")
    stop_price: float = Field(..., gt=0, description="Stop price")
    limit_price: float | None = Field(
        None, gt=0, description="Optional limit price for stop-limit orders"
    )
    chain_id: int = Field(
        default=1, description="Blockchain chain ID (1=Ethereum, 8453=Base, etc.)"
    )
    mode: str = Field(
        default="paper", pattern="^(paper|real)$", description="Trading mode"
    )


class TakeProfitOrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    amount: float = Field(..., gt=0, description="Order amount")
    take_profit_price: float = Field(..., gt=0, description="Take profit price")
    limit_price: float | None = Field(None, gt=0, description="Optional limit price")
    chain_id: int = Field(
        default=1, description="Blockchain chain ID (1=Ethereum, 8453=Base, etc.)"
    )
    mode: str = Field(
        default="paper", pattern="^(paper|real)$", description="Trading mode"
    )


class TrailingStopOrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    amount: float = Field(..., gt=0, description="Order amount")
    trailing_stop_percent: float | None = Field(
        None, gt=0, le=100, description="Trailing stop percentage"
    )
    trailing_stop_amount: float | None = Field(
        None, gt=0, description="Trailing stop fixed amount"
    )
    chain_id: int = Field(
        default=1, description="Blockchain chain ID (1=Ethereum, 8453=Base, etc.)"
    )
    mode: str = Field(
        default="paper", pattern="^(paper|real)$", description="Trading mode"
    )


class OCOOrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    amount: float = Field(..., gt=0, description="Order amount")
    stop_price: float = Field(..., gt=0, description="Stop-loss price")
    take_profit_price: float = Field(..., gt=0, description="Take-profit price")
    chain_id: int = Field(
        default=1, description="Blockchain chain ID (1=Ethereum, 8453=Base, etc.)"
    )
    mode: str = Field(
        default="paper", pattern="^(paper|real)$", description="Trading mode"
    )


@router.post("/stop-loss", response_model=dict)
async def create_stop_loss_order(
    request: StopLossOrderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[AdvancedOrdersService, Depends(get_advanced_orders_service)],
):
    """Create a stop-loss order"""
    try:
        user_id = _get_user_id(current_user)
        order = await service.create_stop_loss_order(
            user_id=int(user_id),
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            stop_price=request.stop_price,
            limit_price=request.limit_price,
            chain_id=request.chain_id,
            mode=request.mode,
        )

        return {
            "id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "order_type": order.order_type,
            "status": order.status,
            "stop_price": order.stop_price,
            "amount": order.amount,
        }
    except Exception as e:
        logger.error(f"Error creating stop-loss order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/take-profit", response_model=dict)
async def create_take_profit_order(
    request: TakeProfitOrderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[AdvancedOrdersService, Depends(get_advanced_orders_service)],
):
    """Create a take-profit order"""
    try:
        user_id = _get_user_id(current_user)
        order = await service.create_take_profit_order(
            user_id=int(user_id),
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            take_profit_price=request.take_profit_price,
            limit_price=request.limit_price,
            chain_id=request.chain_id,
            mode=request.mode,
        )

        return {
            "id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "order_type": order.order_type,
            "status": order.status,
            "take_profit_price": order.take_profit_price,
            "amount": order.amount,
        }
    except Exception as e:
        logger.error(f"Error creating take-profit order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trailing-stop", response_model=dict)
async def create_trailing_stop_order(
    request: TrailingStopOrderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[AdvancedOrdersService, Depends(get_advanced_orders_service)],
):
    """Create a trailing stop order"""
    try:
        user_id = _get_user_id(current_user)

        if not request.trailing_stop_percent and not request.trailing_stop_amount:
            raise HTTPException(
                status_code=400,
                detail="Either trailing_stop_percent or trailing_stop_amount must be provided",
            )
        order = await service.create_trailing_stop_order(
            user_id=int(user_id),
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            trailing_stop_percent=request.trailing_stop_percent,
            trailing_stop_amount=request.trailing_stop_amount,
            chain_id=request.chain_id,
            mode=request.mode,
        )

        return {
            "id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "order_type": order.order_type,
            "status": order.status,
            "trailing_stop_percent": order.trailing_stop_percent,
            "trailing_stop_amount": order.trailing_stop_amount,
            "amount": order.amount,
        }
    except Exception as e:
        logger.error(f"Error creating trailing stop order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oco", response_model=dict)
async def create_oco_order(
    request: OCOOrderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[AdvancedOrdersService, Depends(get_advanced_orders_service)],
):
    """Create an OCO (One-Cancels-Other) order"""
    try:
        user_id = _get_user_id(current_user)
        orders = await service.create_oco_order(
            user_id=int(user_id),
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            stop_price=request.stop_price,
            take_profit_price=request.take_profit_price,
            chain_id=request.chain_id,
            mode=request.mode,
        )

        return {
            "stop_loss_order": {
                "id": orders[0].id,
                "symbol": orders[0].symbol,
                "stop_price": orders[0].stop_price,
            },
            "take_profit_order": {
                "id": orders[1].id,
                "symbol": orders[1].symbol,
                "take_profit_price": orders[1].take_profit_price,
            },
        }
    except Exception as e:
        logger.error(f"Error creating OCO order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[dict])
async def get_advanced_orders(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[AdvancedOrdersService, Depends(get_advanced_orders_service)],
    symbol: str | None = Query(None, description="Filter by symbol"),
    status: str | None = Query(None, description="Filter by status"),
):
    """Get all advanced orders for the current user"""
    try:
        user_id = _get_user_id(current_user)

        # ✅ Use repository through service (service has repository injected)
        # Filter by advanced order types
        advanced_types = [
            "stop",
            "stop_limit",
            "take_profit",
            "take_profit_limit",
            "trailing_stop",
            "trailing_stop_limit",
        ]
        orders = await service.order_repository.get_by_user(
            service.db, int(user_id), status=status, symbol=symbol
        )

        # Filter by advanced order types (repository doesn't filter by order_type yet)
        orders = [o for o in orders if o.order_type in advanced_types]

        return [
            {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "order_type": order.order_type,
                "status": order.status,
                "amount": order.amount,
                "price": order.price,
                "stop_price": order.stop_price,
                "take_profit_price": order.take_profit_price,
                "trailing_stop_percent": order.trailing_stop_percent,
                "trailing_stop_amount": order.trailing_stop_amount,
                "created_at": (
                    order.created_at.isoformat() if order.created_at else None
                ),
            }
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error fetching advanced orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
