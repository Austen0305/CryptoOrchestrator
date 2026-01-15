import logging
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.database import get_db_session
from server_fastapi.dependencies.auth import get_current_user
from server_fastapi.middleware.cache_manager import cached
from server_fastapi.services.advanced_analytics_engine import AdvancedAnalyticsEngine
from server_fastapi.services.analytics_engine import AnalyticsEngine
from server_fastapi.services.monitoring.performance_monitor import PerformanceMonitor
from server_fastapi.utils.response_optimizer import ResponseOptimizer
from server_fastapi.utils.route_helpers import _get_user_id

try:
    import numpy as np
    import pandas as pd

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
    best_performing_bot: str | None
    worst_performing_bot: str | None


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
    pnl: float | None
    status: str


class PortfolioAnalytics(BaseModel):
    total_value: float
    total_pnl: float
    pnl_percentage: float
    asset_allocation: dict[str, float]
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
    labels: list[str]
    datasets: list[dict[str, Any]]


class CorrelationMatrix(BaseModel):
    assets: list[str]
    matrix: list[list[float]]


class AssetAllocation(BaseModel):
    asset: str
    percentage: float
    value: float
    pnl: float


@router.get("/summary")
@cached(ttl=120, prefix="analytics_summary")
async def get_analytics_summary(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsSummary:
    """Get overall analytics summary from database"""
    try:
        user_id = _get_user_id(current_user)

        # Get real data from database
        analytics_result = await engine.analyze(
            {"user_id": user_id, "type": "summary"}, db_session=db_session
        )

        summary = analytics_result.get("summary", {})

        return AnalyticsSummary(
            total_bots=summary.get("total_bots", 0),
            active_bots=summary.get("active_bots", 0),
            total_trades=summary.get("total_trades", 0),
            total_pnl=summary.get("total_pnl", 0.0),
            win_rate=summary.get("win_rate", 0.0),
            best_performing_bot=summary.get("best_performing_bot"),
            worst_performing_bot=summary.get("worst_performing_bot"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting analytics summary: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")


@router.get("/performance")
@cached(ttl=120, prefix="analytics_performance")
async def get_performance_metrics(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_id: str | None = Query(None, description="Filter by specific bot ID"),
    period: str = Query("30d", description="Time period (1d, 7d, 30d, 90d, 1y)"),
) -> list[PerformanceMetrics]:
    """Get performance metrics for bots"""
    try:
        user_id = _get_user_id(current_user)
        analytics_result = await engine.analyze(
            {
                "user_id": user_id,
                "type": "performance",
                "bot_id": bot_id,
                "period": period,
            }
        )

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

        metrics_data = analytics_result.details.get("metrics", [])

        metrics = []
        for metric_data in metrics_data:
            if bot_id and metric_data.get("bot_id") != bot_id:
                continue

            metrics.append(
                PerformanceMetrics(
                    bot_id=metric_data.get("bot_id", "unknown"),
                    bot_name=metric_data.get("bot_name", "Unknown Bot"),
                    total_trades=metric_data.get("total_trades", 0),
                    winning_trades=metric_data.get("winning_trades", 0),
                    losing_trades=metric_data.get("losing_trades", 0),
                    win_rate=metric_data.get("win_rate", 0.0),
                    total_pnl=metric_data.get("total_pnl", 0.0),
                    max_drawdown=metric_data.get("max_drawdown", 0.0),
                    sharpe_ratio=metric_data.get("sharpe_ratio", 0.0),
                    current_balance=metric_data.get("current_balance", 0.0),
                    period_start=start_date,
                    period_end=end_date,
                )
            )

        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting performance metrics: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.get("/risk")
@cached(ttl=120, prefix="analytics_risk")
async def get_risk_metrics(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RiskMetrics:
    """Get portfolio risk metrics"""
    try:
        user_id = _get_user_id(current_user)
        analytics_result = await engine.analyze({"user_id": user_id, "type": "risk"})

        return RiskMetrics(
            portfolio_value=analytics_result.summary.get("portfolio_value", 125000.50),
            total_exposure=analytics_result.summary.get("total_exposure", 25000.75),
            max_drawdown=analytics_result.summary.get("max_drawdown", 1850.25),
            value_at_risk=analytics_result.summary.get("value_at_risk", 1250.50),
            expected_shortfall=analytics_result.summary.get(
                "expected_shortfall", 1875.75
            ),
            volatility=analytics_result.summary.get("volatility", 0.024),
            sharpe_ratio=analytics_result.summary.get("sharpe_ratio", 1.65),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting risk metrics: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get risk metrics")


@router.get("/trades")
@cached(ttl=60, prefix="analytics_trades")
async def get_trade_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    bot_id: str | None = Query(None, description="Filter by bot ID"),
    symbol: str | None = Query(None, description="Filter by trading symbol"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
) -> list[TradeRecord]:
    """Get trade history from database with pagination"""
    try:
        from sqlalchemy import func, select

        from ..models.trade import Trade
        from ..utils.query_optimizer import QueryOptimizer

        user_id = _get_user_id(current_user)
        (page - 1) * page_size

        # Build query
        query = select(Trade).where(Trade.user_id == user_id)

        if bot_id:
            query = query.where(Trade.bot_id == bot_id)
        if symbol:
            query = query.where(Trade.symbol == symbol)

        # Order by executed_at descending (most recent first)
        query = query.order_by(
            Trade.executed_at.desc()
            if hasattr(Trade.executed_at, "desc")
            else Trade.timestamp.desc()
        )

        # Apply pagination using QueryOptimizer
        query = QueryOptimizer.paginate_query(query, page=page, page_size=page_size)

        # Get total count for pagination metadata
        count_query = (
            select(func.count()).select_from(Trade).where(Trade.user_id == user_id)
        )
        if bot_id:
            count_query = count_query.where(Trade.bot_id == bot_id)
        if symbol:
            count_query = count_query.where(Trade.symbol == symbol)
        total_result = await db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Execute query
        result = await db_session.execute(query)
        db_trades = list(result.scalars().all())

        # Convert to TradeRecord
        trade_records = []
        for trade in db_trades:
            trade_records.append(
                TradeRecord(
                    id=str(trade.id),
                    bot_id=trade.bot_id or "",
                    symbol=trade.symbol,
                    side=trade.side,
                    amount=trade.amount,
                    price=trade.price,
                    timestamp=(
                        trade.executed_at if trade.executed_at else trade.timestamp
                    ),
                    pnl=trade.pnl,
                    status=trade.status,
                )
            )

        # Return paginated response
        paginated_response = ResponseOptimizer.paginate_response(
            trade_records, page, page_size, total
        )
        return paginated_response["data"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting trade history: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get trade history")


@router.get("/pnl-chart")
@cached(ttl=300, prefix="analytics_pnl_chart")
async def get_pnl_chart(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    bot_id: str | None = Query(None, description="Filter by bot ID"),
    period: str = Query("30d", description="Time period"),
) -> list[dict[str, Any]]:
    """Get PnL chart data from database"""
    try:
        user_id = _get_user_id(current_user)

        # Get database session and analyze
        analytics_result = await engine.analyze(
            {
                "user_id": user_id,
                "type": "pnl_chart",
                "bot_id": bot_id,
                "period": period,
            },
            db_session=db_session,
        )

        # Use real data from analytics engine
        chart_data = analytics_result.get("chart_data", [])

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
                date = end_date - timedelta(days=days - i - 1)
                daily_pnl = (i % 5 - 2) * 50.0  # Mock daily PnL
                cumulative_pnl += daily_pnl

                chart_data.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "daily_pnl": daily_pnl,
                        "cumulative_pnl": cumulative_pnl,
                    }
                )

        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting PnL chart: {e}", exc_info=True, extra={"user_id": user_id}
        )
        raise HTTPException(status_code=500, detail="Failed to get PnL chart")


@router.get("/win-rate-chart")
async def get_win_rate_chart(
    bot_id: str | None = Query(None, description="Filter by bot ID"),
    period: str = Query("30d", description="Time period"),
) -> list[dict[str, Any]]:
    """Get win rate chart data over time"""
    try:
        user_id = _get_user_id(current_user)

        # Calculate real win rate from trades
        try:
            from ..database import get_db_context
            from ..repositories.trade_repository import TradeRepository

            end_date = datetime.now()
            if period == "7d":
                days = 7
            elif period == "30d":
                days = 30
            elif period == "90d":
                days = 90
            else:
                days = 30

            start_date = end_date - timedelta(days=days)

            async with get_db_context() as session:
                trade_repo = TradeRepository()
                # Get trades for user with reasonable limit for chart calculations
                # Limit to last 1000 trades to prevent performance issues
                trades = await trade_repo.get_by_user(
                    session, int(user_id), skip=0, limit=1000
                )

                # Filter trades by period
                period_trades = [
                    t
                    for t in trades
                    if (t.executed_at or t.timestamp or t.created_at)
                    and (t.executed_at or t.timestamp or t.created_at) >= start_date
                ]

                # Calculate win rate per day
                chart_data = []
                for i in range(days):
                    date = end_date - timedelta(days=days - i - 1)
                    day_start = datetime.combine(date.date(), datetime.min.time())
                    day_end = day_start + timedelta(days=1)

                    day_trades = [
                        t
                        for t in period_trades
                        if (t.executed_at or t.timestamp or t.created_at)
                        and day_start
                        <= (t.executed_at or t.timestamp or t.created_at)
                        < day_end
                    ]

                    if day_trades:
                        winning = sum(1 for t in day_trades if t.pnl and t.pnl > 0)
                        win_rate = winning / len(day_trades)
                    else:
                        win_rate = 0.0

                    chart_data.append(
                        {"date": date.strftime("%Y-%m-%d"), "win_rate": win_rate}
                    )

                return chart_data
        except Exception as calc_error:
            logger.warning(f"Failed to calculate win rate chart: {calc_error}")
            # Return empty data instead of mock data
            end_date = datetime.now()
            days = (
                30
                if period not in ["7d", "30d", "90d"]
                else (7 if period == "7d" else (30 if period == "30d" else 90))
            )
            return [
                {
                    "date": (end_date - timedelta(days=days - i - 1)).strftime(
                        "%Y-%m-%d"
                    ),
                    "win_rate": 0.0,
                }
                for i in range(days)
            ]
    except Exception as e:
        logger.error(f"Error getting win rate chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get win rate chart")


@router.get("/drawdown-chart")
async def get_drawdown_chart(
    bot_id: str | None = Query(None, description="Filter by bot ID"),
    period: str = Query("30d", description="Time period"),
) -> list[dict[str, Any]]:
    """Get drawdown chart data"""
    try:
        user_id = _get_user_id(current_user)

        # Calculate real drawdown from trade history
        try:
            from ..database import get_db_context
            from ..repositories.trade_repository import TradeRepository

            end_date = datetime.now()
            if period == "7d":
                days = 7
            elif period == "30d":
                days = 30
            elif period == "90d":
                days = 90
            else:
                days = 30

            start_date = end_date - timedelta(days=days)

            async with get_db_context() as session:
                trade_repo = TradeRepository()
                trades = await trade_repo.get_by_user_id(session, user_id)

                # Filter trades by period and bot if specified
                period_trades = [
                    t
                    for t in trades
                    if t.executed_at
                    and t.executed_at >= start_date
                    and (not bot_id or str(t.bot_id) == bot_id)
                ]

                # Calculate cumulative P&L over time
                chart_data = []
                cumulative_pnl = 0.0
                peak = 0.0

                # Group trades by day
                for i in range(days):
                    date = end_date - timedelta(days=days - i - 1)
                    day_start = datetime.combine(date.date(), datetime.min.time())
                    day_end = day_start + timedelta(days=1)

                    day_trades = [
                        t
                        for t in period_trades
                        if (t.executed_at or t.timestamp or t.created_at)
                        and day_start
                        <= (t.executed_at or t.timestamp or t.created_at)
                        < day_end
                    ]

                    # Add P&L for this day
                    day_pnl = sum((t.pnl or 0.0) for t in day_trades)
                    cumulative_pnl += day_pnl
                    peak = max(peak, cumulative_pnl)

                    # Calculate drawdown
                    drawdown = (peak - cumulative_pnl) / peak if peak > 0 else 0.0

                    chart_data.append(
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "drawdown": drawdown,
                            "value": cumulative_pnl,
                        }
                    )

                return chart_data
        except Exception as calc_error:
            logger.warning(f"Failed to calculate drawdown chart: {calc_error}")
            # Return empty data instead of mock data
            end_date = datetime.now()
            days = (
                30
                if period not in ["7d", "30d", "90d"]
                else (7 if period == "7d" else (30 if period == "30d" else 90))
            )
            return [
                {
                    "date": (end_date - timedelta(days=days - i - 1)).strftime(
                        "%Y-%m-%d"
                    ),
                    "drawdown": 0.0,
                    "value": 0.0,
                }
                for i in range(days)
            ]

        for i in range(days):
            date = end_date - timedelta(days=days - i - 1)

            # Mock price movement
            change = (i % 10 - 5) * 100.0
            current_value += change
            peak = max(peak, current_value)
            drawdown = (peak - current_value) / peak

            chart_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "drawdown": drawdown,
                    "portfolio_value": current_value,
                }
            )

        return chart_data
    except Exception as e:
        logger.error(f"Error getting drawdown chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get drawdown chart")


