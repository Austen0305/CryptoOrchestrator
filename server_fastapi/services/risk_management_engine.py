import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BotConfig(BaseModel):
    risk_per_trade: float
    stop_loss: float
    take_profit: float

class Trade(BaseModel):
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: int
    total: float
    total_with_fee: float
    fee: float
    pnl: Optional[float] = None

class Portfolio(BaseModel):
    total_balance: float
    available_balance: float
    positions: Dict[str, Dict[str, Any]]
    successful_trades: Optional[int] = 0
    failed_trades: Optional[int] = 0

class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class RiskMetrics(BaseModel):
    current_drawdown: float
    max_drawdown: float
    daily_loss: float
    position_size: float
    total_exposure: float
    risk_per_trade: float

class RiskLimits(BaseModel):
    max_drawdown: float = 0.10  # 10% max drawdown
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_position_size: float = 0.10  # 10% of portfolio per position
    max_total_exposure: float = 0.50  # 50% max total exposure
    stop_loss_multiplier: float = 1.5  # Stop loss at 1.5x risk per trade
    take_profit_multiplier: float = 3.0  # Take profit at 3x risk per trade
    min_position_size: float = 0.0001  # Minimum position size for micro trading (0.01% of portfolio)
    micro_mode_enabled: bool = True  # Enable micro trading mode by default
    persistent_mode: bool = True  # Enable persistent mode - bots don't stop automatically

