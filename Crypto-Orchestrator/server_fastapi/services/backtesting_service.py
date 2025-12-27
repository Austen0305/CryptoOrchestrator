from typing import List
import numpy as np
import pandas as pd
from datetime import datetime
from pydantic import BaseModel
from .ml_service import MLModel, MarketData


class BacktestConfig(BaseModel):
    bot_id: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    commission: float = 0.001


class BacktestResult(BaseModel):
    final_balance: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    trades: List[dict]
    equity_curve: List[float]


class BacktestingEngine:
    def __init__(self):
        self.ml_model = MLModel()

    async def run_backtest(
        self, config: BacktestConfig, historical_data: List[MarketData]
    ) -> BacktestResult:
        if len(historical_data) < 100:
            raise ValueError("Insufficient historical data for backtesting")

        # Initialize variables
        balance = config.initial_balance
        equity_curve = []
        trades = []
        position = None
        entry_price = None
        max_balance = balance
        max_drawdown = 0
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0

        # Process each data point
        for i in range(len(historical_data)):
            if i < 20:  # Skip initial period for indicators
                continue

            # Get prediction
            prediction = self.ml_model.predict(historical_data[: i + 1])
            action = prediction["prediction"]

            # Execute trade
            if action == "buy" and position is None:
                position = "long"
                entry_price = historical_data[i].close
                trade_size = balance * 0.1  # 10% of balance
                fee = trade_size * config.commission
                balance -= fee
                trades.append(
                    {
                        "type": "buy",
                        "price": entry_price,
                        "size": trade_size,
                        "timestamp": historical_data[i].timestamp,
                    }
                )
            elif action == "sell" and position == "long":
                exit_price = historical_data[i].close
                trade_size = trades[-1]["size"]
                pnl = (exit_price - entry_price) * trade_size
                fee = trade_size * config.commission
                balance += pnl - fee
                position = None
                entry_price = None
                trades[-1]["exit_price"] = exit_price
                trades[-1]["pnl"] = pnl
                if pnl > 0:
                    wins += 1
                    total_profit += pnl
                else:
                    losses += 1
                    total_loss += abs(pnl)

            # Update metrics
            equity_curve.append(balance)
            if balance > max_balance:
                max_balance = balance
            drawdown = (max_balance - balance) / max_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Calculate final metrics
        total_return = (balance - config.initial_balance) / config.initial_balance
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")
        sharpe_ratio = self.calculate_sharpe_ratio(equity_curve)

        return BacktestResult(
            final_balance=balance,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(trades),
            profit_factor=profit_factor,
            trades=trades,
            equity_curve=equity_curve,
        )

    def calculate_sharpe_ratio(self, equity_curve: List[float]) -> float:
        returns = np.diff(equity_curve) / equity_curve[:-1]
        return np.mean(returns) / np.std(returns) * np.sqrt(252)
