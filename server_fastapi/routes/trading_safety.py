"""
Trading Safety API Routes
Exposes trading safety service functionality via REST API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from server_fastapi.services.trading.trading_safety_service import get_trading_safety_service

router = APIRouter()
logger = logging.getLogger(__name__)


class TradeValidationRequest(BaseModel):
    """Request model for trade validation."""
    symbol: str = Field(..., example="BTC/USDT", description="Trading pair")
    side: str = Field(..., example="buy", description="Trade side (buy/sell)")
    quantity: float = Field(..., gt=0, example=0.1, description="Trade quantity")
    price: float = Field(..., gt=0, example=50000.0, description="Expected price")
    account_balance: float = Field(..., gt=0, example=10000.0, description="Current account balance in USD")
    current_positions: Dict[str, Dict[str, Any]] = Field(
        default={},
        example={"BTC/USDT": {"value": 1000.0, "quantity": 0.02}},
        description="Current open positions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "side": "buy",
                "quantity": 0.1,
                "price": 50000.0,
                "account_balance": 10000.0,
                "current_positions": {
                    "BTC/USDT": {"value": 1000.0, "quantity": 0.02},
                    "ETH/USDT": {"value": 500.0, "quantity": 0.15}
                }
            }
        }


class TradeValidationResponse(BaseModel):
    """Response model for trade validation."""
    valid: bool
    reason: str
    adjustments: Optional[Dict[str, Any]] = None


class SlippageCheckRequest(BaseModel):
    """Request model for slippage check."""
    expected_price: float = Field(..., gt=0, example=50000.0)
    actual_price: float = Field(..., gt=0, example=50100.0)
    side: str = Field(..., example="buy", description="Trade side (buy/sell)")


class SlippageCheckResponse(BaseModel):
    """Response model for slippage check."""
    acceptable: bool
    slippage_pct: float
    slippage_value: float
    reason: str


class TradeResultRequest(BaseModel):
    """Request model for recording trade result."""
    trade_id: str = Field(..., example="trade_12345")
    pnl: float = Field(..., example=150.0, description="Profit/loss in USD")
    symbol: str = Field(..., example="BTC/USDT")
    side: str = Field(..., example="buy")
    quantity: float = Field(..., gt=0, example=0.1)
    price: float = Field(..., gt=0, example=50000.0)


class SafetyStatusResponse(BaseModel):
    """Response model for safety status."""
    kill_switch_active: bool
    kill_switch_reason: Optional[str]
    daily_pnl: float
    trades_today: int
    consecutive_losses: int
    last_reset: str
    configuration: Dict[str, Any]


class ConfigurationUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    max_position_size_pct: Optional[float] = Field(None, gt=0, le=1.0)
    daily_loss_limit_pct: Optional[float] = Field(None, gt=0, le=1.0)
    max_consecutive_losses: Optional[int] = Field(None, gt=0)
    min_account_balance: Optional[float] = Field(None, gt=0)
    max_slippage_pct: Optional[float] = Field(None, gt=0, le=1.0)
    max_portfolio_heat: Optional[float] = Field(None, gt=0, le=1.0)


@router.post("/validate", response_model=TradeValidationResponse)
async def validate_trade(request: TradeValidationRequest):
    """
    Validate a trade before execution.
    
    Checks:
    - Kill switch status
    - Minimum balance
    - Position size limits
    - Daily loss limits
    - Consecutive loss limits
    - Portfolio heat
    
    Returns validation result with approval or rejection reason.
    """
    try:
        safety_service = get_trading_safety_service()
        
        result = safety_service.validate_trade(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            account_balance=request.account_balance,
            current_positions=request.current_positions
        )
        
        return TradeValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error validating trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-slippage", response_model=SlippageCheckResponse)
async def check_slippage(request: SlippageCheckRequest):
    """
    Check if slippage is within acceptable limits.
    
    Compares expected vs actual execution price and determines
    if the slippage is acceptable based on configured threshold.
    """
    try:
        safety_service = get_trading_safety_service()
        
        result = safety_service.check_slippage(
            expected_price=request.expected_price,
            actual_price=request.actual_price,
            side=request.side
        )
        
        return SlippageCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Error checking slippage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-trade")
async def record_trade_result(request: TradeResultRequest):
    """
    Record a trade result for safety tracking.
    
    Updates daily P&L, consecutive losses, and other safety metrics.
    May trigger kill switch if limits are exceeded.
    """
    try:
        safety_service = get_trading_safety_service()
        
        safety_service.record_trade_result(
            trade_id=request.trade_id,
            pnl=request.pnl,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price
        )
        
        # Return updated status
        status = safety_service.get_safety_status()
        
        return {
            "success": True,
            "message": "Trade result recorded",
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error recording trade result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SafetyStatusResponse)
async def get_safety_status():
    """
    Get current safety system status.
    
    Returns:
    - Kill switch status
    - Daily P&L
    - Trades today
    - Consecutive losses
    - Configuration
    """
    try:
        safety_service = get_trading_safety_service()
        status = safety_service.get_safety_status()
        
        return SafetyStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting safety status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-kill-switch")
async def reset_kill_switch(admin_override: bool = False):
    """
    Reset the kill switch.
    
    Requires admin override or new trading day.
    Use with caution - only reset after investigating why it was triggered.
    """
    try:
        safety_service = get_trading_safety_service()
        
        result = safety_service.reset_kill_switch(admin_override=admin_override)
        
        if not result['success']:
            raise HTTPException(status_code=403, detail=result['reason'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting kill switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/configuration")
async def update_configuration(request: ConfigurationUpdateRequest):
    """
    Update safety configuration.
    
    All parameters are optional. Only provided parameters will be updated.
    Use with caution - incorrect values can increase risk.
    """
    try:
        safety_service = get_trading_safety_service()
        
        # Convert request to dict, excluding None values
        config_updates = {
            k: v for k, v in request.dict().items() if v is not None
        }
        
        if not config_updates:
            raise HTTPException(
                status_code=400,
                detail="No configuration updates provided"
            )
        
        result = safety_service.update_configuration(config_updates)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for safety service."""
    try:
        safety_service = get_trading_safety_service()
        status = safety_service.get_safety_status()
        
        return {
            "status": "healthy",
            "kill_switch_active": status['kill_switch_active'],
            "service": "trading_safety"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "trading_safety"
        }
