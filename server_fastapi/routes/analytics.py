from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from server_fastapi.services.analytics_engine import AnalyticsEngine
from server_fastapi.services.advanced_analytics_engine import AdvancedAnalyticsEngine
from server_fastapi.services.monitoring.performance_monitor import PerformanceMonitor
from server_fastapi.dependencies.auth import get_current_user
from server_fastapi.database import get_db_session
from datetime import datetime, timedelta
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    # Fallback for environments without pandas/numpy
    PANDAS_AVAILABLE = False
    pd = None
    np = None


logger = logging.getLogger(__name__)

# Dependency injection for analytics services
def get_analytics_engine():
    return AnalyticsEngine()

def get_advanced_analytics_engine():
    return AdvancedAnalyticsEngine()

def get_performance_monitor():
    return PerformanceMonitor()

# Import centralized auth dependency
from ..dependencies.auth import get_current_user

router = APIRouter()

class AnalyticsSummary(BaseModel):
    total_bots: int
    active_bots: int
    total_trades: int
    total_pnl: float
    win_rate: float
    best_performing_bot: Optional[str]
    worst_performing_bot: Optional[str]

class PerformanceMetrics(BaseModel):
    bot_id: str
    bot_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    current_balance: float
    period_start: datetime
    period_end: datetime

class RiskMetrics(BaseModel):
    portfolio_value: float
    total_exposure: float
    max_drawdown: float
    value_at_risk: float
    expected_shortfall: float
    volatility: float
    sharpe_ratio: float

class TradeRecord(BaseModel):
    id: str
    bot_id: str
    symbol: str
    side: str
    amount: float
    price: float
    timestamp: datetime
    pnl: Optional[float]
    status: str

class PortfolioAnalytics(BaseModel):
    total_value: float
    total_pnl: float
    pnl_percentage: float
    asset_allocation: Dict[str, float]
    performance_vs_benchmark: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    risk_adjusted_return: float

class BacktestResult(BaseModel):
    strategy_id: str
    strategy_name: str
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_pnl: float
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float

class RealTimeMetrics(BaseModel):
    timestamp: datetime
    portfolio_value: float
    daily_pnl: float
    daily_pnl_percent: float
    active_positions: int
    total_trades_today: int
    win_rate_today: float
    system_health: str
    last_update: datetime

class DashboardSummary(BaseModel):
    total_portfolio_value: float
    total_pnl_today: float
    pnl_percentage_today: float
    active_bots: int
    total_positions: int
    risk_score: float
    market_sentiment: str
    last_updated: datetime

class PerformanceChartData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]

class CorrelationMatrix(BaseModel):
    assets: List[str]
    matrix: List[List[float]]

class AssetAllocation(BaseModel):
    asset: str
    percentage: float
    value: float
    pnl: float

