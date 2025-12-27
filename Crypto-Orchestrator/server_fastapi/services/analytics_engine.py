from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


class PerformanceMetrics(BaseModel):
    botId: str
    period: str
    totalReturn: float
    sharpeRatio: float
    maxDrawdown: float
    winRate: float
    averageWin: float
    averageLoss: float
    profitFactor: float
    totalTrades: int


@dataclass
class Trade:
    timestamp: int
    side: str
    total: float
    totalWithFee: float = 0.0
    fee: float = 0.0
    pair: str = ""


@dataclass
class BotConfig:
    id: str
    name: str


class AnalyticsEngine:
    def __init__(self, storage=None):
        self.storage = storage

    async def analyze(self, params: Dict[str, Any], db_session=None) -> Dict[str, Any]:
        """Analyze data based on type and parameters"""
        analysis_type = params.get("type")
        user_id = params.get("user_id")

        if analysis_type == "summary":
            return await self._analyze_summary(user_id, db_session)
        elif analysis_type == "performance":
            bot_id = params.get("bot_id")
            period = params.get("period", "30d")
            return await self._analyze_performance(user_id, bot_id, period, db_session)
        elif analysis_type == "pnl_chart":
            bot_id = params.get("bot_id")
            period = params.get("period", "30d")
            return await self._analyze_pnl_chart(user_id, bot_id, period, db_session)
        elif analysis_type == "dashboard":
            return await self._analyze_dashboard(user_id, db_session)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

    async def _analyze_dashboard(self, user_id: int, db_session=None) -> Dict[str, Any]:
        """Analyze dashboard data for summary view using real database data"""
        try:
            from sqlalchemy import select, func
            from sqlalchemy.ext.asyncio import AsyncSession
            from ..models.trade import Trade
            from ..models.bot import Bot

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._analyze_dashboard(user_id, session)

            # Get real bot count
            bot_count_query = select(func.count(Bot.id)).where(Bot.user_id == user_id)
            bot_result = await db_session.execute(bot_count_query)
            total_bots = bot_result.scalar() or 0

            active_bots_query = select(func.count(Bot.id)).where(
                Bot.user_id == user_id, Bot.active == True
            )
            active_result = await db_session.execute(active_bots_query)
            active_bots = active_result.scalar() or 0

            # Get real trade statistics
            trades_query = select(Trade).where(Trade.user_id == user_id)
            trades_result = await db_session.execute(trades_query)
            all_trades = list(trades_result.scalars().all())

            total_trades = len(all_trades)

            # Calculate total P&L
            total_pnl = sum(
                trade.pnl or 0.0 for trade in all_trades if trade.pnl is not None
            )

            # Calculate win rate
            winning_trades = [t for t in all_trades if t.pnl and t.pnl > 0]
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0

            # Get bot performance metrics
            bot_metrics = []
            bots_query = select(Bot).where(Bot.user_id == user_id)
            bots_result = await db_session.execute(bots_query)
            bots = list(bots_result.scalars().all())

            best_bot_id = None
            worst_bot_id = None
            best_pnl = float("-inf")
            worst_pnl = float("inf")

            for bot in bots:
                bot_trades = [t for t in all_trades if t.bot_id == bot.id]
                if not bot_trades:
                    continue

                bot_pnl = sum(t.pnl or 0.0 for t in bot_trades if t.pnl is not None)
                winning = [t for t in bot_trades if t.pnl and t.pnl > 0]
                losing = [t for t in bot_trades if t.pnl and t.pnl < 0]

                if bot_pnl > best_pnl:
                    best_pnl = bot_pnl
                    best_bot_id = bot.id
                if bot_pnl < worst_pnl:
                    worst_pnl = bot_pnl
                    worst_bot_id = bot.id

                bot_win_rate = len(winning) / len(bot_trades) if bot_trades else 0.0
                avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0.0
                avg_loss = (
                    sum(abs(t.pnl) for t in losing) / len(losing) if losing else 0.0
                )

                # Calculate max drawdown (simplified)
                equity_curve = []
                running_pnl = 0.0
                for trade in sorted(bot_trades, key=lambda t: t.executed_at):
                    running_pnl += trade.pnl or 0.0
                    equity_curve.append(running_pnl)

                max_drawdown = 0.0
                if equity_curve:
                    peak = equity_curve[0]
                    for equity in equity_curve:
                        if equity > peak:
                            peak = equity
                        drawdown = (peak - equity) / peak if peak > 0 else 0.0
                        max_drawdown = max(max_drawdown, drawdown)

                bot_metrics.append(
                    {
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "total_trades": len(bot_trades),
                        "winning_trades": len(winning),
                        "losing_trades": len(losing),
                        "win_rate": bot_win_rate,
                        "total_pnl": bot_pnl,
                        "max_drawdown": max_drawdown,
                        "sharpe_ratio": 0.0,  # Would need more complex calculation
                        "current_balance": 0.0,  # Would need portfolio service
                    }
                )

            dashboard_data = {
                "summary": {
                    "total_bots": total_bots,
                    "active_bots": active_bots,
                    "total_trades": total_trades,
                    "total_pnl": total_pnl,
                    "win_rate": win_rate,
                    "best_performing_bot": best_bot_id,
                    "worst_performing_bot": worst_bot_id,
                },
                "details": {"metrics": bot_metrics, "chart_data": []},
            }

            return dashboard_data

        except Exception as e:
            logger.error(
                f"Error analyzing dashboard for user {user_id}: {e}", exc_info=True
            )
            # In production, return empty data instead of mock
            from ..config.settings import get_settings

            settings = get_settings()
            if settings.production_mode or settings.is_production:
                return {
                    "summary": {
                        "total_bots": 0,
                        "active_bots": 0,
                        "total_trades": 0,
                        "total_pnl": 0.0,
                        "win_rate": 0.0,
                        "best_performing_bot": None,
                        "worst_performing_bot": None,
                    },
                    "details": {"metrics": [], "chart_data": []},
                }
            else:
                # Development fallback only
                return {
                    "summary": {
                        "total_bots": 0,
                        "active_bots": 0,
                        "total_trades": 0,
                        "total_pnl": 0.0,
                        "win_rate": 0.0,
                        "best_performing_bot": None,
                        "worst_performing_bot": None,
                    },
                    "details": {"metrics": [], "chart_data": []},
                }

    async def calculate_performance_metrics(
        self, bot_id: str, period: str = "all", db_session=None
    ) -> PerformanceMetrics:
        """Calculate performance metrics from real database data"""
        trades = await self._get_trades(bot_id, db_session=db_session)
        bot = await self._get_bot(bot_id, db_session=db_session)

        if not bot or not trades:
            return PerformanceMetrics(
                botId=bot_id,
                period=period,
                totalReturn=0,
                sharpeRatio=0,
                maxDrawdown=0,
                winRate=0,
                averageWin=0,
                averageLoss=0,
                profitFactor=0,
                totalTrades=0,
            )

        # Filter trades by period
        filtered_trades = self._filter_trades_by_period(trades, period)

        if not filtered_trades:
            return PerformanceMetrics(
                botId=bot_id,
                period=period,
                totalReturn=0,
                sharpeRatio=0,
                maxDrawdown=0,
                winRate=0,
                averageWin=0,
                averageLoss=0,
                profitFactor=0,
                totalTrades=0,
            )

        # Calculate metrics
        total_return = self._calculate_total_return(filtered_trades)
        sharpe_ratio = self._calculate_sharpe_ratio(filtered_trades)
        max_drawdown = self._calculate_max_drawdown(filtered_trades)
        win_rate = self._calculate_win_rate(filtered_trades)
        average_win = self._calculate_average_win(filtered_trades)
        average_loss = self._calculate_average_loss(filtered_trades)
        profit_factor = self._calculate_profit_factor(filtered_trades)

        metrics = PerformanceMetrics(
            botId=bot_id,
            period=period,
            totalReturn=total_return,
            sharpeRatio=sharpe_ratio,
            maxDrawdown=max_drawdown,
            winRate=win_rate,
            averageWin=average_win,
            averageLoss=average_loss,
            profitFactor=profit_factor,
            totalTrades=len(filtered_trades),
        )

        # Save to storage (mock)
        await self._save_performance_metrics(metrics)

        return metrics

    def _filter_trades_by_period(self, trades: List[Trade], period: str) -> List[Trade]:
        now = datetime.now().timestamp() * 1000
        start_time = 0

        if period == "1d":
            start_time = now - 24 * 60 * 60 * 1000
        elif period == "7d":
            start_time = now - 7 * 24 * 60 * 60 * 1000
        elif period == "30d":
            start_time = now - 30 * 24 * 60 * 60 * 1000
        elif period == "90d":
            start_time = now - 90 * 24 * 60 * 60 * 1000
        elif period == "1y":
            start_time = now - 365 * 24 * 60 * 60 * 1000
        else:
            return trades  # 'all' period

        return [trade for trade in trades if trade.timestamp >= start_time]

    def _calculate_total_return(self, trades: List[Trade]) -> float:
        initial_investment = 100000  # Assume starting balance
        current_balance = initial_investment

        for trade in trades:
            if trade.side == "buy":
                current_balance -= trade.totalWithFee
            else:
                current_balance += trade.total - trade.fee

        return (current_balance - initial_investment) / initial_investment

    def _calculate_sharpe_ratio(self, trades: List[Trade]) -> float:
        if len(trades) < 2:
            return 0

        # Group trades by day
        daily_returns = self._calculate_daily_returns(trades)

        if not daily_returns:
            return 0

        avg_return = sum(daily_returns) / len(daily_returns)
        variance = sum((ret - avg_return) ** 2 for ret in daily_returns) / len(
            daily_returns
        )
        std_dev = math.sqrt(variance)

        # Assume risk-free rate of 0.02 (2%)
        risk_free_rate = 0.02 / 365  # Daily risk-free rate

        if std_dev == 0:
            return 0

        return (avg_return - risk_free_rate) / std_dev * math.sqrt(365)  # Annualized

    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        if not trades:
            return 0

        equity_curve = self._calculate_equity_curve(trades)
        peak = equity_curve[0]
        max_drawdown = 0

        for equity in equity_curve:
            if equity > peak:
                peak = equity

            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_win_rate(self, trades: List[Trade]) -> float:
        if not trades:
            return 0

        winning_trades = [
            trade for trade in trades if trade.side == "sell" and trade.total > 0
        ]

        return len(winning_trades) / len(trades)

    def _calculate_average_win(self, trades: List[Trade]) -> float:
        winning_trades = [
            trade for trade in trades if trade.side == "sell" and trade.total > 0
        ]

        if not winning_trades:
            return 0

        total_wins = sum(trade.total for trade in winning_trades)
        return total_wins / len(winning_trades)

    def _calculate_average_loss(self, trades: List[Trade]) -> float:
        losing_trades = [
            trade for trade in trades if trade.side == "sell" and trade.total < 0
        ]

        if not losing_trades:
            return 0

        total_losses = sum(abs(trade.total) for trade in losing_trades)
        return total_losses / len(losing_trades)

    def _calculate_profit_factor(self, trades: List[Trade]) -> float:
        gross_profit = sum(
            trade.total for trade in trades if trade.side == "sell" and trade.total > 0
        )

        gross_loss = abs(
            sum(
                trade.total
                for trade in trades
                if trade.side == "sell" and trade.total < 0
            )
        )

        if gross_loss > 0:
            return gross_profit / gross_loss
        elif gross_profit > 0:
            return float("inf")
        else:
            return 0

    def _calculate_daily_returns(self, trades: List[Trade]) -> List[float]:
        daily_pnl = {}
        initial_balance = 100000

        for trade in trades:
            day = trade.timestamp // (24 * 60 * 60 * 1000)
            pnl = (
                -trade.totalWithFee if trade.side == "buy" else trade.total - trade.fee
            )

            daily_pnl[day] = daily_pnl.get(day, 0) + pnl

        daily_returns = []
        for day, pnl in sorted(daily_pnl.items()):
            daily_return = pnl / initial_balance
            daily_returns.append(daily_return)

        return daily_returns

    def _calculate_equity_curve(self, trades: List[Trade]) -> List[float]:
        initial_balance = 100000
        balance = initial_balance
        equity = [balance]

        # Sort trades by timestamp
        sorted_trades = sorted(trades, key=lambda t: t.timestamp)

        for trade in sorted_trades:
            if trade.side == "buy":
                balance -= trade.totalWithFee
            else:
                balance += trade.total - trade.fee
            equity.append(balance)

        return equity

    async def get_performance_comparison(
        self, bot_ids: List[str], period: str = "30d"
    ) -> Dict[str, PerformanceMetrics]:
        comparisons = {}

        for bot_id in bot_ids:
            comparisons[bot_id] = await self.calculate_performance_metrics(
                bot_id, period
            )

        return comparisons

    async def generate_performance_report(
        self, bot_id: str, period: str = "30d"
    ) -> str:
        metrics = await self.calculate_performance_metrics(bot_id, period)
        bot = await self._get_bot(bot_id)

        if not bot:
            return "Bot not found"
        # Build a human-readable performance report
        report = f"""
Performance Report for {bot.name} ({period})

Total Return: {(metrics.totalReturn * 100):.2f}%
Sharpe Ratio: {metrics.sharpeRatio:.2f}
Max Drawdown: {(metrics.maxDrawdown * 100):.2f}%
Win Rate: {(metrics.winRate * 100):.2f}%
Average Win: ${metrics.averageWin:.2f}
Average Loss: ${metrics.averageLoss:.2f}
Profit Factor: {metrics.profitFactor:.2f}
Total Trades: {metrics.totalTrades}
""".strip()

        return report

    # Database methods - use real database queries
    async def _get_trades(
        self, bot_id: str, user_id: int = None, db_session=None
    ) -> List[Trade]:
        """Get trades from database"""
        try:
            from sqlalchemy import select
            from sqlalchemy.ext.asyncio import AsyncSession
            from ..models.trade import Trade as TradeModel

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._get_trades(bot_id, user_id, session)

            query = select(TradeModel).where(TradeModel.bot_id == bot_id)
            if user_id:
                query = query.where(TradeModel.user_id == user_id)

            result = await db_session.execute(query)
            db_trades = list(result.scalars().all())

            # Convert to Trade dataclass
            trades = []
            for db_trade in db_trades:
                timestamp_ms = (
                    int(db_trade.executed_at.timestamp() * 1000)
                    if db_trade.executed_at
                    else int(db_trade.timestamp.timestamp() * 1000)
                )
                trades.append(
                    Trade(
                        timestamp=timestamp_ms,
                        side=db_trade.side,
                        total=db_trade.cost,
                        totalWithFee=db_trade.cost + db_trade.fee,
                        fee=db_trade.fee,
                        pair=db_trade.pair or db_trade.symbol,
                    )
                )

            return trades
        except Exception as e:
            logger.error(f"Error getting trades for bot {bot_id}: {e}", exc_info=True)
            return []

    async def _get_bot(self, bot_id: str, db_session=None) -> Optional[BotConfig]:
        """Get bot from database"""
        try:
            from sqlalchemy import select
            from ..models.bot import Bot

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._get_bot(bot_id, session)

            query = select(Bot).where(Bot.id == bot_id)
            result = await db_session.execute(query)
            bot = result.scalar_one_or_none()

            if bot:
                return BotConfig(id=bot.id, name=bot.name)
            return None
        except Exception as e:
            logger.error(f"Error getting bot {bot_id}: {e}", exc_info=True)
            return None

    async def _save_performance_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics (optional - can be stored in bot.performance_data)"""
        # Could store in bot.performance_data JSON field
        pass

    async def _analyze_summary(self, user_id: int, db_session=None) -> Dict[str, Any]:
        """Analyze summary data"""
        # Use dashboard analysis for summary
        dashboard = await self._analyze_dashboard(user_id, db_session)
        return dashboard.get("summary", {})

    async def _analyze_performance(
        self, user_id: int, bot_id: str, period: str, db_session=None
    ) -> Dict[str, Any]:
        """Analyze performance for a specific bot"""
        metrics = await self.calculate_performance_metrics(bot_id, period, db_session)
        return {
            "bot_id": bot_id,
            "period": period,
            "metrics": metrics.dict() if hasattr(metrics, "dict") else metrics,
        }

    async def _analyze_pnl_chart(
        self, user_id: int, bot_id: Optional[str], period: str, db_session=None
    ) -> Dict[str, Any]:
        """Analyze PnL chart data"""
        try:
            from sqlalchemy import select, func
            from datetime import datetime, timedelta
            from ..models.trade import Trade

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._analyze_pnl_chart(
                        user_id, bot_id, period, session
                    )

            # Calculate date range
            end_date = datetime.now()
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

            # Query trades
            query = select(Trade).where(
                Trade.user_id == user_id, Trade.executed_at >= start_date
            )
            if bot_id:
                query = query.where(Trade.bot_id == bot_id)

            result = await db_session.execute(query)
            trades = list(result.scalars().all())

            # Group by date and calculate cumulative PnL
            chart_data = []
            cumulative_pnl = 0.0
            daily_pnl = {}

            for trade in sorted(trades, key=lambda t: t.executed_at):
                date_key = (
                    trade.executed_at.date()
                    if trade.executed_at
                    else trade.timestamp.date()
                )
                pnl = trade.pnl or 0.0
                daily_pnl[date_key] = daily_pnl.get(date_key, 0.0) + pnl

            for date, pnl in sorted(daily_pnl.items()):
                cumulative_pnl += pnl
                chart_data.append(
                    {
                        "date": date.isoformat(),
                        "pnl": pnl,
                        "cumulative_pnl": cumulative_pnl,
                    }
                )

            return {
                "chart_data": chart_data,
                "period": period,
                "total_pnl": cumulative_pnl,
            }
        except Exception as e:
            logger.error(f"Error analyzing PnL chart: {e}", exc_info=True)
            return {"chart_data": [], "period": period, "total_pnl": 0.0}


# Create singleton instance
analytics_engine = AnalyticsEngine()
