"""
Stop-Loss and Take-Profit API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from server_fastapi.services.trading.sl_tp_service import get_sl_tp_service, OrderType
from server_fastapi.services.trading.price_monitor import get_price_monitor

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateStopLossRequest(BaseModel):
    """Request model for creating stop-loss order."""
    position_id: str = Field(..., description="Unique position identifier")
    symbol: str = Field(..., example="BTC/USDT")
    side: str = Field(..., example="buy", description="Original trade side")
    quantity: float = Field(..., gt=0, example=0.1)
    entry_price: float = Field(..., gt=0, example=50000.0)
    stop_loss_pct: float = Field(..., gt=0, le=1, example=0.02, description="Stop-loss percentage (0.02 = 2%)")
    user_id: str = Field(..., description="User identifier")
    bot_id: Optional[str] = Field(None, description="Optional bot identifier")


class CreateTakeProfitRequest(BaseModel):
    """Request model for creating take-profit order."""
    position_id: str = Field(..., description="Unique position identifier")
    symbol: str = Field(..., example="BTC/USDT")
    side: str = Field(..., example="buy", description="Original trade side")
    quantity: float = Field(..., gt=0, example=0.1)
    entry_price: float = Field(..., gt=0, example=50000.0)
    take_profit_pct: float = Field(..., gt=0, le=1, example=0.05, description="Take-profit percentage (0.05 = 5%)")
    user_id: str = Field(..., description="User identifier")
    bot_id: Optional[str] = Field(None, description="Optional bot identifier")


class CreateTrailingStopRequest(BaseModel):
    """Request model for creating trailing stop order."""
    position_id: str = Field(..., description="Unique position identifier")
    symbol: str = Field(..., example="BTC/USDT")
    side: str = Field(..., example="buy", description="Original trade side")
    quantity: float = Field(..., gt=0, example=0.1)
    entry_price: float = Field(..., gt=0, example=50000.0)
    trailing_pct: float = Field(..., gt=0, le=1, example=0.03, description="Trailing percentage (0.03 = 3%)")
    user_id: str = Field(..., description="User identifier")
    bot_id: Optional[str] = Field(None, description="Optional bot identifier")


class CheckTriggersRequest(BaseModel):
    """Request model for checking order triggers."""
    current_prices: Dict[str, float] = Field(
        ...,
        example={"BTC/USDT": 51000.0, "ETH/USDT": 3000.0},
        description="Current prices for symbols"
    )


@router.post("/stop-loss")
async def create_stop_loss(request: CreateStopLossRequest):
    """
    Create a stop-loss order for a position.
    
    The stop-loss will automatically trigger when the price moves against the position
    by the specified percentage.
    """
    try:
        service = get_sl_tp_service()
        
        order = service.create_stop_loss(
            position_id=request.position_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            entry_price=request.entry_price,
            stop_loss_pct=request.stop_loss_pct,
            user_id=request.user_id,
            bot_id=request.bot_id
        )
        
        return {
            "success": True,
            "order": order,
            "message": f"Stop-loss created at ${order['trigger_price']:.2f}"
        }
        
    except Exception as e:
        logger.error(f"Error creating stop-loss: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/take-profit")
async def create_take_profit(request: CreateTakeProfitRequest):
    """
    Create a take-profit order for a position.
    
    The take-profit will automatically trigger when the price moves in favor of the position
    by the specified percentage.
    """
    try:
        service = get_sl_tp_service()
        
        order = service.create_take_profit(
            position_id=request.position_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            entry_price=request.entry_price,
            take_profit_pct=request.take_profit_pct,
            user_id=request.user_id,
            bot_id=request.bot_id
        )
        
        return {
            "success": True,
            "order": order,
            "message": f"Take-profit created at ${order['trigger_price']:.2f}"
        }
        
    except Exception as e:
        logger.error(f"Error creating take-profit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trailing-stop")
async def create_trailing_stop(request: CreateTrailingStopRequest):
    """
    Create a trailing stop-loss order for a position.
    
    The trailing stop will move with the price in your favor, locking in profits
    while protecting against reversals.
    """
    try:
        service = get_sl_tp_service()
        
        order = service.create_trailing_stop(
            position_id=request.position_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            entry_price=request.entry_price,
            trailing_pct=request.trailing_pct,
            user_id=request.user_id,
            bot_id=request.bot_id
        )
        
        return {
            "success": True,
            "order": order,
            "message": f"Trailing stop created, initially at ${order['trigger_price']:.2f}"
        }
        
    except Exception as e:
        logger.error(f"Error creating trailing stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-triggers")
async def check_triggers(request: CheckTriggersRequest):
    """
    Check if any stop-loss/take-profit orders should be triggered.
    
    This should be called periodically (e.g., every second) with current market prices
    to detect triggered orders.
    """
    try:
        service = get_sl_tp_service()
        
        triggered_orders = service.check_triggers(request.current_prices)
        
        return {
            "triggered_count": len(triggered_orders),
            "triggered_orders": triggered_orders
        }
        
    except Exception as e:
        logger.error(f"Error checking triggers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}")
async def cancel_order(order_id: str):
    """Cancel a stop-loss/take-profit order."""
    try:
        service = get_sl_tp_service()
        
        success = service.cancel_order(order_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "success": True,
            "message": f"Order {order_id} cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_orders(
    user_id: Optional[str] = None,
    bot_id: Optional[str] = None
):
    """Get all active stop-loss/take-profit orders."""
    try:
        service = get_sl_tp_service()
        
        orders = service.get_active_orders(user_id=user_id, bot_id=bot_id)
        
        return {
            "count": len(orders),
            "orders": orders
        }
        
    except Exception as e:
        logger.error(f"Error fetching active orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for SL/TP service."""
    try:
        service = get_sl_tp_service()
        orders = service.get_active_orders()
        
        return {
            "status": "healthy",
            "active_orders": len(orders),
            "service": "stop_loss_take_profit"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "stop_loss_take_profit"
        }


@router.post("/monitor/start")
async def start_price_monitoring(check_interval: int = 5):
    """
    Start the price monitoring service.
    
    This service will continuously check market prices and trigger
    stop-loss/take-profit orders automatically.
    
    Args:
        check_interval: How often to check prices (in seconds)
    """
    try:
        monitor = get_price_monitor()
        await monitor.start_monitoring(check_interval=check_interval)
        
        return {
            "success": True,
            "message": f"Price monitoring started (checking every {check_interval}s)",
            "status": monitor.get_monitoring_status()
        }
    except Exception as e:
        logger.error(f"Error starting price monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop")
async def stop_price_monitoring():
    """Stop the price monitoring service."""
    try:
        monitor = get_price_monitor()
        await monitor.stop_monitoring()
        
        return {
            "success": True,
            "message": "Price monitoring stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping price monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status")
async def get_monitoring_status():
    """Get the current status of price monitoring."""
    try:
        monitor = get_price_monitor()
        status = monitor.get_monitoring_status()
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
