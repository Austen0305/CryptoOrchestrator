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

    async def analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data based on type and parameters"""
        analysis_type = params.get('type')
        user_id = params.get('user_id')

        if analysis_type == 'summary':
            return self._analyze_summary(user_id)
        elif analysis_type == 'performance':
            bot_id = params.get('bot_id')
            period = params.get('period', '30d')
            return self._analyze_performance(user_id, bot_id, period)
        elif analysis_type == 'pnl_chart':
            bot_id = params.get('bot_id')
            period = params.get('period', '30d')
            return self._analyze_pnl_chart(user_id, bot_id, period)
        elif analysis_type == 'dashboard':
            return self._analyze_dashboard(user_id)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

    def _analyze_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Analyze dashboard data for summary view"""
        # Mock dashboard data - would integrate with actual data sources
        dashboard_data = {
            "summary": {
                "total_bots": 5,
                "active_bots": 3,
                "total_trades": 245,
                "total_pnl": 3250.75,
                "win_rate": 0.612,
                "best_performing_bot": "bot-1",
                "worst_performing_bot": "bot-3"
            },
            "details": {
                "metrics": [
                    {
                        "bot_id": "bot-1",
                        "bot_name": "Scalping Bot",
                        "total_trades": 120,
                        "winning_trades": 85,
                        "losing_trades": 35,
                        "win_rate": 0.708,
                        "total_pnl": 1850.25,
                        "max_drawdown": 245.50,
                        "sharpe_ratio": 1.85,
                        "current_balance": 101850.25
                    },
                    {
                        "bot_id": "bot-2",
                        "bot_name": "Swing Bot",
                        "total_trades": 89,
                        "winning_trades": 52,
                        "losing_trades": 37,
                        "win_rate": 0.584,
                        "total_pnl": 1250.50,
                        "max_drawdown": 180.25,
                        "sharpe_ratio": 1.42,
                        "current_balance": 101250.50
                    }
                ],
                "chart_data": []
            }
        }

        return dashboard_data

    async def calculate_performance_metrics(self, bot_id: str, period: str = 'all') -> PerformanceMetrics:
        # Mock data for demonstration - in real implementation would fetch from storage
        trades = await self._get_trades(bot_id)
        bot = await self._get_bot(bot_id)

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

        if period == '1d':
            start_time = now - 24 * 60 * 60 * 1000
        elif period == '7d':
            start_time = now - 7 * 24 * 60 * 60 * 1000
        elif period == '30d':
            start_time = now - 30 * 24 * 60 * 60 * 1000
        elif period == '90d':
            start_time = now - 90 * 24 * 60 * 60 * 1000
        elif period == '1y':
            start_time = now - 365 * 24 * 60 * 60 * 1000
        else:
            return trades  # 'all' period

        return [trade for trade in trades if trade.timestamp >= start_time]

    def _calculate_total_return(self, trades: List[Trade]) -> float:
        initial_investment = 100000  # Assume starting balance
        current_balance = initial_investment

        for trade in trades:
            if trade.side == 'buy':
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
        variance = sum((ret - avg_return) ** 2 for ret in daily_returns) / len(daily_returns)
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

        winning_trades = [trade for trade in trades if trade.side == 'sell' and trade.total > 0]

        return len(winning_trades) / len(trades)

    def _calculate_average_win(self, trades: List[Trade]) -> float:
        winning_trades = [trade for trade in trades if trade.side == 'sell' and trade.total > 0]

        if not winning_trades:
            return 0

        total_wins = sum(trade.total for trade in winning_trades)
        return total_wins / len(winning_trades)

    def _calculate_average_loss(self, trades: List[Trade]) -> float:
        losing_trades = [trade for trade in trades if trade.side == 'sell' and trade.total < 0]

        if not losing_trades:
            return 0

        total_losses = sum(abs(trade.total) for trade in losing_trades)
        return total_losses / len(losing_trades)

    def _calculate_profit_factor(self, trades: List[Trade]) -> float:
        gross_profit = sum(trade.total for trade in trades if trade.side == 'sell' and trade.total > 0)

        gross_loss = abs(sum(trade.total for trade in trades if trade.side == 'sell' and trade.total < 0))

        if gross_loss > 0:
            return gross_profit / gross_loss
        elif gross_profit > 0:
            return float('inf')
        else:
            return 0

    def _calculate_daily_returns(self, trades: List[Trade]) -> List[float]:
        daily_pnl = {}
        initial_balance = 100000

        for trade in trades:
            day = trade.timestamp // (24 * 60 * 60 * 1000)
            pnl = -trade.totalWithFee if trade.side == 'buy' else trade.total - trade.fee

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
            if trade.side == 'buy':
                balance -= trade.totalWithFee
            else:
                balance += trade.total - trade.fee
            equity.append(balance)

        return equity

    async def get_performance_comparison(self, bot_ids: List[str], period: str = '30d') -> Dict[str, PerformanceMetrics]:
        comparisons = {}

        for bot_id in bot_ids:
            comparisons[bot_id] = await self.calculate_performance_metrics(bot_id, period)

        return comparisons

    async def generate_performance_report(self, bot_id: str, period: str = '30d') -> str:
        metrics = await self.calculate_performance_metrics(bot_id, period)
        bot = await self._get_bot(bot_id)

        if not bot:
            return 'Bot not found'
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

    # Mock storage methods - replace with actual storage calls
    async def _get_trades(self, bot_id: str) -> List[Trade]:
        # Mock implementation
        return []

    async def _get_bot(self, bot_id: str) -> Optional[BotConfig]:
        # Mock implementation
        return BotConfig(id=bot_id, name=f"Bot {bot_id}")

    async def _save_performance_metrics(self, metrics: PerformanceMetrics):
        # Mock implementation
        pass

# Create singleton instance
analytics_engine = AnalyticsEngine()
