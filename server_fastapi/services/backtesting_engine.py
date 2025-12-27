from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
import asyncio
from datetime import datetime

from .ml.ensemble_engine import (
    EnsembleEngine,
    ensemble_engine,
    MarketData,
    EnsemblePrediction,
)
from .risk_management_engine import RiskManagementEngine, BotConfig, Trade

logger = logging.getLogger(__name__)


class BacktestConfig(BaseModel):
    botId: str
    initialBalance: float = 1000.0
    commission: float = 0.001


class BacktestPosition(BaseModel):
    entryPrice: float
    amount: float
    side: str  # 'long' or 'short'
    entryTime: int


class BacktestResult(BaseModel):
    id: Optional[str] = None
    botId: str
    totalReturn: float
    sharpeRatio: float
    maxDrawdown: float
    winRate: float
    totalTrades: int
    profitFactor: float
    trades: List[Dict[str, Any]]
    equityCurve: List[Dict[str, Any]]
    createdAt: Optional[datetime] = None


class BacktestingEngine:
    def __init__(self):
        self.ensemble_engine = ensemble_engine
        self.risk_manager = RiskManagementEngine()

    async def run_backtest(
        self, config: BacktestConfig, historical_data: List[MarketData]
    ) -> BacktestResult:
        if len(historical_data) < 100:
            raise ValueError("Insufficient historical data for backtesting")

        # Initialize ensemble engine with bot's model
        await self.ensemble_engine.initialize(config.botId)

        # Create a mock bot config for now - in real implementation, get from storage
        from .risk_management_engine import BotConfig as RiskBotConfig

        bot_config = RiskBotConfig(
            risk_per_trade=0.01, stop_loss=0.02, take_profit=0.05
        )

        # Create a simple config object for backtesting
        class SimpleBotConfig:
            def __init__(self, bot_id: str):
                self.id = bot_id
                self.tradingPair = "BTC/USD"
                self.maxPositionSize = 0.1
                self.riskPerTrade = bot_config.risk_per_trade

        simple_config = SimpleBotConfig(config.botId)

        # Run backtest
        result = await self.simulate_trading(historical_data, config, simple_config)

        # Create result with ID and timestamp
        backtest_result = BacktestResult(
            botId=config.botId,
            totalReturn=result["totalReturn"],
            sharpeRatio=result["sharpeRatio"],
            maxDrawdown=result["maxDrawdown"],
            winRate=result["winRate"],
            totalTrades=result["totalTrades"],
            profitFactor=result["profitFactor"],
            trades=result["trades"],
            equityCurve=result["equityCurve"],
        )

        return backtest_result

    async def simulate_trading(
        self,
        market_data: List[MarketData],
        config: BacktestConfig,
        bot_config: Any,  # SimpleBotConfig
    ) -> Dict[str, Any]:
        balance = config.initialBalance
        available_balance = balance
        positions: List[BacktestPosition] = []
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        # Sort market data by timestamp
        market_data.sort(key=lambda x: x.timestamp)

        for i in range(50, len(market_data)):  # Start after enough data for indicators
            current_data = market_data[i]
            current_price = current_data.close

            # Get trading decision from ensemble engine
            decision: EnsemblePrediction = await self.ensemble_engine.predict(
                market_data[: i + 1]
            )

            # Execute trades based on decision and risk management
            await self.execute_trade(
                decision.action,
                current_data,
                bot_config,
                balance,
                available_balance,
                positions,
                trades,
                config.commission,
            )

            # Update balances
            total_position_value = 0.0
            for pos in positions:
                if pos.side == "long":
                    total_position_value += pos.amount * current_price
                else:
                    # Short position value
                    total_position_value += pos.amount * (
                        2 * pos.entryPrice - current_price
                    )

            current_balance = available_balance + total_position_value
            balance = current_balance

            equity_curve.append(
                {
                    "timestamp": current_data.timestamp,
                    "balance": current_balance,
                }
            )

            # Update ensemble engine with reward (simplified)
            if i > 0:
                prev_data = market_data[i - 1]
                reward = self.ensemble_engine.calculate_reward(
                    decision.action,
                    prev_data.close,
                    current_price,
                    positions[0].side if positions else None,
                )

        # Calculate performance metrics
        metrics = self.calculate_performance_metrics(
            trades, equity_curve, config.initialBalance
        )

        return metrics

    async def execute_trade(
        self,
        action: str,
        market_data: MarketData,
        bot_config: Any,  # SimpleBotConfig
        balance: float,
        available_balance: float,
        positions: List[BacktestPosition],
        trades: List[Dict[str, Any]],
        commission: float,
    ) -> None:
        current_price = market_data.close
        timestamp = market_data.timestamp

        if action == "buy" and not positions:
            # Enter long position
            position_size = min(
                bot_config.maxPositionSize, available_balance * bot_config.riskPerTrade
            )

            if position_size > 10:  # Minimum trade size
                amount = position_size / current_price
                fee = position_size * commission

                positions.append(
                    BacktestPosition(
                        entryPrice=current_price,
                        amount=amount,
                        side="long",
                        entryTime=timestamp,
                    )
                )

                available_balance -= position_size + fee

                trades.append(
                    {
                        "id": f"trade_{len(trades) + 1}",
                        "botId": bot_config.id,
                        "pair": bot_config.tradingPair,
                        "side": "buy",
                        "type": "market",
                        "amount": amount,
                        "price": current_price,
                        "fee": fee,
                        "total": position_size,
                        "totalWithFee": position_size + fee,
                        "status": "completed",
                        "mode": "paper",
                        "timestamp": timestamp,
                    }
                )
        elif action == "sell" and positions:
            # Exit position
            position = positions.pop(0)

            exit_value: float
            if position.side == "long":
                exit_value = position.amount * current_price
            else:
                exit_value = position.amount * (2 * position.entryPrice - current_price)

            fee = exit_value * commission
            available_balance += exit_value - fee

            trades.append(
                {
                    "id": f"trade_{len(trades) + 1}",
                    "botId": bot_config.id,
                    "pair": bot_config.tradingPair,
                    "side": "sell",
                    "type": "market",
                    "amount": position.amount,
                    "price": current_price,
                    "fee": fee,
                    "total": exit_value,
                    "totalWithFee": exit_value - fee,
                    "status": "completed",
                    "mode": "paper",
                    "timestamp": timestamp,
                }
            )

    def calculate_performance_metrics(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]],
        initial_balance: float,
    ) -> Dict[str, Any]:
        if not trades:
            return {
                "totalReturn": 0.0,
                "sharpeRatio": 0.0,
                "maxDrawdown": 0.0,
                "winRate": 0.0,
                "profitFactor": 0.0,
                "totalTrades": 0,
                "trades": trades,
                "equityCurve": equity_curve,
            }

        # Calculate returns
        if equity_curve:
            final_balance = equity_curve[-1]["balance"]
            total_return = (final_balance - initial_balance) / initial_balance
        else:
            total_return = 0.0

        # Calculate daily returns for Sharpe ratio
        daily_returns: List[float] = []
        for i in range(1, len(equity_curve)):
            daily_return = (
                equity_curve[i]["balance"] - equity_curve[i - 1]["balance"]
            ) / equity_curve[i - 1]["balance"]
            daily_returns.append(daily_return)

        if daily_returns:
            avg_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(
                daily_returns
            )
            std_dev = variance**0.5
            sharpe_ratio = (
                avg_return / std_dev * (365**0.5) if std_dev > 0 else 0.0
            )  # Annualized
        else:
            sharpe_ratio = 0.0

        # Calculate max drawdown
        peak = initial_balance
        max_drawdown = 0.0

        for point in equity_curve:
            balance = point["balance"]
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # Calculate win rate and profit factor
        winning_trades = [t for t in trades if t.get("total", 0) > 0]
        losing_trades = [t for t in trades if t.get("total", 0) < 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0.0

        total_profit = sum(t.get("total", 0) for t in winning_trades)
        total_loss = abs(sum(t.get("total", 0) for t in losing_trades))
        profit_factor = (
            total_profit / total_loss
            if total_loss > 0
            else float("inf") if total_profit > 0 else 0.0
        )

        return {
            "totalReturn": total_return,
            "sharpeRatio": sharpe_ratio,
            "maxDrawdown": max_drawdown,
            "winRate": win_rate,
            "profitFactor": profit_factor,
            "totalTrades": len(trades),
            "trades": trades,
            "equityCurve": equity_curve,
        }

    def dispose(self) -> None:
        self.ensemble_engine.dispose()