@router.get("/summary")
async def get_analytics_summary(
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> AnalyticsSummary:
    """Get overall analytics summary from database"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get real data from database
        analytics_result = await engine.analyze({
            "user_id": user_id,
            "type": "summary"
        }, db_session=db_session)
        
        summary = analytics_result.get("summary", {})
        
        return AnalyticsSummary(
            total_bots=summary.get("total_bots", 0),
            active_bots=summary.get("active_bots", 0),
            total_trades=summary.get("total_trades", 0),
            total_pnl=summary.get("total_pnl", 0.0),
            win_rate=summary.get("win_rate", 0.0),
            best_performing_bot=summary.get("best_performing_bot"),
            worst_performing_bot=summary.get("worst_performing_bot")
        )
        user_id = current_user.get('id')
        analytics_result = await engine.analyze({"user_id": user_id, "type": "summary"})

        return AnalyticsSummary(
            total_bots=analytics_result.summary.get('total_bots', 5),
            active_bots=analytics_result.summary.get('active_bots', 2),
            total_trades=analytics_result.summary.get('total_trades', 245),
            total_pnl=analytics_result.summary.get('total_pnl', 3250.75),
            win_rate=analytics_result.summary.get('win_rate', 0.612),
            best_performing_bot=analytics_result.summary.get('best_performing_bot', "bot-1"),
            worst_performing_bot=analytics_result.summary.get('worst_performing_bot', "bot-3")
        )
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")

@router.get("/performance")
async def get_performance_metrics(
    bot_id: Optional[str] = Query(None, description="Filter by specific bot ID"),
    period: str = Query("30d", description="Time period (1d, 7d, 30d, 90d, 1y)"),
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> List[PerformanceMetrics]:
    """Get performance metrics for bots"""
    try:
        user_id = current_user.get('id')
        analytics_result = await engine.analyze({
            "user_id": user_id,
            "type": "performance",
            "bot_id": bot_id,
            "period": period
        })

        # Parse period to get start/end dates
        end_date = datetime.now()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        metrics_data = analytics_result.details.get('metrics', [])

        metrics = []
        for metric_data in metrics_data:
            if bot_id and metric_data.get('bot_id') != bot_id:
                continue

            metrics.append(PerformanceMetrics(
                bot_id=metric_data.get('bot_id', 'unknown'),
                bot_name=metric_data.get('bot_name', 'Unknown Bot'),
                total_trades=metric_data.get('total_trades', 0),
                winning_trades=metric_data.get('winning_trades', 0),
                losing_trades=metric_data.get('losing_trades', 0),
                win_rate=metric_data.get('win_rate', 0.0),
                total_pnl=metric_data.get('total_pnl', 0.0),
                max_drawdown=metric_data.get('max_drawdown', 0.0),
                sharpe_ratio=metric_data.get('sharpe_ratio', 0.0),
                current_balance=metric_data.get('current_balance', 0.0),
                period_start=start_date,
                period_end=end_date
            ))

        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.get("/risk")
async def get_risk_metrics(
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> RiskMetrics:
    """Get portfolio risk metrics"""
    try:
        user_id = current_user.get('id')
        analytics_result = await engine.analyze({"user_id": user_id, "type": "risk"})

        return RiskMetrics(
            portfolio_value=analytics_result.summary.get('portfolio_value', 125000.50),
            total_exposure=analytics_result.summary.get('total_exposure', 25000.75),
            max_drawdown=analytics_result.summary.get('max_drawdown', 1850.25),
            value_at_risk=analytics_result.summary.get('value_at_risk', 1250.50),
            expected_shortfall=analytics_result.summary.get('expected_shortfall', 1875.75),
            volatility=analytics_result.summary.get('volatility', 0.024),
            sharpe_ratio=analytics_result.summary.get('sharpe_ratio', 1.65)
        )
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk metrics")

@router.get("/trades")
async def get_trade_history(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    symbol: Optional[str] = Query(None, description="Filter by trading symbol"),
    limit: int = Query(50, description="Number of trades to return", ge=1, le=500),
    offset: int = Query(0, description="Number of trades to skip", ge=0),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> List[TradeRecord]:
    """Get trade history from database"""
    try:
        from sqlalchemy import select
        from ..models.trade import Trade
        
        user_id = current_user.get('id') or current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Build query
        query = select(Trade).where(Trade.user_id == user_id)
            
        if bot_id:
            query = query.where(Trade.bot_id == bot_id)
        if symbol:
            query = query.where(Trade.symbol == symbol)
        
        # Order by executed_at descending (most recent first)
        query = query.order_by(Trade.executed_at.desc() if hasattr(Trade.executed_at, 'desc') else Trade.timestamp.desc())
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db_session.execute(query)
        db_trades = list(result.scalars().all())
        
        # Convert to TradeRecord
        trade_records = []
        for trade in db_trades:
            trade_records.append(TradeRecord(
                id=str(trade.id),
                bot_id=trade.bot_id or "",
                symbol=trade.symbol,
                side=trade.side,
                amount=trade.amount,
                price=trade.price,
                timestamp=trade.executed_at if trade.executed_at else trade.timestamp,
                pnl=trade.pnl,
                status=trade.status
            ))
        
        return trade_records
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trade history")

@router.get("/pnl-chart")
async def get_pnl_chart(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    period: str = Query("30d", description="Time period"),
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Get PnL chart data from database"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get database session and analyze
            analytics_result = await engine.analyze({
                "user_id": user_id,
                "type": "pnl_chart",
                "bot_id": bot_id,
                "period": period
            }, db_session=db_session)
            
            # Use real data from analytics engine
            chart_data = analytics_result.get('chart_data', [])
            
            # In production, return empty data if no trades found
            if not chart_data:
                from ..config.settings import get_settings
                settings = get_settings()
                if settings.production_mode or settings.is_production:
                    return []
                else:
                    # Development fallback only
                    end_date = datetime.now()
                    if period == "7d":
                        days = 7
                    elif period == "30d":
                        days = 30
                    elif period == "90d":
                        days = 90
                    else:
                        days = 30

                chart_data = []
                cumulative_pnl = 0.0
                for i in range(days):
                    date = end_date - timedelta(days=days-i-1)
                    daily_pnl = (i % 5 - 2) * 50.0  # Mock daily PnL
                    cumulative_pnl += daily_pnl

                    chart_data.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "daily_pnl": daily_pnl,
                        "cumulative_pnl": cumulative_pnl
                    })

        return chart_data
    except Exception as e:
        logger.error(f"Error getting PnL chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get PnL chart")

@router.get("/win-rate-chart")
async def get_win_rate_chart(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    period: str = Query("30d", description="Time period")
) -> List[Dict[str, Any]]:
    """Get win rate chart data over time"""
    try:
        # Mock data - in real implementation, calculate rolling win rate
        end_date = datetime.now()
        if period == "7d":
            days = 7
        elif period == "30d":
            days = 30
        elif period == "90d":
            days = 90
        else:
            days = 30

        chart_data = []

        for i in range(days):
            date = end_date - timedelta(days=days-i-1)
            # Mock win rate between 50-70%
            win_rate = 0.5 + 0.2 * (i % 3 - 1) * 0.1

            chart_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "win_rate": win_rate
            })

        return chart_data
    except Exception as e:
        logger.error(f"Error getting win rate chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get win rate chart")

@router.get("/drawdown-chart")
async def get_drawdown_chart(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    period: str = Query("30d", description="Time period")
) -> List[Dict[str, Any]]:
    """Get drawdown chart data"""
    try:
        # Mock data - in real implementation, calculate drawdown from equity curve
        end_date = datetime.now()
        if period == "7d":
            days = 7
        elif period == "30d":
            days = 30
        elif period == "90d":
            days = 90
        else:
            days = 30

        chart_data = []
        peak = 100000.0
        current_value = 100000.0

        for i in range(days):
            date = end_date - timedelta(days=days-i-1)

            # Mock price movement
            change = (i % 10 - 5) * 100.0
            current_value += change
            peak = max(peak, current_value)
            drawdown = (peak - current_value) / peak

            chart_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "drawdown": drawdown,
                "portfolio_value": current_value
            })

        return chart_data
    except Exception as e:
        logger.error(f"Error getting drawdown chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get drawdown chart")

@router.get("/portfolio")
async def get_portfolio_analytics(
    period: str = Query("30d", description="Time period (1d, 7d, 30d, 90d, 1y)"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> PortfolioAnalytics:
    """Get portfolio analytics"""
    try:
        user_id = current_user.get('id')
        analytics_result = await engine.analyze({
            "user_id": user_id,
            "type": "portfolio",
            "period": period
        })

        return PortfolioAnalytics(
            total_value=analytics_result.summary.get('total_value', 100000.0),
            total_pnl=analytics_result.summary.get('total_pnl', 5000.0),
            pnl_percentage=analytics_result.summary.get('pnl_percentage', 5.0),
            asset_allocation=analytics_result.details.get('asset_allocation', {}),
            performance_vs_benchmark=analytics_result.summary.get('performance_vs_benchmark', 2.5),
            volatility=analytics_result.summary.get('volatility', 0.15),
            sharpe_ratio=analytics_result.summary.get('sharpe_ratio', 1.8),
            max_drawdown=analytics_result.summary.get('max_drawdown', 1500.0),
            risk_adjusted_return=analytics_result.summary.get('risk_adjusted_return', 1.2)
        )
    except Exception as e:
        logger.error(f"Error getting portfolio analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio analytics")

@router.get("/backtesting/{strategy_id}")
async def get_backtesting_results(
    strategy_id: str,
    backtest_id: Optional[str] = Query(None, description="Specific backtest ID"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> BacktestResult:
    """Get backtesting results for a strategy"""
    try:
        user_id = current_user.get('id')
        analytics_result = await engine.analyze({
            "user_id": user_id,
            "type": "backtesting",
            "strategy_id": strategy_id,
            "backtest_id": backtest_id
        })

        backtest_data = analytics_result.details.get('backtest', {})

        return BacktestResult(
            strategy_id=strategy_id,
            strategy_name=backtest_data.get('strategy_name', 'Unknown Strategy'),
            total_return=backtest_data.get('total_return', 0.0),
            annualized_return=backtest_data.get('annualized_return', 0.0),
            volatility=backtest_data.get('volatility', 0.0),
            sharpe_ratio=backtest_data.get('sharpe_ratio', 0.0),
            max_drawdown=backtest_data.get('max_drawdown', 0.0),
            win_rate=backtest_data.get('win_rate', 0.0),
            total_trades=backtest_data.get('total_trades', 0),
            avg_trade_pnl=backtest_data.get('avg_trade_pnl', 0.0),
            start_date=datetime.fromisoformat(backtest_data.get('start_date', datetime.now().isoformat())),
            end_date=datetime.fromisoformat(backtest_data.get('end_date', datetime.now().isoformat())),
            initial_balance=backtest_data.get('initial_balance', 10000.0),
            final_balance=backtest_data.get('final_balance', 10000.0)
        )
    except Exception as e:
        logger.error(f"Error getting backtesting results: {e}")
@router.get("/backtesting/compare")
async def compare_backtesting_results(
    strategy_ids: List[str] = Query(..., description="List of strategy IDs to compare"),
    backtest_ids: Optional[List[str]] = Query(None, description="Specific backtest IDs for each strategy"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> List[BacktestResult]:
    """Compare backtesting results across multiple strategies"""
    try:
        user_id = current_user.get('id')
        comparison_results = []

        for i, strategy_id in enumerate(strategy_ids):
            backtest_id = backtest_ids[i] if backtest_ids and i < len(backtest_ids) else None
            analytics_result = await engine.analyze({
                "user_id": user_id,
                "type": "backtesting",
                "strategy_id": strategy_id,
                "backtest_id": backtest_id
            })

            backtest_data = analytics_result.details.get('backtest', {})

            comparison_results.append(BacktestResult(
                strategy_id=strategy_id,
                strategy_name=backtest_data.get('strategy_name', f'Strategy {strategy_id}'),
                total_return=backtest_data.get('total_return', 0.0),
                annualized_return=backtest_data.get('annualized_return', 0.0),
                volatility=backtest_data.get('volatility', 0.0),
                sharpe_ratio=backtest_data.get('sharpe_ratio', 0.0),
                max_drawdown=backtest_data.get('max_drawdown', 0.0),
                win_rate=backtest_data.get('win_rate', 0.0),
                total_trades=backtest_data.get('total_trades', 0),
                avg_trade_pnl=backtest_data.get('avg_trade_pnl', 0.0),
                start_date=datetime.fromisoformat(backtest_data.get('start_date', datetime.now().isoformat())),
                end_date=datetime.fromisoformat(backtest_data.get('end_date', datetime.now().isoformat())),
                initial_balance=backtest_data.get('initial_balance', 10000.0),
                final_balance=backtest_data.get('final_balance', 10000.0)
            ))

        return comparison_results
    except Exception as e:
        logger.error(f"Error comparing backtesting results: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare backtesting results")

@router.get("/backtesting/performance-metrics")
async def get_backtesting_performance_metrics(
    strategy_id: str,
    backtest_id: Optional[str] = Query(None, description="Specific backtest ID"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed performance metrics for a backtest"""
    try:
        user_id = current_user.get('id')
        analytics_result = await engine.analyze({
            "user_id": user_id,
            "type": "backtesting",
            "strategy_id": strategy_id,
            "backtest_id": backtest_id
        })

        backtest_data = analytics_result.details.get('backtest', {})

        # Calculate additional metrics
        total_return = backtest_data.get('total_return', 0.0)
        volatility = backtest_data.get('volatility', 0.0)
        max_drawdown = backtest_data.get('max_drawdown', 0.0)
        initial_balance = backtest_data.get('initial_balance', 10000.0)
        final_balance = backtest_data.get('final_balance', initial_balance * (1 + total_return))

        # Risk-adjusted returns
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else float('inf')
        sortino_ratio = total_return / volatility if volatility > 0 else float('inf')  # Simplified

        return {
            "strategy_id": strategy_id,
            "backtest_id": backtest_id,
            "basic_metrics": {
                "total_return": total_return,
                "annualized_return": backtest_data.get('annualized_return', total_return),
                "volatility": volatility,
                "sharpe_ratio": backtest_data.get('sharpe_ratio', 0.0),
                "max_drawdown": max_drawdown,
                "win_rate": backtest_data.get('win_rate', 0.0),
                "total_trades": backtest_data.get('total_trades', 0),
                "avg_trade_pnl": backtest_data.get('avg_trade_pnl', 0.0)
            },
            "risk_metrics": {
                "calmar_ratio": calmar_ratio,
                "sortino_ratio": sortino_ratio,
                "value_at_risk": -volatility * 1.645,  # Simplified VaR calculation
                "expected_shortfall": -volatility * 2.0  # Simplified ES calculation
            },
            "portfolio_metrics": {
                "initial_balance": initial_balance,
                "final_balance": final_balance,
                "peak_balance": final_balance * (1 + max_drawdown),  # Simplified
                "recovery_factor": total_return / max_drawdown if max_drawdown > 0 else float('inf')
            }
        }
    except Exception as e:
        logger.error(f"Error getting backtesting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backtesting performance metrics")


# ===== ENHANCED BUSINESS INTELLIGENCE DASHBOARD APIs =====

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    advanced_engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> DashboardSummary:
    """Get comprehensive dashboard summary with real-time metrics"""
    try:
        user_id = current_user.get('id')

        # Get portfolio analytics
        portfolio_result = await advanced_engine._analyze_portfolio(user_id, '1d')
        portfolio_data = portfolio_result.details if portfolio_result else {}

        # Get performance metrics from database
        performance_result = await engine.analyze({
            "user_id": user_id,
            "type": "performance",
            "period": "1d"
        }, db_session=db_session)
        performance_data = performance_result.get("details", {}) if performance_result else {}

        # Get system health
        system_health = await monitor.get_system_health()

        # Calculate risk score (simplified)
        risk_score = min(abs(portfolio_data.get('volatility', 0.15)) * 100, 100)

        # Determine market sentiment (simplified)
        market_sentiment = "neutral"
        if portfolio_data.get('sharpe_ratio', 0) > 1.5:
            market_sentiment = "bullish"
        elif portfolio_data.get('sharpe_ratio', 0) < 0.5:
            market_sentiment = "bearish"

        return DashboardSummary(
            total_portfolio_value=portfolio_data.get('total_value', 100000.0),
            total_pnl_today=portfolio_data.get('total_pnl', 0.0),
            pnl_percentage_today=portfolio_data.get('pnl_percentage', 0.0),
            active_bots=performance_data.get('active_bots', 0),
            total_positions=portfolio_data.get('total_positions', 0),
            risk_score=risk_score,
            market_sentiment=market_sentiment,
            last_updated=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")


@router.get("/dashboard/realtime")
async def get_realtime_metrics(
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
    current_user: dict = Depends(get_current_user)
) -> RealTimeMetrics:
    """Get real-time trading and performance metrics"""
    try:
        user_id = current_user.get('id')

        # Get system metrics
        system_metrics = await monitor.collect_system_metrics()

        # Get trading performance (simplified real-time data)
        performance_result = await engine.analyze({"user_id": user_id, "type": "performance", "period": "1d"})
        performance_data = performance_result.details.get('metrics', [{}])[0] if performance_result and performance_result.details.get('metrics') else {}

        # Calculate daily P&L (simplified)
        daily_pnl = performance_data.get('total_pnl', 0.0)
        portfolio_value = performance_data.get('current_balance', 100000.0)
        daily_pnl_percent = (daily_pnl / portfolio_value) * 100 if portfolio_value > 0 else 0

        # Determine system health
        system_health = "healthy"
        if system_metrics.cpu_usage > 90 or system_metrics.memory_usage > 90:
            system_health = "degraded"
        elif system_metrics.cpu_usage > 95 or system_metrics.memory_usage > 95:
            system_health = "critical"

        return RealTimeMetrics(
            timestamp=datetime.now(),
            portfolio_value=portfolio_value,
            daily_pnl=daily_pnl,
            daily_pnl_percent=daily_pnl_percent,
            active_positions=performance_data.get('active_positions', 0),
            total_trades_today=performance_data.get('total_trades', 0),
            win_rate_today=performance_data.get('win_rate', 0.0),
            system_health=system_health,
            last_update=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting realtime metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get realtime metrics")


@router.get("/dashboard/charts/portfolio-performance")
async def get_portfolio_performance_chart(
    period: str = Query("30d", description="Time period (1d, 7d, 30d, 90d, 1y)"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> PerformanceChartData:
    """Get portfolio performance chart data optimized for visualization"""
    try:
        user_id = current_user.get('id')

        # Parse period
        days = 30
        if period == "1d":
            days = 1
        elif period == "7d":
            days = 7
        elif period == "90d":
            days = 90
        elif period == "1y":
            days = 365

        # Generate date labels
        end_date = datetime.now()
        dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, 0, -1)]

        # Get portfolio data over time (simplified - would use historical data)
        portfolio_values = []
        pnl_values = []
        base_value = 100000.0

        for i in range(days):
            # Simulate portfolio growth with some volatility
            if PANDAS_AVAILABLE:
                change = np.random.normal(0.001, 0.02)  # Mean 0.1%, std 2%
            else:
                # Simple random fallback without numpy
                import random
                change = random.gauss(0.001, 0.02)
            base_value *= (1 + change)
            portfolio_values.append(base_value)

            # Calculate P&L for this day
            daily_pnl = change * base_value
            pnl_values.append(daily_pnl)

        return PerformanceChartData(
            labels=dates,
            datasets=[
                {
                    "label": "Portfolio Value",
                    "data": [round(v, 2) for v in portfolio_values],
                    "borderColor": "rgb(75, 192, 192)",
                    "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    "type": "line"
                },
                {
                    "label": "Daily P&L",
                    "data": [round(p, 2) for p in pnl_values],
                    "borderColor": "rgb(255, 99, 132)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "type": "bar"
                }
            ]
        )
    except Exception as e:
        logger.error(f"Error getting portfolio performance chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio performance chart")


@router.get("/dashboard/charts/asset-allocation")
async def get_asset_allocation_chart(
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> List[AssetAllocation]:
    """Get current asset allocation for pie chart visualization"""
    try:
        user_id = current_user.get('id')

        # Get portfolio analytics
        portfolio_result = await engine._analyze_portfolio(user_id, '1d')
        portfolio_data = portfolio_result.details if portfolio_result else {}

        # Mock asset allocation data (would be from real portfolio)
        assets = [
            {"asset": "BTC", "percentage": 0.45, "value": 45000.0, "pnl": 2500.0},
            {"asset": "ETH", "percentage": 0.30, "value": 30000.0, "pnl": -500.0},
            {"asset": "ADA", "percentage": 0.15, "value": 15000.0, "pnl": 800.0},
            {"asset": "SOL", "percentage": 0.10, "value": 10000.0, "pnl": 1200.0}
        ]

        return [AssetAllocation(**asset) for asset in assets]
    except Exception as e:
        logger.error(f"Error getting asset allocation chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get asset allocation chart")


@router.get("/dashboard/charts/correlation-matrix")
async def get_correlation_matrix_data(
    assets: List[str] = Query(None, description="List of asset symbols"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> CorrelationMatrix:
    """Get correlation matrix data for risk analysis visualization"""
    try:
        user_id = current_user.get('id')

        # Default assets if none provided
        if not assets:
            assets = ["BTC", "ETH", "ADA", "SOL", "DOT"]

        # Generate correlation matrix (simplified - would use real market data)
        n = len(assets)
        matrix = []

        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(1.0)  # Perfect correlation with itself
                else:
                    # Generate realistic correlations
                    correlation = np.random.uniform(-0.3, 0.8)
                    row.append(round(correlation, 3))
            matrix.append(row)

        return CorrelationMatrix(assets=assets, matrix=matrix)
    except Exception as e:
        logger.error(f"Error getting correlation matrix: {e}")
        raise HTTPException(status_code=500, detail="Failed to get correlation matrix")


@router.get("/dashboard/charts/risk-metrics")
async def get_risk_metrics_chart(
    period: str = Query("30d", description="Time period"),
    engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> PerformanceChartData:
    """Get risk metrics chart data for visualization"""
    try:
        user_id = current_user.get('id')

        # Get risk analysis
        risk_result = await engine._analyze_risk(user_id)
        risk_data = risk_result.summary if risk_result else {}

        # Generate historical risk metrics (simplified)
        days = 30 if period == "30d" else 7 if period == "7d" else 30
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, 0, -1)]

        # Simulate risk metrics over time
        if PANDAS_AVAILABLE:
            volatility_data = [risk_data.get('volatility', 0.15) + np.random.normal(0, 0.02) for _ in range(days)]
            sharpe_data = [risk_data.get('sharpe_ratio', 1.5) + np.random.normal(0, 0.3) for _ in range(days)]
        else:
            import random
            volatility_data = [risk_data.get('volatility', 0.15) + random.gauss(0, 0.02) for _ in range(days)]
            sharpe_data = [risk_data.get('sharpe_ratio', 1.5) + random.gauss(0, 0.3) for _ in range(days)]
        var_data = [-abs(v) * 1.645 * 100 for v in volatility_data]  # VaR at 95% confidence

        return PerformanceChartData(
            labels=dates,
            datasets=[
                {
                    "label": "Volatility",
                    "data": [round(v * 100, 2) for v in volatility_data],
                    "borderColor": "rgb(255, 159, 64)",
                    "backgroundColor": "rgba(255, 159, 64, 0.2)",
                    "type": "line"
                },
                {
                    "label": "Value at Risk (95%)",
                    "data": [round(v, 2) for v in var_data],
                    "borderColor": "rgb(255, 99, 132)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "type": "line"
                },
                {
                    "label": "Sharpe Ratio",
                    "data": [round(s, 2) for s in sharpe_data],
                    "borderColor": "rgb(54, 162, 235)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "type": "line"
                }
            ]
        )
    except Exception as e:
        logger.error(f"Error getting risk metrics chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk metrics chart")


@router.get("/dashboard/charts/bot-performance-comparison")
async def get_bot_performance_comparison_chart(
    period: str = Query("30d", description="Time period"),
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> PerformanceChartData:
    """Get bot performance comparison chart data"""
    try:
        user_id = current_user.get('id')

        # Get performance data for all bots
        performance_result = await engine.analyze({"user_id": user_id, "type": "performance", "period": period})
        metrics_data = performance_result.details.get('metrics', [])

        # Prepare data for chart
        bot_names = [m.get('bot_name', f'Bot {m.get("bot_id", "unknown")}') for m in metrics_data]
        win_rates = [m.get('win_rate', 0) * 100 for m in metrics_data]
        total_pnl = [m.get('total_pnl', 0) for m in metrics_data]
        sharpe_ratios = [m.get('sharpe_ratio', 0) for m in metrics_data]

        return PerformanceChartData(
            labels=bot_names,
            datasets=[
                {
                    "label": "Win Rate (%)",
                    "data": [round(w, 1) for w in win_rates],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "type": "bar"
                },
                {
                    "label": "Total P&L ($)",
                    "data": [round(p, 2) for p in total_pnl],
                    "backgroundColor": "rgba(255, 99, 132, 0.6)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "type": "bar"
                }
            ]
        )
    except Exception as e:
        logger.error(f"Error getting bot performance comparison chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot performance comparison chart")


@router.get("/dashboard/charts/trade-distribution")
async def get_trade_distribution_chart(
    period: str = Query("30d", description="Time period"),
    current_user: dict = Depends(get_current_user)
) -> PerformanceChartData:
    """Get trade distribution chart data (by hour, day, symbol)"""
    try:
        # Mock trade distribution data (would be from actual trade logs)
        hours = [f"{i:02d}:00" for i in range(24)]
        if PANDAS_AVAILABLE:
            trades_by_hour = [np.random.poisson(5) for _ in range(24)]  # Poisson distribution
            trades_by_day = [np.random.poisson(20) for _ in range(7)]
            trades_by_symbol = [np.random.poisson(15) for _ in range(5)]
        else:
            import random
            trades_by_hour = [max(0, int(random.gauss(5, 2))) for _ in range(24)]
            trades_by_day = [max(0, int(random.gauss(20, 5))) for _ in range(7)]
            trades_by_symbol = [max(0, int(random.gauss(15, 4))) for _ in range(5)]

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        symbols = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'SOL/USD', 'DOT/USD']

        return PerformanceChartData(
            labels=hours + days + symbols,
            datasets=[
                {
                    "label": "Trades by Hour",
                    "data": trades_by_hour + [0] * (len(days) + len(symbols)),
                    "backgroundColor": "rgba(153, 102, 255, 0.6)",
                    "borderColor": "rgba(153, 102, 255, 1)",
                    "type": "bar"
                },
                {
                    "label": "Trades by Day",
                    "data": [0] * len(hours) + trades_by_day + [0] * len(symbols),
                    "backgroundColor": "rgba(255, 159, 64, 0.6)",
                    "borderColor": "rgba(255, 159, 64, 1)",
                    "type": "bar"
                },
                {
                    "label": "Trades by Symbol",
                    "data": [0] * (len(hours) + len(days)) + trades_by_symbol,
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "type": "bar"
                }
            ]
        )
    except Exception as e:
        logger.error(f"Error getting trade distribution chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trade distribution chart")


@router.get("/dashboard/kpis")
async def get_key_performance_indicators(
    period: str = Query("30d", description="Time period"),
    engine: AnalyticsEngine = Depends(get_analytics_engine),
    advanced_engine: AdvancedAnalyticsEngine = Depends(get_advanced_analytics_engine),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get key performance indicators for dashboard"""
    try:
        user_id = current_user.get('id')

        # Get various analytics data
        summary_result = await engine.analyze({"user_id": user_id, "type": "summary"})
        portfolio_result = await advanced_engine._analyze_portfolio(user_id, period)
        risk_result = await advanced_engine._analyze_risk(user_id)

        summary_data = summary_result.summary if summary_result else {}
        portfolio_data = portfolio_result.summary if portfolio_result else {}
        risk_data = risk_result.summary if risk_result else {}

        # Calculate KPIs
        kpis = {
            "total_portfolio_value": {
                "value": portfolio_data.get('total_value', 100000.0),
                "change": portfolio_data.get('total_pnl', 0.0),
                "change_percent": portfolio_data.get('pnl_percentage', 0.0),
                "format": "currency"
            },
            "total_pnl": {
                "value": summary_data.get('total_pnl', 0.0),
                "change": summary_data.get('total_pnl', 0.0) * 0.1,  # Mock daily change
                "change_percent": 10.0,  # Mock percentage
                "format": "currency"
            },
            "win_rate": {
                "value": summary_data.get('win_rate', 0.0) * 100,
                "change": 2.5,  # Mock improvement
                "change_percent": 2.5,
                "format": "percentage"
            },
            "active_bots": {
                "value": summary_data.get('active_bots', 0),
                "change": 1,
                "change_percent": 25.0,  # Mock increase
                "format": "number"
            },
            "sharpe_ratio": {
                "value": risk_data.get('sharpe_ratio', 0.0),
                "change": 0.1,
                "change_percent": 7.1,
                "format": "decimal"
            },
            "max_drawdown": {
                "value": abs(risk_data.get('max_drawdown', 0.0)) * 100,
                "change": -2.0,  # Mock improvement (reduction)
                "change_percent": -20.0,
                "format": "percentage"
            }
        }

        return kpis
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get KPIs")


@router.get("/dashboard/alerts-summary")
async def get_alerts_summary(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get summary of active alerts and notifications"""
    try:
        # This would integrate with the notification service
        # For now, return mock data
        alerts = {
            "critical": 2,
            "warning": 5,
            "info": 12,
            "total_unread": 19
        }

        recent_alerts = [
            {
                "id": "alert-1",
                "title": "High Volatility Detected",
                "message": "BTC/USD volatility exceeded 5% threshold",
                "level": "warning",
                "timestamp": datetime.now().isoformat(),
                "category": "risk"
            },
            {
                "id": "alert-2",
                "title": "Bot Performance Alert",
                "message": "Bot-1 win rate dropped below 40%",
                "level": "critical",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "category": "bot"
            },
            {
                "id": "alert-3",
                "title": "Portfolio Rebalancing Needed",
                "message": "Asset allocation deviated by 15% from target",
                "level": "info",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "category": "portfolio"
            }
        ]

        return {
            "alert_counts": alerts,
            "recent_alerts": recent_alerts
        }
    except Exception as e:
        logger.error(f"Error getting alerts summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts summary")