@router.get("/portfolio")
@cached(ttl=120, prefix="analytics_portfolio")
async def get_portfolio_analytics(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("30d", description="Time period (1d, 7d, 30d, 90d, 1y)"),
) -> PortfolioAnalytics:
    """Get portfolio analytics"""
    try:
        user_id = _get_user_id(current_user)
        analytics_result = await engine.analyze(
            {"user_id": user_id, "type": "portfolio", "period": period}
        )

        return PortfolioAnalytics(
            total_value=analytics_result.summary.get("total_value", 100000.0),
            total_pnl=analytics_result.summary.get("total_pnl", 5000.0),
            pnl_percentage=analytics_result.summary.get("pnl_percentage", 5.0),
            asset_allocation=analytics_result.details.get("asset_allocation", {}),
            performance_vs_benchmark=analytics_result.summary.get(
                "performance_vs_benchmark", 2.5
            ),
            volatility=analytics_result.summary.get("volatility", 0.15),
            sharpe_ratio=analytics_result.summary.get("sharpe_ratio", 1.8),
            max_drawdown=analytics_result.summary.get("max_drawdown", 1500.0),
            risk_adjusted_return=analytics_result.summary.get(
                "risk_adjusted_return", 1.2
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting portfolio analytics: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get portfolio analytics")


@router.get("/backtesting/{strategy_id}")
@cached(ttl=300, prefix="analytics_backtest")
async def get_backtesting_results(
    strategy_id: str,
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    backtest_id: str | None = Query(None, description="Specific backtest ID"),
) -> BacktestResult:
    """Get backtesting results for a strategy"""
    try:
        user_id = _get_user_id(current_user)
        analytics_result = await engine.analyze(
            {
                "user_id": user_id,
                "type": "backtesting",
                "strategy_id": strategy_id,
                "backtest_id": backtest_id,
            }
        )

        backtest_data = analytics_result.details.get("backtest", {})

        return BacktestResult(
            strategy_id=strategy_id,
            strategy_name=backtest_data.get("strategy_name", "Unknown Strategy"),
            total_return=backtest_data.get("total_return", 0.0),
            annualized_return=backtest_data.get("annualized_return", 0.0),
            volatility=backtest_data.get("volatility", 0.0),
            sharpe_ratio=backtest_data.get("sharpe_ratio", 0.0),
            max_drawdown=backtest_data.get("max_drawdown", 0.0),
            win_rate=backtest_data.get("win_rate", 0.0),
            total_trades=backtest_data.get("total_trades", 0),
            avg_trade_pnl=backtest_data.get("avg_trade_pnl", 0.0),
            start_date=datetime.fromisoformat(
                backtest_data.get("start_date", datetime.now().isoformat())
            ),
            end_date=datetime.fromisoformat(
                backtest_data.get("end_date", datetime.now().isoformat())
            ),
            initial_balance=backtest_data.get("initial_balance", 10000.0),
            final_balance=backtest_data.get("final_balance", 10000.0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting backtesting results: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get backtesting results")


@router.get("/backtesting/compare")
@cached(ttl=300, prefix="analytics_backtest_compare")
async def compare_backtesting_results(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    strategy_ids: list[str] = Query(..., description="List of strategy IDs to compare"),
    backtest_ids: list[str] | None = Query(
        None, description="Specific backtest IDs for each strategy"
    ),
) -> list[BacktestResult]:
    """Compare backtesting results across multiple strategies"""
    try:
        user_id = _get_user_id(current_user)
        comparison_results = []

        for i, strategy_id in enumerate(strategy_ids):
            backtest_id = (
                backtest_ids[i] if backtest_ids and i < len(backtest_ids) else None
            )
            analytics_result = await engine.analyze(
                {
                    "user_id": user_id,
                    "type": "backtesting",
                    "strategy_id": strategy_id,
                    "backtest_id": backtest_id,
                }
            )

            backtest_data = analytics_result.details.get("backtest", {})

            comparison_results.append(
                BacktestResult(
                    strategy_id=strategy_id,
                    strategy_name=backtest_data.get(
                        "strategy_name", f"Strategy {strategy_id}"
                    ),
                    total_return=backtest_data.get("total_return", 0.0),
                    annualized_return=backtest_data.get("annualized_return", 0.0),
                    volatility=backtest_data.get("volatility", 0.0),
                    sharpe_ratio=backtest_data.get("sharpe_ratio", 0.0),
                    max_drawdown=backtest_data.get("max_drawdown", 0.0),
                    win_rate=backtest_data.get("win_rate", 0.0),
                    total_trades=backtest_data.get("total_trades", 0),
                    avg_trade_pnl=backtest_data.get("avg_trade_pnl", 0.0),
                    start_date=datetime.fromisoformat(
                        backtest_data.get("start_date", datetime.now().isoformat())
                    ),
                    end_date=datetime.fromisoformat(
                        backtest_data.get("end_date", datetime.now().isoformat())
                    ),
                    initial_balance=backtest_data.get("initial_balance", 10000.0),
                    final_balance=backtest_data.get("final_balance", 10000.0),
                )
            )

        return comparison_results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error comparing backtesting results: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to compare backtesting results"
        )


@router.get("/backtesting/performance-metrics")
@cached(ttl=300, prefix="analytics_backtest_metrics")
async def get_backtesting_performance_metrics(
    strategy_id: str,
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    backtest_id: str | None = Query(None, description="Specific backtest ID"),
) -> dict[str, Any]:
    """Get detailed performance metrics for a backtest"""
    try:
        user_id = _get_user_id(current_user)
        analytics_result = await engine.analyze(
            {
                "user_id": user_id,
                "type": "backtesting",
                "strategy_id": strategy_id,
                "backtest_id": backtest_id,
            }
        )

        backtest_data = analytics_result.details.get("backtest", {})

        # Calculate additional metrics
        total_return = backtest_data.get("total_return", 0.0)
        volatility = backtest_data.get("volatility", 0.0)
        max_drawdown = backtest_data.get("max_drawdown", 0.0)
        initial_balance = backtest_data.get("initial_balance", 10000.0)
        final_balance = backtest_data.get(
            "final_balance", initial_balance * (1 + total_return)
        )

        # Risk-adjusted returns
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else float("inf")
        sortino_ratio = (
            total_return / volatility if volatility > 0 else float("inf")
        )  # Simplified

        return {
            "strategy_id": strategy_id,
            "backtest_id": backtest_id,
            "basic_metrics": {
                "total_return": total_return,
                "annualized_return": backtest_data.get(
                    "annualized_return", total_return
                ),
                "volatility": volatility,
                "sharpe_ratio": backtest_data.get("sharpe_ratio", 0.0),
                "max_drawdown": max_drawdown,
                "win_rate": backtest_data.get("win_rate", 0.0),
                "total_trades": backtest_data.get("total_trades", 0),
                "avg_trade_pnl": backtest_data.get("avg_trade_pnl", 0.0),
            },
            "risk_metrics": {
                "calmar_ratio": calmar_ratio,
                "sortino_ratio": sortino_ratio,
                "value_at_risk": -volatility * 1.645,  # Simplified VaR calculation
                "expected_shortfall": -volatility * 2.0,  # Simplified ES calculation
            },
            "portfolio_metrics": {
                "initial_balance": initial_balance,
                "final_balance": final_balance,
                "peak_balance": final_balance * (1 + max_drawdown),  # Simplified
                "recovery_factor": (
                    total_return / max_drawdown if max_drawdown > 0 else float("inf")
                ),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting backtesting performance metrics: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to get backtesting performance metrics"
        )


# ===== ENHANCED BUSINESS INTELLIGENCE DASHBOARD APIs =====


@router.get("/dashboard/summary")
@cached(ttl=60, prefix="analytics_dashboard_summary")
async def get_dashboard_summary(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    advanced_engine: Annotated[
        AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)
    ],
    monitor: Annotated[PerformanceMonitor, Depends(get_performance_monitor)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DashboardSummary:
    """Get comprehensive dashboard summary with real-time metrics"""
    try:
        user_id = _get_user_id(current_user)

        # Get portfolio analytics
        portfolio_result = await advanced_engine._analyze_portfolio(user_id, "1d")
        portfolio_data = portfolio_result.details if portfolio_result else {}

        # Get performance metrics from database
        performance_result = await engine.analyze(
            {"user_id": user_id, "type": "performance", "period": "1d"},
            db_session=db_session,
        )
        performance_data = (
            performance_result.get("details", {}) if performance_result else {}
        )

        # Get system health
        await monitor.get_system_health()

        # Calculate risk score (simplified)
        risk_score = min(abs(portfolio_data.get("volatility", 0.15)) * 100, 100)

        # Determine market sentiment (simplified)
        market_sentiment = "neutral"
        if portfolio_data.get("sharpe_ratio", 0) > 1.5:
            market_sentiment = "bullish"
        elif portfolio_data.get("sharpe_ratio", 0) < 0.5:
            market_sentiment = "bearish"

        return DashboardSummary(
            total_portfolio_value=portfolio_data.get("total_value", 100000.0),
            total_pnl_today=portfolio_data.get("total_pnl", 0.0),
            pnl_percentage_today=portfolio_data.get("pnl_percentage", 0.0),
            active_bots=performance_data.get("active_bots", 0),
            total_positions=portfolio_data.get("total_positions", 0),
            risk_score=risk_score,
            market_sentiment=market_sentiment,
            last_updated=datetime.now(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting dashboard summary: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")


@router.get("/dashboard/realtime")
async def get_realtime_metrics(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    monitor: Annotated[PerformanceMonitor, Depends(get_performance_monitor)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RealTimeMetrics:
    """Get real-time trading and performance metrics"""
    try:
        user_id = _get_user_id(current_user)

        # Get system metrics
        system_metrics = await monitor.collect_system_metrics()

        # Get trading performance (simplified real-time data)
        performance_result = await engine.analyze(
            {"user_id": user_id, "type": "performance", "period": "1d"}
        )
        performance_data = (
            performance_result.details.get("metrics", [{}])[0]
            if performance_result and performance_result.details.get("metrics")
            else {}
        )

        # Calculate daily P&L (simplified)
        daily_pnl = performance_data.get("total_pnl", 0.0)
        portfolio_value = performance_data.get("current_balance", 100000.0)
        daily_pnl_percent = (
            (daily_pnl / portfolio_value) * 100 if portfolio_value > 0 else 0
        )

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
            active_positions=performance_data.get("active_positions", 0),
            total_trades_today=performance_data.get("total_trades", 0),
            win_rate_today=performance_data.get("win_rate", 0.0),
            system_health=system_health,
            last_update=datetime.now(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting realtime metrics: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get realtime metrics")


@router.get("/dashboard/charts/portfolio-performance")
@cached(ttl=300, prefix="analytics_portfolio_chart")
async def get_portfolio_performance_chart(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("30d", description="Time period (1d, 7d, 30d, 90d, 1y)"),
) -> PerformanceChartData:
    """Get portfolio performance chart data optimized for visualization"""
    try:
        user_id = _get_user_id(current_user)

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
        dates = [
            (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days, 0, -1)
        ]

        # Get portfolio data over time (simplified - would use historical data)
        portfolio_values = []
        pnl_values = []
        base_value = 100000.0

        for _i in range(days):
            # Simulate portfolio growth with some volatility
            if PANDAS_AVAILABLE:
                change = np.random.normal(0.001, 0.02)  # Mean 0.1%, std 2%
            else:
                # Simple random fallback without numpy
                import random

                change = random.gauss(0.001, 0.02)
            base_value *= 1 + change
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
                    "type": "line",
                },
                {
                    "label": "Daily P&L",
                    "data": [round(p, 2) for p in pnl_values],
                    "borderColor": "rgb(255, 99, 132)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "type": "bar",
                },
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting portfolio performance chart: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to get portfolio performance chart"
        )


@router.get("/dashboard/charts/asset-allocation")
@cached(ttl=300, prefix="analytics_asset_allocation")
async def get_asset_allocation_chart(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[AssetAllocation]:
    """Get current asset allocation for pie chart visualization"""
    try:
        user_id = _get_user_id(current_user)

        # Get portfolio analytics
        portfolio_result = await engine._analyze_portfolio(user_id, "1d")
        portfolio_data = portfolio_result.details if portfolio_result else {}

        # Get real asset allocation from portfolio
        try:
            # Get asset allocation from portfolio data if available
            # Note: Full integration would require calling portfolio API endpoint
            # For now, calculate from available portfolio_data positions
            if portfolio_data and isinstance(portfolio_data, dict):
                positions = portfolio_data.get("positions", {})
                if positions:
                    # Convert positions to allocation format
                    allocation = []
                    total_value = sum(
                        pos.get("totalValue", 0.0) if isinstance(pos, dict) else 0.0
                        for pos in positions.values()
                    )
                    if total_value > 0:
                        for asset, pos in positions.items():
                            if isinstance(pos, dict):
                                value = pos.get("totalValue", 0.0)
                                allocation.append(
                                    {
                                        "asset": asset,
                                        "allocation": (value / total_value) * 100,
                                        "value": value,
                                    }
                                )
                    return allocation
            return []
        except Exception as e:
            logger.warning(f"Failed to get asset allocation: {e}")
            # Return empty allocation instead of mock data
            return []
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting asset allocation chart: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to get asset allocation chart"
        )


@router.get("/dashboard/charts/correlation-matrix")
async def get_correlation_matrix_data(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    assets: list[str] = Query(None, description="List of asset symbols"),
) -> CorrelationMatrix:
    """Get correlation matrix data for risk analysis visualization"""
    try:
        user_id = _get_user_id(current_user)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting correlation matrix: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get correlation matrix")


@router.get("/dashboard/charts/risk-metrics")
@cached(ttl=300, prefix="analytics_risk_chart")
async def get_risk_metrics_chart(
    engine: Annotated[AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("30d", description="Time period"),
) -> PerformanceChartData:
    """Get risk metrics chart data for visualization"""
    try:
        user_id = _get_user_id(current_user)

        # Get risk analysis
        risk_result = await engine._analyze_risk(user_id)
        risk_data = risk_result.summary if risk_result else {}

        # Generate historical risk metrics (simplified)
        days = 30 if period == "30d" else 7 if period == "7d" else 30
        dates = [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days, 0, -1)
        ]

        # Simulate risk metrics over time
        if PANDAS_AVAILABLE:
            volatility_data = [
                risk_data.get("volatility", 0.15) + np.random.normal(0, 0.02)
                for _ in range(days)
            ]
            sharpe_data = [
                risk_data.get("sharpe_ratio", 1.5) + np.random.normal(0, 0.3)
                for _ in range(days)
            ]
        else:
            import random

            volatility_data = [
                risk_data.get("volatility", 0.15) + random.gauss(0, 0.02)
                for _ in range(days)
            ]
            sharpe_data = [
                risk_data.get("sharpe_ratio", 1.5) + random.gauss(0, 0.3)
                for _ in range(days)
            ]
        var_data = [
            -abs(v) * 1.645 * 100 for v in volatility_data
        ]  # VaR at 95% confidence

        return PerformanceChartData(
            labels=dates,
            datasets=[
                {
                    "label": "Volatility",
                    "data": [round(v * 100, 2) for v in volatility_data],
                    "borderColor": "rgb(255, 159, 64)",
                    "backgroundColor": "rgba(255, 159, 64, 0.2)",
                    "type": "line",
                },
                {
                    "label": "Value at Risk (95%)",
                    "data": [round(v, 2) for v in var_data],
                    "borderColor": "rgb(255, 99, 132)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "type": "line",
                },
                {
                    "label": "Sharpe Ratio",
                    "data": [round(s, 2) for s in sharpe_data],
                    "borderColor": "rgb(54, 162, 235)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "type": "line",
                },
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting risk metrics chart: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get risk metrics chart")


@router.get("/dashboard/charts/bot-performance-comparison")
@cached(ttl=300, prefix="analytics_bot_comparison")
async def get_bot_performance_comparison_chart(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("30d", description="Time period"),
) -> PerformanceChartData:
    """Get bot performance comparison chart data"""
    try:
        user_id = _get_user_id(current_user)

        # Get performance data for all bots
        performance_result = await engine.analyze(
            {"user_id": user_id, "type": "performance", "period": period}
        )
        metrics_data = performance_result.details.get("metrics", [])

        # Prepare data for chart
        bot_names = [
            m.get("bot_name", f"Bot {m.get('bot_id', 'unknown')}") for m in metrics_data
        ]
        win_rates = [m.get("win_rate", 0) * 100 for m in metrics_data]
        total_pnl = [m.get("total_pnl", 0) for m in metrics_data]
        [m.get("sharpe_ratio", 0) for m in metrics_data]

        return PerformanceChartData(
            labels=bot_names,
            datasets=[
                {
                    "label": "Win Rate (%)",
                    "data": [round(w, 1) for w in win_rates],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "type": "bar",
                },
                {
                    "label": "Total P&L ($)",
                    "data": [round(p, 2) for p in total_pnl],
                    "backgroundColor": "rgba(255, 99, 132, 0.6)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "type": "bar",
                },
            ],
        )
    except Exception as e:
        logger.error(f"Error getting bot performance comparison chart: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get bot performance comparison chart"
        )


@router.get("/dashboard/charts/trade-distribution")
@cached(ttl=300, prefix="analytics_trade_distribution")
async def get_trade_distribution_chart(
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("30d", description="Time period"),
) -> PerformanceChartData:
    """Get trade distribution chart data (by hour, day, symbol)"""
    try:
        user_id = _get_user_id(current_user)

        # Get real trade distribution from database
        try:
            from ..database import get_db_context
            from ..repositories.trade_repository import TradeRepository

            hours = [f"{i:02d}:00" for i in range(24)]
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            symbols = ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "DOT/USD"]

            async with get_db_context() as session:
                trade_repo = TradeRepository()
                # Get trades for user with reasonable limit for chart calculations
                # Limit to last 1000 trades to prevent performance issues
                trades = await trade_repo.get_by_user(
                    session, int(user_id), skip=0, limit=1000
                )

                # Calculate trades by hour
                trades_by_hour = [0] * 24
                for trade in trades:
                    if trade.executed_at:
                        hour = trade.executed_at.hour
                        trades_by_hour[hour] += 1

                # Calculate trades by day of week
                trades_by_day = [0] * 7
                for trade in trades:
                    if trade.executed_at:
                        day_of_week = trade.executed_at.weekday()
                        trades_by_day[day_of_week] += 1

                # Calculate trades by symbol
                trades_by_symbol = [0] * len(symbols)
                for trade in trades:
                    if trade.pair:
                        for idx, symbol in enumerate(symbols):
                            if symbol in trade.pair or trade.pair in symbol:
                                trades_by_symbol[idx] += 1
                                break

                return PerformanceChartData(
                    labels=hours + days + symbols,
                    datasets=[
                        {
                            "label": "Trades by Hour",
                            "data": trades_by_hour + [0] * (len(days) + len(symbols)),
                            "backgroundColor": "rgba(153, 102, 255, 0.6)",
                            "borderColor": "rgba(153, 102, 255, 1)",
                            "type": "bar",
                        },
                        {
                            "label": "Trades by Day",
                            "data": [0] * len(hours)
                            + trades_by_day
                            + [0] * len(symbols),
                            "backgroundColor": "rgba(255, 159, 64, 0.6)",
                            "borderColor": "rgba(255, 159, 64, 1)",
                            "type": "bar",
                        },
                        {
                            "label": "Trades by Symbol",
                            "data": [0] * (len(hours) + len(days)) + trades_by_symbol,
                            "backgroundColor": "rgba(54, 162, 235, 0.6)",
                            "borderColor": "rgba(54, 162, 235, 1)",
                            "type": "bar",
                        },
                    ],
                )
        except Exception as e:
            logger.warning(f"Failed to get trade distribution: {e}")
            # Return empty data instead of mock data
            hours = [f"{i:02d}:00" for i in range(24)]
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            symbols = ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "DOT/USD"]
            return PerformanceChartData(
                labels=hours + days + symbols,
                datasets=[
                    {
                        "label": "Trades by Hour",
                        "data": [0] * (len(hours) + len(days) + len(symbols)),
                        "backgroundColor": "rgba(153, 102, 255, 0.6)",
                        "borderColor": "rgba(153, 102, 255, 1)",
                        "type": "bar",
                    },
                ],
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting trade distribution chart: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to get trade distribution chart"
        )


@router.get("/dashboard/kpis")
@cached(ttl=60, prefix="analytics_kpis")
async def get_key_performance_indicators(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    advanced_engine: Annotated[
        AdvancedAnalyticsEngine, Depends(get_advanced_analytics_engine)
    ],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("30d", description="Time period"),
) -> dict[str, Any]:
    """Get key performance indicators for dashboard"""
    try:
        user_id = _get_user_id(current_user)

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
                "value": portfolio_data.get("total_value", 100000.0),
                "change": portfolio_data.get("total_pnl", 0.0),
                "change_percent": portfolio_data.get("pnl_percentage", 0.0),
                "format": "currency",
            },
            "total_pnl": {
                "value": summary_data.get("total_pnl", 0.0),
                "change": summary_data.get("total_pnl", 0.0) * 0.1,  # Mock daily change
                "change_percent": 10.0,  # Mock percentage
                "format": "currency",
            },
            "win_rate": {
                "value": summary_data.get("win_rate", 0.0) * 100,
                "change": 2.5,  # Mock improvement
                "change_percent": 2.5,
                "format": "percentage",
            },
            "active_bots": {
                "value": summary_data.get("active_bots", 0),
                "change": 1,
                "change_percent": 25.0,  # Mock increase
                "format": "number",
            },
            "sharpe_ratio": {
                "value": risk_data.get("sharpe_ratio", 0.0),
                "change": 0.1,
                "change_percent": 7.1,
                "format": "decimal",
            },
            "max_drawdown": {
                "value": abs(risk_data.get("max_drawdown", 0.0)) * 100,
                "change": -2.0,  # Mock improvement (reduction)
                "change_percent": -20.0,
                "format": "percentage",
            },
        }

        return kpis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting KPIs: {e}", exc_info=True, extra={"user_id": user_id}
        )
        raise HTTPException(status_code=500, detail="Failed to get KPIs")


@router.get("/dashboard/alerts-summary")
async def get_alerts_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get summary of active alerts and notifications"""
    try:
        user_id = _get_user_id(current_user)

        # Get real alerts from database
        try:
            from sqlalchemy import desc, select

            from ..database import get_db_context
            from ..models.risk_alert import RiskAlert

            async with get_db_context() as session:
                # Query alerts directly if repository doesn't exist
                query = (
                    select(RiskAlert)
                    .where(RiskAlert.user_id == str(user_id))
                    .order_by(desc(RiskAlert.created_at))
                    .limit(50)
                )
                result = await session.execute(query)
                alerts_list = result.scalars().all()

                # Count alerts by level
                alerts = {
                    "critical": sum(1 for a in alerts_list if a.severity == "high"),
                    "warning": sum(1 for a in alerts_list if a.severity == "medium"),
                    "info": sum(1 for a in alerts_list if a.severity == "low"),
                    "total_unread": len([a for a in alerts_list if not a.read]),
                }

                # Get recent alerts
                recent_alerts = [
                    {
                        "id": f"alert-{a.id}",
                        "title": a.alert_type or "Alert",
                        "message": a.message or "",
                        "level": "critical"
                        if a.severity == "high"
                        else ("warning" if a.severity == "medium" else "info"),
                        "timestamp": a.created_at.isoformat()
                        if hasattr(a.created_at, "isoformat")
                        else str(a.created_at),
                        "category": a.alert_type or "general",
                    }
                    for a in alerts_list[:10]
                ]
        except Exception as e:
            logger.warning(f"Failed to get alerts: {e}")
            # Return empty alerts instead of mock data
            alerts = {"critical": 0, "warning": 0, "info": 0, "total_unread": 0}
            recent_alerts = []

        return {"alert_counts": alerts, "recent_alerts": recent_alerts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting alerts summary: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to get alerts summary")


# ===== PERFORMANCE ATTRIBUTION API =====


class AttributionData(BaseModel):
    strategy: str
    alpha: float
    beta: float
    sharpe: float
    informationRatio: float
    contribution: float
    trades: int
    winRate: float
    avgReturn: float


class CumulativeReturn(BaseModel):
    month: str
    returns: float
    benchmark: float
    alpha: float


class FactorAnalysis(BaseModel):
    factor: str
    exposure: float
    contribution: float
    color: str


class PerformanceAttributionResponse(BaseModel):
    attribution: list[AttributionData]
    cumulativeReturns: list[CumulativeReturn]
    factorAnalysis: list[FactorAnalysis]


@router.get(
    "/performance/attribution",
    response_model=PerformanceAttributionResponse,
    summary="Get performance attribution analysis",
    description="""
    Get detailed performance attribution analysis by strategy/bot.
    
    This endpoint provides:
    - Attribution metrics (alpha, beta, Sharpe ratio, information ratio) per strategy
    - Cumulative returns over time with benchmark comparison
    - Factor analysis showing exposure and contribution
    
    **Example Response:**
    ```json
    {
      "attribution": [
        {
          "strategy": "ML Enhanced",
          "alpha": 8.5,
          "beta": 1.2,
          "sharpe": 2.1,
          "informationRatio": 1.8,
          "contribution": 45.0,
          "trades": 120,
          "winRate": 68.0,
          "avgReturn": 3.2
        }
      ],
      "cumulativeReturns": [
        {
          "month": "2024-01",
          "returns": 0.15,
          "benchmark": 0.10,
          "alpha": 0.05
        }
      ],
      "factorAnalysis": [
        {
          "factor": "Momentum",
          "exposure": 0.8,
          "contribution": 12.5,
          "color": "#3b82f6"
        }
      ]
    }
    ```
    """,
)
@cached(ttl=300, prefix="analytics_performance_attribution")
async def get_performance_attribution(
    engine: Annotated[AnalyticsEngine, Depends(get_analytics_engine)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    period: str = Query("1y", description="Time period (1d, 7d, 30d, 90d, 1y)"),
) -> PerformanceAttributionResponse:
    """Get performance attribution analysis by strategy/bot"""
    try:
        import calendar

        from sqlalchemy import and_, select

        from ..models.trade import Trade

        user_id = _get_user_id(current_user)

        # Parse period to get start date
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
            start_date = end_date - timedelta(days=365)

        # Get all trades for the user in the period with eager loading to prevent N+1 queries
        from sqlalchemy.orm import joinedload

        trades_query = (
            select(Trade)
            .where(
                and_(
                    Trade.user_id == user_id,
                    Trade.executed_at >= start_date,
                    Trade.executed_at <= end_date,
                    Trade.status == "completed",
                )
            )
            .options(joinedload(Trade.bot))  # Eager load bot to prevent N+1 queries
            .limit(1000)  # Limit to prevent performance issues
        )
        trades_result = await db_session.execute(trades_query)
        trades = list(trades_result.scalars().all())

        if not trades:
            # Return empty data structure if no trades
            return PerformanceAttributionResponse(
                attribution=[],
                cumulativeReturns=[],
                factorAnalysis=[],
            )

        # Group trades by strategy/bot (bot is already loaded, no N+1 query)
        strategy_trades: dict[str, list[Trade]] = {}
        for trade in trades:
            # Get strategy name from bot or use default
            strategy_name = "Manual Trading"
            if trade.bot_id and trade.bot:
                strategy_name = trade.bot.strategy or "Unknown Strategy"
            else:
                strategy_name = "Manual Trading"

            if strategy_name not in strategy_trades:
                strategy_trades[strategy_name] = []
            strategy_trades[strategy_name].append(trade)

        # Calculate attribution metrics for each strategy
        attribution_list = []
        total_portfolio_pnl = sum(t.pnl or 0.0 for t in trades)
        total_trades_count = len(trades)
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        (
            len(winning_trades) / total_trades_count if total_trades_count > 0 else 0.0
        )

        # Calculate benchmark return (simplified - using average market return)
        # In production, this would use actual market index data
        benchmark_return = 0.15  # 15% annual benchmark (simplified)
        period_days = (end_date - start_date).days
        benchmark_period_return = (benchmark_return / 365) * period_days

        for strategy_name, strategy_trades_list in strategy_trades.items():
            if not strategy_trades_list:
                continue

            strategy_pnl = sum(t.pnl or 0.0 for t in strategy_trades_list)
            strategy_trades_count = len(strategy_trades_list)
            strategy_winning = [t for t in strategy_trades_list if t.pnl and t.pnl > 0]
            strategy_win_rate = (
                len(strategy_winning) / strategy_trades_count
                if strategy_trades_count > 0
                else 0.0
            )

            # Calculate average return per trade
            strategy_avg_return = (
                strategy_pnl / strategy_trades_count
                if strategy_trades_count > 0
                else 0.0
            )

            # Calculate contribution percentage
            contribution_pct = (
                (strategy_pnl / total_portfolio_pnl * 100)
                if total_portfolio_pnl != 0
                else 0.0
            )

            # Calculate strategy return
            strategy_total_cost = sum(t.cost for t in strategy_trades_list)
            strategy_return = (
                (strategy_pnl / strategy_total_cost * 100)
                if strategy_total_cost > 0
                else 0.0
            )

            # Calculate alpha (excess return over benchmark)
            alpha = strategy_return - benchmark_period_return

            # Calculate beta (simplified - correlation with market)
            # In production, this would use actual market correlation
            beta = 1.0  # Default beta

            # Calculate Sharpe ratio (simplified)
            # Sharpe = (Return - Risk-free rate) / Volatility
            # Using simplified calculation
            if strategy_trades_count > 1:
                returns = [t.pnl or 0.0 for t in strategy_trades_list]
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                std_dev = variance**0.5
                sharpe = (avg_return / std_dev) if std_dev > 0 else 0.0
            else:
                sharpe = 0.0

            # Calculate Information Ratio (alpha / tracking error)
            # Simplified calculation
            tracking_error = abs(strategy_return - benchmark_period_return)
            information_ratio = (alpha / tracking_error) if tracking_error > 0 else 0.0

            attribution_list.append(
                AttributionData(
                    strategy=strategy_name,
                    alpha=round(alpha, 2),
                    beta=round(beta, 2),
                    sharpe=round(sharpe, 2),
                    informationRatio=round(information_ratio, 2),
                    contribution=round(contribution_pct, 2),
                    trades=strategy_trades_count,
                    winRate=round(strategy_win_rate * 100, 2),
                    avgReturn=round(strategy_avg_return, 2),
                )
            )

        # Sort by contribution (descending)
        attribution_list.sort(key=lambda x: x.contribution, reverse=True)

        # Calculate cumulative returns by month
        cumulative_returns = []
        if period == "1y" and trades:
            # Group trades by month
            monthly_trades: dict[str, list[Trade]] = {}
            for trade in trades:
                month_key = trade.executed_at.strftime("%Y-%m")
                if month_key not in monthly_trades:
                    monthly_trades[month_key] = []
                monthly_trades[month_key].append(trade)

            # Calculate cumulative returns
            cumulative_pnl = 0.0
            cumulative_benchmark = 0.0
            months = sorted(monthly_trades.keys())

            for _i, month_key in enumerate(months):
                month_trades = monthly_trades[month_key]
                month_pnl = sum(t.pnl or 0.0 for t in month_trades)
                cumulative_pnl += month_pnl

                # Calculate month return percentage
                month_cost = sum(t.cost for t in month_trades)
                month_return = (month_pnl / month_cost * 100) if month_cost > 0 else 0.0

                # Benchmark return for month (simplified)
                month_benchmark_return = benchmark_return / 12  # Monthly benchmark
                cumulative_benchmark += month_benchmark_return

                # Calculate alpha
                month_alpha = month_return - month_benchmark_return

                # Get month name
                year, month_num = month_key.split("-")
                month_name = calendar.month_abbr[int(month_num)]

                cumulative_returns.append(
                    CumulativeReturn(
                        month=month_name,
                        returns=round(cumulative_pnl, 2),
                        benchmark=round(cumulative_benchmark, 2),
                        alpha=round(month_alpha, 2),
                    )
                )
        else:
            # For shorter periods, use weekly or daily data
            # Simplified: just show overall returns
            total_return = total_portfolio_pnl
            period_benchmark = benchmark_period_return
            period_alpha = total_return - period_benchmark

            cumulative_returns.append(
                CumulativeReturn(
                    month=period,
                    returns=round(total_return, 2),
                    benchmark=round(period_benchmark, 2),
                    alpha=round(period_alpha, 2),
                )
            )

        # Calculate factor analysis (simplified)
        # In production, this would use actual factor models (Fama-French, etc.)
        factor_analysis = []
        if attribution_list:
            # Calculate momentum factor (based on win rate)
            momentum_exposure = (
                sum(a.winRate / 100 for a in attribution_list) / len(attribution_list)
                if attribution_list
                else 0.0
            )
            momentum_contribution = (
                sum(a.contribution for a in attribution_list if a.winRate > 60) / 100
                if attribution_list
                else 0.0
            )

            # Calculate value factor (based on alpha)
            value_exposure = (
                sum(max(0, a.alpha) for a in attribution_list) / len(attribution_list)
                if attribution_list
                else 0.0
            )
            value_contribution = (
                sum(a.contribution for a in attribution_list if a.alpha > 0) / 100
                if attribution_list
                else 0.0
            )

            # Calculate size factor (based on trade count)
            avg_trades = (
                sum(a.trades for a in attribution_list) / len(attribution_list)
                if attribution_list
                else 0.0
            )
            size_exposure = min(1.0, avg_trades / 100)  # Normalize
            size_contribution = (
                sum(a.contribution for a in attribution_list if a.trades > avg_trades)
                / 100
                if attribution_list
                else 0.0
            )

            # Calculate volatility factor (inverse of Sharpe)
            avg_sharpe = (
                sum(a.sharpe for a in attribution_list) / len(attribution_list)
                if attribution_list
                else 0.0
            )
            volatility_exposure = -0.15 if avg_sharpe < 1.0 else 0.15
            volatility_contribution = -2.1 if avg_sharpe < 1.0 else 2.1

            # Calculate quality factor (based on information ratio)
            quality_exposure = (
                sum(a.informationRatio / 2.0 for a in attribution_list)
                / len(attribution_list)
                if attribution_list
                else 0.0
            )
            quality_contribution = (
                sum(
                    a.contribution for a in attribution_list if a.informationRatio > 1.0
                )
                / 100
                if attribution_list
                else 0.0
            )

            factor_analysis = [
                FactorAnalysis(
                    factor="Momentum",
                    exposure=round(momentum_exposure, 2),
                    contribution=round(momentum_contribution * 100, 1),
                    color="#8884d8",
                ),
                FactorAnalysis(
                    factor="Value",
                    exposure=round(value_exposure / 10, 2),
                    contribution=round(value_contribution * 100, 1),
                    color="#82ca9d",
                ),
                FactorAnalysis(
                    factor="Size",
                    exposure=round(size_exposure, 2),
                    contribution=round(size_contribution * 100, 1),
                    color="#ffc658",
                ),
                FactorAnalysis(
                    factor="Volatility",
                    exposure=round(volatility_exposure, 2),
                    contribution=round(volatility_contribution, 1),
                    color="#ff7c7c",
                ),
                FactorAnalysis(
                    factor="Quality",
                    exposure=round(quality_exposure, 2),
                    contribution=round(quality_contribution * 100, 1),
                    color="#8dd1e1",
                ),
            ]

        return PerformanceAttributionResponse(
            attribution=attribution_list,
            cumulativeReturns=cumulative_returns,
            factorAnalysis=factor_analysis,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting performance attribution: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to get performance attribution"
        )
