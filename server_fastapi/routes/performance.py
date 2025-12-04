"""
Performance Routes - Comprehensive trading performance metrics
Includes Sharpe ratio, Sortino ratio, Max Drawdown, and other professional metrics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
import math

from ..dependencies.auth import get_current_user

# Import cache utilities
try:
    from ..middleware.query_cache import cache_query_result

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

    def cache_query_result(*args, **kwargs):
        """Fallback no-op decorator when cache not available"""

        def decorator(func):
            return func

        return decorator


logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration constants
DEFAULT_INITIAL_CAPITAL = 10000.0  # Default starting capital for calculations
RISK_FREE_RATE = 0.04  # 4% annual risk-free rate (approximate T-bill rate)
TRADING_DAYS_PER_YEAR = 252  # Standard trading days for annualization


class PerformanceSummary(BaseModel):
    """Basic performance summary model"""

    winRate: float = Field(..., description="Win rate as percentage")
    avgProfit: float = Field(..., description="Average profit per trade")
    totalProfit: float = Field(..., description="Total profit/loss")
    bestTrade: float = Field(..., description="Best trade P&L")
    worstTrade: float = Field(..., description="Worst trade P&L")


class AdvancedMetrics(BaseModel):
    """Advanced trading metrics model"""

    # Basic metrics
    totalTrades: int = Field(0, description="Total number of trades")
    winningTrades: int = Field(0, description="Number of winning trades")
    losingTrades: int = Field(0, description="Number of losing trades")
    winRate: float = Field(0.0, description="Win rate as percentage")

    # Profit metrics
    totalProfit: float = Field(0.0, description="Total realized P&L")
    avgProfit: float = Field(0.0, description="Average profit per trade")
    avgWin: float = Field(0.0, description="Average winning trade")
    avgLoss: float = Field(0.0, description="Average losing trade")
    profitFactor: float = Field(0.0, description="Gross profit / Gross loss")

    # Risk-adjusted returns
    sharpeRatio: float = Field(0.0, description="Sharpe ratio (annualized)")
    sortinoRatio: float = Field(0.0, description="Sortino ratio (downside risk)")
    calmarRatio: float = Field(0.0, description="Calmar ratio (return / max drawdown)")

    # Drawdown metrics
    maxDrawdown: float = Field(0.0, description="Maximum drawdown as percentage")
    maxDrawdownAmount: float = Field(0.0, description="Maximum drawdown in currency")
    avgDrawdown: float = Field(0.0, description="Average drawdown as percentage")
    currentDrawdown: float = Field(0.0, description="Current drawdown from peak")

    # Trade quality
    bestTrade: float = Field(0.0, description="Best trade P&L")
    worstTrade: float = Field(0.0, description="Worst trade P&L")
    avgHoldingTime: float = Field(0.0, description="Average trade duration in minutes")

    # Period returns
    dailyReturn: float = Field(0.0, description="Average daily return")
    weeklyReturn: float = Field(0.0, description="Average weekly return")
    monthlyReturn: float = Field(0.0, description="Average monthly return")

    model_config = {
        "json_schema_extra": {
            "example": {
                "totalTrades": 100,
                "winningTrades": 65,
                "losingTrades": 35,
                "winRate": 65.0,
                "totalProfit": 5420.50,
                "avgProfit": 54.21,
                "profitFactor": 2.1,
                "sharpeRatio": 1.8,
                "sortinoRatio": 2.3,
                "maxDrawdown": 12.5,
                "bestTrade": 850.0,
                "worstTrade": -320.0,
            }
        }
    }


class DailyPnL(BaseModel):
    """Daily P&L data point"""

    date: str
    pnl: float
    cumulativePnl: float
    trades: int


class DrawdownPoint(BaseModel):
    """Drawdown data point"""

    date: str
    drawdown: float
    peakEquity: float
    currentEquity: float


@router.get("/summary")
@cache_query_result(
    ttl=60, key_prefix="performance_summary", include_user=True, include_params=True
)
async def get_performance_summary(
    mode: Optional[str] = Query("paper", description="Trading mode: paper or real"),
    current_user: dict = Depends(get_current_user),
) -> PerformanceSummary:
    """
    Get basic performance summary for the current user.

    Returns:
    - Win rate (percentage)
    - Average profit per trade
    - Total profit
    - Best trade (highest profit)
    - Worst trade (lowest profit/largest loss)
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            return PerformanceSummary(
                winRate=0.0,
                avgProfit=0.0,
                totalProfit=0.0,
                bestTrade=0.0,
                worstTrade=0.0,
            )
        
        normalized_mode = "real" if mode == "live" else mode

        from ..database import get_db_context
        from sqlalchemy import select
        from ..models.trade import Trade

        async with get_db_context() as db:
            trades_result = await db.execute(
                select(Trade)
                .where(Trade.user_id == str(user_id))
                .where(Trade.mode == normalized_mode)
            )
            trades = trades_result.scalars().all()

            if not trades:
                return PerformanceSummary(
                    winRate=0.0,
                    avgProfit=0.0,
                    totalProfit=0.0,
                    bestTrade=0.0,
                    worstTrade=0.0,
                )

            total_trades = len(trades)
            winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
            win_rate = (
                (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
            )

            profits = [t.pnl for t in trades if t.pnl is not None]
            total_profit = sum(profits) if profits else 0.0
            avg_profit = (total_profit / len(profits)) if profits else 0.0

            best_trade = max(profits) if profits else 0.0
            worst_trade = min(profits) if profits else 0.0

            return PerformanceSummary(
                winRate=win_rate,
                avgProfit=avg_profit,
                totalProfit=total_profit,
                bestTrade=best_trade,
                worstTrade=worst_trade,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching performance summary: {e}", exc_info=True)
        # Return empty performance summary instead of 500 error for better UX during development
        logger.warning(f"Returning empty performance summary due to error: {e}")
        return PerformanceSummary(
            winRate=0.0,
            avgProfit=0.0,
            totalProfit=0.0,
            bestTrade=0.0,
            worstTrade=0.0,
        )


@router.get("/advanced")
@cache_query_result(
    ttl=120, key_prefix="advanced_metrics", include_user=True, include_params=True
)
async def get_advanced_metrics(
    mode: Optional[str] = Query("paper", description="Trading mode: paper or real"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
) -> AdvancedMetrics:
    """
    Get comprehensive advanced trading metrics.

    Includes professional-grade metrics used by hedge funds:
    - Sharpe Ratio (risk-adjusted return)
    - Sortino Ratio (downside risk-adjusted return)
    - Calmar Ratio (return / max drawdown)
    - Maximum Drawdown (peak-to-trough decline)
    - Profit Factor (gross profits / gross losses)
    """
    try:
        user_id = current_user.get("id")
        normalized_mode = "real" if mode == "live" else mode

        from ..database import get_db_context
        from sqlalchemy import select, and_
        from ..models.trade import Trade

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with get_db_context() as db:
            trades_result = await db.execute(
                select(Trade)
                .where(
                    and_(
                        Trade.user_id == user_id,
                        Trade.mode == normalized_mode,
                        Trade.created_at >= cutoff_date,
                    )
                )
                .order_by(Trade.created_at)
            )
            trades = trades_result.scalars().all()

            if not trades:
                return AdvancedMetrics()

            # Extract P&L values
            profits = [float(t.pnl) for t in trades if t.pnl is not None]
            if not profits:
                return AdvancedMetrics(totalTrades=len(trades))

            # Basic metrics
            total_trades = len(trades)
            winning_profits = [p for p in profits if p > 0]
            losing_profits = [p for p in profits if p < 0]

            winning_trades = len(winning_profits)
            losing_trades = len(losing_profits)
            win_rate = (
                (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            )

            # Profit metrics
            total_profit = sum(profits)
            avg_profit = total_profit / len(profits) if profits else 0.0
            avg_win = (
                sum(winning_profits) / len(winning_profits) if winning_profits else 0.0
            )
            avg_loss = (
                sum(losing_profits) / len(losing_profits) if losing_profits else 0.0
            )

            # Profit factor
            gross_profit = sum(winning_profits) if winning_profits else 0.0
            gross_loss = (
                abs(sum(losing_profits)) if losing_profits else 0.001
            )  # Avoid division by zero
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

            # Calculate returns for risk metrics
            initial_capital = DEFAULT_INITIAL_CAPITAL
            cumulative_pnl = []
            running_total = 0.0
            for p in profits:
                running_total += p
                cumulative_pnl.append(running_total)

            # Calculate returns (as percentage of equity)
            returns = []
            equity = initial_capital
            for p in profits:
                ret = p / equity if equity > 0 else 0.0
                returns.append(ret)
                equity += p

            # Sharpe Ratio (annualized, with risk-free rate)
            # Using configurable trading days per year
            if len(returns) > 1:
                avg_return = sum(returns) / len(returns)
                std_return = math.sqrt(
                    sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
                )
                # Subtract daily risk-free rate from average return
                daily_risk_free = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
                excess_return = avg_return - daily_risk_free
                sharpe_ratio = (
                    (excess_return / std_return * math.sqrt(TRADING_DAYS_PER_YEAR))
                    if std_return > 0
                    else 0.0
                )
            else:
                sharpe_ratio = 0.0

            # Sortino Ratio (using only downside volatility)
            downside_returns = [r for r in returns if r < 0]
            if downside_returns and len(downside_returns) > 1:
                avg_return = sum(returns) / len(returns)
                daily_risk_free = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
                excess_return = avg_return - daily_risk_free
                downside_std = math.sqrt(
                    sum(r**2 for r in downside_returns) / len(downside_returns)
                )
                sortino_ratio = (
                    (excess_return / downside_std * math.sqrt(TRADING_DAYS_PER_YEAR))
                    if downside_std > 0
                    else 0.0
                )
            elif returns:
                # If no downside returns, use 0 (indicates all trades were profitable)
                # Note: A positive Sharpe but no downside volatility suggests all trades were winners
                sortino_ratio = (
                    0.0 if sharpe_ratio <= 0 else sharpe_ratio * 1.5
                )  # Higher than Sharpe when no losses
            else:
                sortino_ratio = 0.0

            # Maximum Drawdown
            peak_equity = initial_capital
            max_drawdown_pct = 0.0
            max_drawdown_amt = 0.0
            current_drawdown = 0.0
            drawdowns = []

            equity = initial_capital
            for p in profits:
                equity += p
                if equity > peak_equity:
                    peak_equity = equity
                drawdown = (
                    (peak_equity - equity) / peak_equity if peak_equity > 0 else 0.0
                )
                drawdowns.append(drawdown)
                if drawdown > max_drawdown_pct:
                    max_drawdown_pct = drawdown
                    max_drawdown_amt = peak_equity - equity

            current_drawdown = drawdowns[-1] if drawdowns else 0.0
            avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else 0.0

            # Calmar Ratio (annualized return / max drawdown)
            if max_drawdown_pct > 0 and days > 0:
                annualized_return = (total_profit / initial_capital) * (365 / days)
                calmar_ratio = annualized_return / max_drawdown_pct
            else:
                calmar_ratio = 0.0

            # Period returns
            daily_return = (total_profit / initial_capital) / days if days > 0 else 0.0
            weekly_return = daily_return * 7
            monthly_return = daily_return * 30

            return AdvancedMetrics(
                totalTrades=total_trades,
                winningTrades=winning_trades,
                losingTrades=losing_trades,
                winRate=win_rate,
                totalProfit=total_profit,
                avgProfit=avg_profit,
                avgWin=avg_win,
                avgLoss=avg_loss,
                profitFactor=profit_factor,
                sharpeRatio=round(sharpe_ratio, 2),
                sortinoRatio=round(sortino_ratio, 2),
                calmarRatio=round(calmar_ratio, 2),
                maxDrawdown=round(max_drawdown_pct * 100, 2),
                maxDrawdownAmount=round(max_drawdown_amt, 2),
                avgDrawdown=round(avg_drawdown * 100, 2),
                currentDrawdown=round(current_drawdown * 100, 2),
                bestTrade=max(profits) if profits else 0.0,
                worstTrade=min(profits) if profits else 0.0,
                avgHoldingTime=0.0,  # Would need trade entry/exit times
                dailyReturn=round(daily_return * 100, 4),
                weeklyReturn=round(weekly_return * 100, 2),
                monthlyReturn=round(monthly_return * 100, 2),
            )

    except Exception as e:
        logger.error(f"Error calculating advanced metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to calculate advanced metrics"
        )


@router.get("/daily-pnl")
@cache_query_result(
    ttl=300, key_prefix="daily_pnl", include_user=True, include_params=True
)
async def get_daily_pnl(
    mode: Optional[str] = Query("paper", description="Trading mode: paper or real"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    current_user: dict = Depends(get_current_user),
) -> List[DailyPnL]:
    """
    Get daily P&L breakdown for charting.

    Returns:
    - Daily profit/loss
    - Cumulative P&L over time
    - Number of trades per day
    """
    try:
        user_id = current_user.get("id")
        normalized_mode = "real" if mode == "live" else mode

        from ..database import get_db_context
        from sqlalchemy import select, and_, func
        from ..models.trade import Trade

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with get_db_context() as db:
            trades_result = await db.execute(
                select(Trade)
                .where(
                    and_(
                        Trade.user_id == user_id,
                        Trade.mode == normalized_mode,
                        Trade.created_at >= cutoff_date,
                    )
                )
                .order_by(Trade.created_at)
            )
            trades = trades_result.scalars().all()

            if not trades:
                return []

            # Group by date
            daily_data = {}
            for trade in trades:
                if trade.pnl is None:
                    continue
                date_key = trade.created_at.strftime("%Y-%m-%d")
                if date_key not in daily_data:
                    daily_data[date_key] = {"pnl": 0.0, "trades": 0}
                daily_data[date_key]["pnl"] += float(trade.pnl)
                daily_data[date_key]["trades"] += 1

            # Build cumulative P&L
            result = []
            cumulative = 0.0
            for date_key in sorted(daily_data.keys()):
                data = daily_data[date_key]
                cumulative += data["pnl"]
                result.append(
                    DailyPnL(
                        date=date_key,
                        pnl=round(data["pnl"], 2),
                        cumulativePnl=round(cumulative, 2),
                        trades=data["trades"],
                    )
                )

            return result

    except Exception as e:
        logger.error(f"Error fetching daily P&L: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch daily P&L")


@router.get("/drawdown")
@cache_query_result(
    ttl=300, key_prefix="drawdown_chart", include_user=True, include_params=True
)
async def get_drawdown_chart(
    mode: Optional[str] = Query("paper", description="Trading mode: paper or real"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    current_user: dict = Depends(get_current_user),
) -> List[DrawdownPoint]:
    """
    Get drawdown history for visualization.

    Calculates the drawdown (decline from peak equity) over time.
    Essential for understanding risk and worst-case scenarios.
    """
    try:
        user_id = current_user.get("id")
        normalized_mode = "real" if mode == "live" else mode

        from ..database import get_db_context
        from sqlalchemy import select, and_
        from ..models.trade import Trade

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with get_db_context() as db:
            trades_result = await db.execute(
                select(Trade)
                .where(
                    and_(
                        Trade.user_id == user_id,
                        Trade.mode == normalized_mode,
                        Trade.created_at >= cutoff_date,
                    )
                )
                .order_by(Trade.created_at)
            )
            trades = trades_result.scalars().all()

            if not trades:
                return []

            # Calculate drawdown over time
            initial_capital = DEFAULT_INITIAL_CAPITAL
            equity = initial_capital
            peak_equity = initial_capital

            result = []
            for trade in trades:
                if trade.pnl is None:
                    continue

                equity += float(trade.pnl)
                if equity > peak_equity:
                    peak_equity = equity

                drawdown = (
                    ((peak_equity - equity) / peak_equity * 100)
                    if peak_equity > 0
                    else 0.0
                )

                result.append(
                    DrawdownPoint(
                        date=trade.created_at.strftime("%Y-%m-%d %H:%M"),
                        drawdown=round(drawdown, 2),
                        peakEquity=round(peak_equity, 2),
                        currentEquity=round(equity, 2),
                    )
                )

            return result

    except Exception as e:
        logger.error(f"Error calculating drawdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate drawdown")