class RiskManagementEngine:
    def __init__(self):
        self.default_limits = RiskLimits()
        self.historical_volatility: float = 0.0
        self.last_volatility_update: int = 0
        self.volatility_update_interval = 1000 * 60 * 15  # 15 minutes in milliseconds

    async def update_historical_volatility(self, exchange_service: Any) -> None:
        """Update historical volatility from exchange data"""
        now = int(datetime.utcnow().timestamp() * 1000)
        if now - self.last_volatility_update < self.volatility_update_interval:
            return

        try:
            # Mock historical data fetch - in real implementation, call exchange service
            historical_data = []  # Would be fetched from exchange_service.get_historical_data()

            if historical_data:
                self.historical_volatility = self.calculate_volatility_index(historical_data)
                self.last_volatility_update = now
        except Exception as error:
            logger.error(f"Failed to update historical volatility: {error}")

    def calculate_volatility_index(self, historical_data: List[MarketData]) -> float:
        """Calculate volatility index from historical data"""
        if len(historical_data) < 2:
            return 0.02  # Default volatility

        import numpy as np
        prices = [data.close for data in historical_data]
        returns = []

        for i in range(1, len(prices)):
            ret = np.log(prices[i] / prices[i - 1])
            returns.append(ret)

        return np.std(returns) if returns else 0.02

    async def calculate_risk_metrics(self, bot_id: str, portfolio: Portfolio, storage: Any) -> RiskMetrics:
        """Calculate comprehensive risk metrics for a bot"""
        try:
            # Mock trades fetch - in real implementation, call storage.get_trades()
            trades = []  # Would be fetched from storage

            # Calculate current drawdown
            equity_curve = self.calculate_equity_curve(trades, portfolio.total_balance)
            current_drawdown = self.calculate_current_drawdown(equity_curve)

            # Calculate max drawdown
            max_drawdown = self.calculate_max_drawdown(equity_curve)

            # Calculate daily P&L
            daily_pnl = self.calculate_daily_pnl(trades)
            daily_loss = abs(min(daily_pnl)) if daily_pnl else 0.0

            # Calculate position metrics
            position_size = self.calculate_current_position_size(portfolio)
            total_exposure = self.calculate_total_exposure(portfolio)

            return RiskMetrics(
                current_drawdown=current_drawdown,
                max_drawdown=max_drawdown,
                daily_loss=daily_loss,
                position_size=position_size,
                total_exposure=total_exposure,
                risk_per_trade=0.02  # Mock value - would come from bot config
            )
        except Exception as error:
            logger.error(f"Error calculating risk metrics: {error}")
            raise

    def should_stop_trading(self, portfolio: Portfolio) -> Tuple[bool, Optional[str]]:
        """Determine if trading should stop based on risk limits"""
        # If persistent mode is enabled, never stop trading automatically
        if self.default_limits.persistent_mode:
            return False, None

        # Mock risk metrics calculation
        try:
            # Would call self.calculate_risk_metrics() in real implementation
            mock_metrics = RiskMetrics(
                current_drawdown=0.05,
                max_drawdown=0.08,
                daily_loss=0.02,
                position_size=0.15,
                total_exposure=0.30,
                risk_per_trade=0.02
            )

            limits = self.default_limits

            if mock_metrics.current_drawdown >= limits.max_drawdown:
                return True, f"Max drawdown exceeded: {mock_metrics.current_drawdown:.2%} >= {limits.max_drawdown:.2%}"

            if mock_metrics.daily_loss >= limits.max_daily_loss:
                return True, f"Daily loss limit exceeded: {mock_metrics.daily_loss:.2%} >= {limits.max_daily_loss:.2%}"

            if mock_metrics.total_exposure >= limits.max_total_exposure:
                return True, f"Total exposure limit exceeded: {mock_metrics.total_exposure:.2%} >= {limits.max_total_exposure:.2%}"

            return False, None
        except Exception as error:
            logger.error(f"Error checking if trading should stop: {error}")
            return False, None

    def calculate_position_size_for_trade(
        self,
        bot_config: BotConfig,
        portfolio: Portfolio,
        current_price: float
    ) -> float:
        """Calculate position size for a new trade using Kelly Criterion"""
        available_balance = portfolio.available_balance

        # Calculate Kelly Criterion
        wins = portfolio.successful_trades or 0
        losses = portfolio.failed_trades or 0
        total_trades = wins + losses

        kelly_fraction = 0.0
        if total_trades > 0:
            win_rate = wins / total_trades
            win_multiplier = bot_config.take_profit / bot_config.stop_loss
            loss_multiplier = 1.0

            kelly_fraction = (win_rate * win_multiplier - (1 - win_rate) * loss_multiplier) / win_multiplier
            # Use half-Kelly for more conservative sizing
            kelly_fraction = max(0.0, kelly_fraction * 0.5)
        else:
            # Start conservative with 1% if no trade history
            kelly_fraction = 0.01

        # Calculate position size based on risk and Kelly Criterion
        risk_amount = available_balance * bot_config.risk_per_trade * kelly_fraction
        stop_loss_amount = current_price * bot_config.stop_loss

        if stop_loss_amount == 0:
            return 0.0

        position_size = risk_amount / stop_loss_amount
        max_position_size = available_balance * self.default_limits.max_position_size / current_price

        # Apply micro trading limits if enabled
        final_position_size = min(position_size, max_position_size)

        if self.default_limits.micro_mode_enabled:
            # Ensure position size doesn't go below minimum for micro trading
            min_position_value = available_balance * self.default_limits.min_position_size
            min_position_size = min_position_value / current_price

            # For small balances, allow micro positions but cap at a reasonable maximum
            if available_balance < 1000:  # Less than $1000 balance
                final_position_size = max(final_position_size, min_position_size)
                # Cap at 1% of available balance for safety
                final_position_size = min(final_position_size, available_balance * 0.01 / current_price)

        return final_position_size

    def calculate_dynamic_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        bot_config: BotConfig
    ) -> float:
        """Calculate dynamic trailing stop loss"""
        risk_amount = entry_price * bot_config.risk_per_trade
        stop_loss_distance = risk_amount / (entry_price * self.default_limits.stop_loss_multiplier)

        # Trailing stop loss
        trailing_stop = current_price * (1 - stop_loss_distance)

        # Ensure stop loss is below entry for long positions
        return min(trailing_stop, entry_price * (1 - bot_config.stop_loss))

    def calculate_take_profit(self, entry_price: float, bot_config: BotConfig) -> float:
        """Calculate take profit level"""
        return entry_price * (1 + bot_config.take_profit * self.default_limits.take_profit_multiplier)

    def calculate_equity_curve(self, trades: List[Trade], initial_balance: float) -> List[float]:
        """Calculate equity curve from trade history"""
        balance = initial_balance
        equity = [balance]

        # Group trades by day (simplified)
        daily_trades: Dict[int, List[Trade]] = {}

        for trade in trades:
            day = trade.timestamp // (24 * 60 * 60 * 1000)  # Convert to days
            if day not in daily_trades:
                daily_trades[day] = []
            daily_trades[day].append(trade)

        # Calculate daily equity
        for day in sorted(daily_trades.keys()):
            day_trades = daily_trades[day]
            for trade in day_trades:
                if trade.side == 'buy':
                    balance -= trade.total_with_fee
                else:
                    balance += trade.total - trade.fee
            equity.append(balance)

        return equity

    def calculate_current_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate current drawdown from equity curve"""
        if not equity_curve:
            return 0.0

        peak = max(equity_curve)
        current = equity_curve[-1]

        return (peak - current) / peak if peak > 0 else 0.0

    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if len(equity_curve) < 2:
            return 0.0

        max_drawdown = 0.0
        peak = equity_curve[0]

        for value in equity_curve[1:]:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def calculate_daily_pnl(self, trades: List[Trade]) -> List[float]:
        """Calculate daily profit and loss"""
        daily_pnl: Dict[int, float] = {}

        for trade in trades:
            day = trade.timestamp // (24 * 60 * 60 * 1000)
            pnl = -trade.total_with_fee if trade.side == 'buy' else trade.total - trade.fee

            daily_pnl[day] = daily_pnl.get(day, 0.0) + pnl

        return list(daily_pnl.values())

    def calculate_current_position_size(self, portfolio: Portfolio) -> float:
        """Calculate current position size as percentage of portfolio"""
        total_value = sum(pos.get('total_value', 0.0) for pos in portfolio.positions.values())
        return total_value / portfolio.total_balance if portfolio.total_balance > 0 else 0.0

    def calculate_total_exposure(self, portfolio: Portfolio) -> float:
        """Calculate total exposure (same as position size for simplicity)"""
        return self.calculate_current_position_size(portfolio)

    def update_risk_limits(self, limits: Dict[str, Any]) -> None:
        """Update risk limits configuration"""
        for key, value in limits.items():
            if hasattr(self.default_limits, key):
                setattr(self.default_limits, key, value)

    def get_risk_limits(self) -> RiskLimits:
        """Get current risk limits"""
        return self.default_limits.copy()

# Global instance
risk_management_engine = RiskManagementEngine()