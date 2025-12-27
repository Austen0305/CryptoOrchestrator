"""
Advanced Risk Management API Routes

Provides endpoints for professional risk management:
- Position sizing calculations (Kelly, Fixed Fractional, Volatility-based)
- Value at Risk (VaR) calculations (Historical, Parametric, Monte Carlo)
- Risk limit checking
- Portfolio risk analysis
- Stop-loss and take-profit recommendations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import numpy as np

from server_fastapi.services.advanced_risk_management import (
    AdvancedRiskManager,
    PositionSizingMethod,
    VaRMethod,
    RiskLimits,
)

router = APIRouter()

# Global risk manager instance
risk_manager = AdvancedRiskManager()


class PositionSizingRequest(BaseModel):
    """Request for position sizing calculation."""

    method: str = Field(
        ...,
        description="Position sizing method: fixed_fractional, kelly_criterion, volatility_based",
    )
    account_balance: float = Field(..., gt=0, description="Current account balance")
    risk_per_trade: float = Field(
        ..., gt=0, le=1, description="Risk per trade as decimal (e.g., 0.02 for 2%)"
    )
    entry_price: float = Field(..., gt=0, description="Planned entry price")
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    win_rate: Optional[float] = Field(
        None, ge=0, le=1, description="Historical win rate (for Kelly)"
    )
    avg_win: Optional[float] = Field(None, description="Average win amount (for Kelly)")
    avg_loss: Optional[float] = Field(
        None, description="Average loss amount (for Kelly)"
    )
    volatility: Optional[float] = Field(
        None, description="Asset volatility (for volatility-based)"
    )


class PositionSizingResponse(BaseModel):
    """Response for position sizing calculation."""

    position_size: float
    position_value: float
    risk_amount: float
    risk_percentage: float
    method_used: str


class VaRRequest(BaseModel):
    """Request for VaR calculation."""

    returns: List[float] = Field(..., description="Historical returns array")
    confidence_level: float = Field(
        0.95, ge=0.9, le=0.99, description="Confidence level (0.95 or 0.99)"
    )
    method: str = Field(
        "historical", description="VaR method: historical, parametric, monte_carlo"
    )
    portfolio_value: float = Field(..., gt=0, description="Current portfolio value")


class VaRResponse(BaseModel):
    """Response for VaR calculation."""

    var: float
    expected_shortfall: float
    confidence_level: float
    method_used: str
    interpretation: str


class RiskLimitsRequest(BaseModel):
    """Request for custom risk limits."""

    max_position_size: Optional[float] = Field(
        0.20, description="Max position size as % of portfolio"
    )
    max_total_exposure: Optional[float] = Field(1.0, description="Max total exposure")
    max_leverage: Optional[float] = Field(3.0, description="Max leverage")
    max_daily_loss: Optional[float] = Field(0.05, description="Max daily loss %")
    max_drawdown: Optional[float] = Field(0.20, description="Max drawdown %")


class Position(BaseModel):
    """Position model."""

    symbol: str
    size: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    value: Optional[float] = None
    unrealized_pnl: Optional[float] = None


class RiskCheckRequest(BaseModel):
    """Request for risk limit check."""

    positions: List[Position]
    account_balance: float


class StopLossRequest(BaseModel):
    """Request for stop loss calculation."""

    entry_price: float = Field(..., gt=0)
    atr: float = Field(..., gt=0, description="Average True Range")
    atr_multiplier: float = Field(2.0, gt=0, description="ATR multiplier (default 2x)")
    max_loss_pct: float = Field(
        0.02, gt=0, le=0.1, description="Max loss % (default 2%)"
    )


@router.post("/position-size", response_model=PositionSizingResponse)
async def calculate_position_size(request: PositionSizingRequest):
    """Calculate optimal position size using various methods.

    **Methods:**
    - `fixed_fractional`: Classic fixed percentage risk per trade
    - `kelly_criterion`: Optimal f based on win rate and avg win/loss
    - `volatility_based`: Adjust size based on asset volatility
    """
    try:
        # Parse method
        try:
            method = PositionSizingMethod(request.method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid method. Must be one of: {[m.value for m in PositionSizingMethod]}",
            )

        # Calculate position size
        position_size = risk_manager.calculate_position_size(
            method=method,
            account_balance=request.account_balance,
            risk_per_trade=request.risk_per_trade,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            win_rate=request.win_rate,
            avg_win=request.avg_win,
            avg_loss=request.avg_loss,
            volatility=request.volatility,
        )

        position_value = position_size * request.entry_price
        risk_amount = abs((request.entry_price - request.stop_loss) * position_size)
        risk_percentage = (
            (risk_amount / request.account_balance) * 100
            if request.account_balance > 0
            else 0
        )

        return PositionSizingResponse(
            position_size=position_size,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_percentage=risk_percentage,
            method_used=method.value,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating position size: {str(e)}"
        )


@router.post("/var", response_model=VaRResponse)
async def calculate_var(request: VaRRequest):
    """Calculate Value at Risk (VaR) and Expected Shortfall (ES).

    **Methods:**
    - `historical`: Historical simulation (no distribution assumptions)
    - `parametric`: Assumes normal distribution
    - `monte_carlo`: Monte Carlo simulation with 10,000 runs

    **Returns:**
    - VaR: Maximum expected loss at given confidence level
    - Expected Shortfall (CVaR): Average loss beyond VaR threshold
    """
    try:
        # Parse method
        try:
            method = VaRMethod(request.method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid method. Must be one of: {[m.value for m in VaRMethod]}",
            )

        # Convert returns to numpy array
        returns_array = np.array(request.returns)

        # Calculate VaR
        var, expected_shortfall = risk_manager.calculate_var(
            returns=returns_array,
            confidence_level=request.confidence_level,
            method=method,
            portfolio_value=request.portfolio_value,
        )

        # Generate interpretation
        confidence_pct = request.confidence_level * 100
        interpretation = (
            f"With {confidence_pct}% confidence, the portfolio will not lose more than "
            f"${var:,.2f} in a single day. If losses exceed VaR, the expected loss is ${expected_shortfall:,.2f}."
        )

        return VaRResponse(
            var=var,
            expected_shortfall=expected_shortfall,
            confidence_level=request.confidence_level,
            method_used=method.value,
            interpretation=interpretation,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating VaR: {str(e)}")


@router.post("/stop-loss")
async def calculate_stop_loss(request: StopLossRequest):
    """Calculate optimal stop loss using ATR."""
    try:
        stop_loss = risk_manager.calculate_optimal_stop_loss(
            entry_price=request.entry_price,
            atr=request.atr,
            atr_multiplier=request.atr_multiplier,
            max_loss_pct=request.max_loss_pct,
        )

        risk_amount = abs(request.entry_price - stop_loss)

        return {
            "stop_loss": stop_loss,
            "risk_amount": risk_amount,
            "risk_percentage": (risk_amount / request.entry_price) * 100,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating stop loss: {str(e)}"
        )


@router.post("/take-profit")
async def calculate_take_profit(
    entry_price: float, stop_loss: float, risk_reward_ratio: float = 2.0
):
    """Calculate optimal take profit based on risk-reward ratio."""
    try:
        take_profit = risk_manager.calculate_optimal_take_profit(
            entry_price=entry_price,
            stop_loss=stop_loss,
            risk_reward_ratio=risk_reward_ratio,
        )

        risk_amount = abs(entry_price - stop_loss)
        reward_amount = abs(take_profit - entry_price)

        return {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_amount": risk_amount,
            "reward_amount": reward_amount,
            "risk_reward_ratio": risk_reward_ratio,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating take profit: {str(e)}"
        )


@router.get("/risk-limits")
async def get_current_risk_limits():
    """Get current risk management limits."""
    limits = risk_manager.risk_limits

    return {
        "max_position_size": f"{limits.max_position_size:.1%}",
        "max_total_exposure": f"{limits.max_total_exposure:.1%}",
        "max_leverage": f"{limits.max_leverage:.1f}x",
        "max_daily_loss": f"{limits.max_daily_loss:.1%}",
        "max_drawdown": f"{limits.max_drawdown:.1%}",
        "max_correlation": f"{limits.max_correlation:.1%}",
        "min_liquidity_ratio": f"{limits.min_liquidity_ratio:.1%}",
    }
