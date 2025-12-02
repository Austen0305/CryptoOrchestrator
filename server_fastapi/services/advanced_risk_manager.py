import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class RiskProfile(BaseModel):
    max_position_size: float
    stop_loss_distance: float
    take_profit_distance: float
    entry_confidence: float

class RiskMetrics(BaseModel):
    current_risk: float
    historical_volatility: float
    expected_drawdown: float
    optimal_leverage: float
    kelly_fraction: float

class Trade(BaseModel):
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: int
    pnl: Optional[float] = None

class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class AdvancedRiskManager:
    _instance: Optional['AdvancedRiskManager'] = None

    def __init__(self):
        if AdvancedRiskManager._instance is not None:
            raise Exception("AdvancedRiskManager is a singleton class")

        self.historical_data: List[MarketData] = []
        self.recent_trades: List[Trade] = []
        self.risk_metrics = RiskMetrics(
            current_risk=0.0,
            historical_volatility=0.0,
            expected_drawdown=0.0,
            optimal_leverage=1.0,
            kelly_fraction=0.5
        )

        self.max_trades_history = 1000
        self.risk_update_interval = 5 * 60  # 5 minutes in seconds
        self.update_task: Optional[asyncio.Task] = None

        AdvancedRiskManager._instance = self

    @classmethod
    def get_instance(cls) -> 'AdvancedRiskManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start_risk_updates(self):
        """Start periodic risk assessment updates"""
        if self.update_task is None:
            self.update_task = asyncio.create_task(self._periodic_risk_update())

    async def stop_risk_updates(self):
        """Stop periodic risk assessment updates"""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
            self.update_task = None

    async def _periodic_risk_update(self):
        """Periodic risk assessment update"""
        while True:
            try:
                await self.update_risk_assessment()
                await asyncio.sleep(self.risk_update_interval)
            except asyncio.CancelledError:
                break
            except Exception as error:
                logger.error(f"Error in periodic risk update: {error}")
                await asyncio.sleep(self.risk_update_interval)

    async def calculate_optimal_risk_profile(
        self,
        current_price: float,
        volatility: float,
        market_conditions: Dict[str, Any]
    ) -> RiskProfile:
        """Calculate optimal risk profile based on current market conditions"""
        metrics = self.risk_metrics
        kelly_fraction = self.calculate_kelly_fraction()

        # Base position size on Kelly Criterion and current market conditions
        max_position_size = kelly_fraction * metrics.optimal_leverage

        # Adjust for market volatility
        max_position_size *= (1 - min(volatility, 0.5))

        # Calculate dynamic stop loss based on volatility and market conditions
        stop_loss_distance = self.calculate_dynamic_stop_loss(volatility, market_conditions)

        # Calculate take profit based on risk:reward ratio
        take_profit_distance = stop_loss_distance * self.calculate_risk_reward_ratio(market_conditions)

        # Calculate entry confidence score
        entry_confidence = self.calculate_entry_confidence(market_conditions)

        return RiskProfile(
            max_position_size=min(max_position_size, 0.1),  # Cap at 10%
            stop_loss_distance=stop_loss_distance,
            take_profit_distance=take_profit_distance,
            entry_confidence=entry_confidence
        )

    def calculate_kelly_fraction(self) -> float:
        """Calculate Kelly fraction based on trading performance"""
        if len(self.recent_trades) < 10:
            return 0.1  # Default conservative value

        wins = [t for t in self.recent_trades if t.pnl and t.pnl > 0]
        losses = [t for t in self.recent_trades if t.pnl and t.pnl <= 0]

        if not losses:
            return 0.1  # Avoid division by zero

        win_rate = len(wins) / len(self.recent_trades)
        avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t.pnl for t in losses) / len(losses)) if losses else 0

        if avg_loss == 0:
            return 0.1  # Avoid division by zero

        payoff_ratio = avg_win / avg_loss

        # Standard Kelly formula: f* = p - (1 - p)/b
        kelly_fraction = win_rate - (1 - win_rate) / payoff_ratio

        # Limit to reasonable bounds
        return max(0.0, min(kelly_fraction, 0.5))

    def calculate_dynamic_stop_loss(self, volatility: float, market_conditions: Dict[str, Any]) -> float:
        """Calculate dynamic stop loss based on volatility and market conditions"""
        # Base stop loss on volatility (simplified ATR)
        stop_loss = volatility * 2

        # Adjust for market conditions
        regime = market_conditions.get('regime', 'normal')
        if regime == 'volatile':
            stop_loss *= 1.5

        # Ensure minimum stop loss
        return max(stop_loss, 0.01)

    def calculate_risk_reward_ratio(self, market_conditions: Dict[str, Any]) -> float:
        """Calculate risk-reward ratio based on market regime"""
        regime = market_conditions.get('regime', 'normal')

        # Base RR ratio on market regime
        if regime == 'trending':
            return 3.0  # Higher reward target in trending markets
        elif regime == 'ranging':
            return 2.0  # Lower targets in ranging markets
        elif regime == 'volatile':
            return 2.5  # Balanced in volatile markets
        else:
            return 2.0

    def calculate_entry_confidence(self, market_conditions: Dict[str, Any]) -> float:
        """Calculate entry confidence score"""
        confidence = 0.5  # Base confidence

        # Adjust for market conditions
        trend_strength = market_conditions.get('trend', {}).get('strength', 0.5)
        if trend_strength > 0.7:
            confidence += 0.2

        volume_level = market_conditions.get('volume', {}).get('level', 'medium')
        if volume_level == 'high':
            confidence += 0.1

        liquidity_sufficient = market_conditions.get('liquidity', {}).get('sufficient', True)
        if not liquidity_sufficient:
            confidence -= 0.3

        # Ensure bounds
        return max(0.0, min(confidence, 1.0))

    async def update_risk_assessment(self):
        """Update comprehensive risk assessment"""
        try:
            # Mock market conditions - in real implementation, get from market analyzer
            market_conditions = {
                'regime': 'normal',
                'volatility': 0.02,
                'trend': {'strength': 0.6},
                'volume': {'level': 'medium'},
                'liquidity': {'sufficient': True}
            }

            # Update risk metrics
            self.risk_metrics = RiskMetrics(
                current_risk=self.calculate_current_risk(),
                historical_volatility=market_conditions['volatility'],
                expected_drawdown=self.calculate_expected_drawdown(),
                optimal_leverage=self.calculate_optimal_leverage(),
                kelly_fraction=self.calculate_kelly_fraction()
            )

            # Emit risk metrics updated event (in FastAPI, this would be through dependency injection or signals)
            logger.info('Risk metrics updated', extra={
                'current_risk': self.risk_metrics.current_risk,
                'historical_volatility': self.risk_metrics.historical_volatility,
                'expected_drawdown': self.risk_metrics.expected_drawdown,
                'optimal_leverage': self.risk_metrics.optimal_leverage,
                'kelly_fraction': self.risk_metrics.kelly_fraction
            })
        except Exception as error:
            logger.error(f'Error updating risk assessment: {error}')

    def calculate_current_risk(self) -> float:
        """Calculate current risk exposure"""
        if not self.recent_trades:
            return 0.5  # Default medium risk

        # Calculate win rate and profit factor
        winning_trades = [t for t in self.recent_trades if t.pnl and t.pnl > 0]
        win_rate = len(winning_trades) / len(self.recent_trades)
        total_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_loss = sum(abs(t.pnl) for t in self.recent_trades if t.pnl and t.pnl <= 0)

        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')

        # Count positions per symbol
        position_counts: Dict[str, int] = {}
        for trade in self.recent_trades:
            position_counts[trade.symbol] = position_counts.get(trade.symbol, 0) + 1

        concentration_risk = sum((count / len(self.recent_trades)) ** 2 for count in position_counts.values())

        # Combine factors into risk score (0-1)
        risk_score = (
            0.4 * (1 - win_rate) +
            0.3 * (1 - min(1, profit_factor / 5)) +
            0.3 * concentration_risk
        )

        return min(1.0, max(0.0, risk_score))

    def calculate_expected_drawdown(self) -> float:
        """Calculate expected maximum drawdown"""
        if len(self.historical_data) < 30:
            return 0.2  # Default

        # Calculate rolling volatility from price data
        returns = []
        for i in range(1, len(self.historical_data)):
            ret = np.log(self.historical_data[i].close / self.historical_data[i - 1].close)
            returns.append(ret)

        volatility = np.std(returns) if returns else 0.02
        expected_drawdown = volatility * 2.5  # 2.5 sigma event

        return min(0.5, max(0.05, expected_drawdown))

    def calculate_optimal_leverage(self) -> float:
        """Calculate optimal leverage based on Kelly criterion"""
        if self.risk_metrics.kelly_fraction <= 0:
            return 1.0

        max_leverage = 10.0
        safety_margin = 0.7  # Conservative factor
        volatility_factor = min(1.0, 0.2 / self.risk_metrics.historical_volatility) if self.risk_metrics.historical_volatility > 0 else 1.0

        return min(max_leverage, max(1.0, self.risk_metrics.kelly_fraction * safety_margin * volatility_factor))

    def update_risk_metrics(self, market_conditions: Dict[str, Any]):
        """Update risk metrics based on market conditions"""
        # Update risk metrics based on market conditions
        volatility = market_conditions.get('volatility', 0.02)
        regime = market_conditions.get('regime', 'normal')

        if volatility > 0.3 or regime == 'volatile':
            # In FastAPI, this would emit an event or notification
            logger.warning('High risk alert triggered', extra={
                'volatility': volatility,
                'regime': regime
            })

    def adjust_risk_parameters(self, performance_metrics: Dict[str, Any]):
        """Adjust risk parameters based on performance"""
        # Adjust risk parameters based on performance
        consecutive_losses = performance_metrics.get('consecutive_losses', 0)

        if consecutive_losses > 3:
            self.reduce_risk_exposure()

    def reduce_risk_exposure(self):
        """Reduce risk exposure after consecutive losses"""
        self.risk_metrics.optimal_leverage *= 0.8
        logger.info('Risk exposure reduced due to consecutive losses', extra={
            'new_leverage': self.risk_metrics.optimal_leverage
        })

    def add_trade(self, trade: Trade):
        """Add a trade to the recent trades history"""
        self.recent_trades.append(trade)
        if len(self.recent_trades) > self.max_trades_history:
            self.recent_trades.pop(0)

    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        return self.risk_metrics.copy()

    async def dispose(self):
        """Clean up resources"""
        await self.stop_risk_updates()

# Global instance
advanced_risk_manager = AdvancedRiskManager.get_instance()
