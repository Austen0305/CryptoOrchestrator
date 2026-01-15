import asyncio
import contextlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PositionSizingMethod(Enum):
    """Position sizing calculation methods."""

    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_BASED = "volatility_based"
    RISK_PARITY = "risk_parity"


class VaRMethod(Enum):
    """Value at Risk calculation methods."""

    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class RiskLimits:
    """Risk limits configuration."""

    max_position_size: float = 0.20  # Max 20% of portfolio per position
    max_total_exposure: float = 1.0  # Max 100% total exposure
    max_leverage: float = 3.0  # Max 3x leverage
    max_daily_loss: float = 0.05  # Max 5% daily loss
    max_drawdown: float = 0.20  # Max 20% drawdown
    max_correlation: float = 0.70  # Max 70% correlation between positions
    min_liquidity_ratio: float = 0.10  # Min 10% cash reserve


@dataclass
class PositionRisk:
    """Risk metrics for a single position."""

    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    stop_loss: float | None
    take_profit: float | None
    unrealized_pnl: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    position_weight: float


@dataclass
class PortfolioRisk:
    """Risk metrics for entire portfolio."""

    total_value: float
    total_exposure: float
    leverage: float
    var_95: float
    var_99: float
    expected_shortfall: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    correlation_matrix: np.ndarray | None
    position_risks: list[PositionRisk]


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
    pnl: float | None = None


class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class AdvancedRiskManager:
    _instance: Optional["AdvancedRiskManager"] = None

    def __init__(self):
        if AdvancedRiskManager._instance is not None:
            raise Exception("AdvancedRiskManager is a singleton class")

        self.historical_data: list[MarketData] = []
        self.recent_trades: list[Trade] = []
        self.risk_metrics = RiskMetrics(
            current_risk=0.0,
            historical_volatility=0.0,
            expected_drawdown=0.0,
            optimal_leverage=1.0,
            kelly_fraction=0.5,
        )

        self.risk_limits = RiskLimits()
        self.position_history: list[dict] = []
        self.peak_value: float = 0.0

        self.max_trades_history = 1000
        self.risk_update_interval = 5 * 60  # 5 minutes in seconds
        self.update_task: asyncio.Task | None = None

        AdvancedRiskManager._instance = self

    @classmethod
    def get_instance(cls) -> "AdvancedRiskManager":
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
            with contextlib.suppress(asyncio.CancelledError):
                await self.update_task
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
        self, current_price: float, volatility: float, market_conditions: dict[str, Any]
    ) -> RiskProfile:
        """Calculate optimal risk profile based on current market conditions"""
        metrics = self.risk_metrics
        kelly_fraction = self.calculate_kelly_fraction()

        # Base position size on Kelly Criterion and current market conditions
        max_position_size = kelly_fraction * metrics.optimal_leverage

        # Adjust for market volatility
        max_position_size *= 1 - min(volatility, 0.5)

        # Calculate dynamic stop loss based on volatility and market conditions
        stop_loss_distance = self.calculate_dynamic_stop_loss(
            volatility, market_conditions
        )

        # Calculate take profit based on risk:reward ratio
        take_profit_distance = stop_loss_distance * self.calculate_risk_reward_ratio(
            market_conditions
        )

        # Calculate entry confidence score
        entry_confidence = self.calculate_entry_confidence(market_conditions)

        return RiskProfile(
            max_position_size=min(max_position_size, 0.1),  # Cap at 10%
            stop_loss_distance=stop_loss_distance,
            take_profit_distance=take_profit_distance,
            entry_confidence=entry_confidence,
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

    def calculate_dynamic_stop_loss(
        self, volatility: float, market_conditions: dict[str, Any]
    ) -> float:
        """Calculate dynamic stop loss based on volatility and market conditions"""
        # Base stop loss on volatility (simplified ATR)
        stop_loss = volatility * 2

        # Adjust for market conditions
        regime = market_conditions.get("regime", "normal")
        if regime == "volatile":
            stop_loss *= 1.5

        # Ensure minimum stop loss
        return max(stop_loss, 0.01)

    def calculate_risk_reward_ratio(self, market_conditions: dict[str, Any]) -> float:
        """Calculate risk-reward ratio based on market regime"""
        regime = market_conditions.get("regime", "normal")

        # Base RR ratio on market regime
        if regime == "trending":
            return 3.0  # Higher reward target in trending markets
        elif regime == "ranging":
            return 2.0  # Lower targets in ranging markets
        elif regime == "volatile":
            return 2.5  # Balanced in volatile markets
        else:
            return 2.0

    def calculate_entry_confidence(self, market_conditions: dict[str, Any]) -> float:
        """Calculate entry confidence score"""
        confidence = 0.5  # Base confidence

        # Adjust for market conditions
        trend_strength = market_conditions.get("trend", {}).get("strength", 0.5)
        if trend_strength > 0.7:
            confidence += 0.2

        volume_level = market_conditions.get("volume", {}).get("level", "medium")
        if volume_level == "high":
            confidence += 0.1

        liquidity_sufficient = market_conditions.get("liquidity", {}).get(
            "sufficient", True
        )
        if not liquidity_sufficient:
            confidence -= 0.3

        # Ensure bounds
        return max(0.0, min(confidence, 1.0))

    async def update_risk_assessment(self):
        """Update comprehensive risk assessment"""
        try:
            # Mock market conditions - in real implementation, get from market analyzer
            market_conditions = {
                "regime": "normal",
                "volatility": 0.02,
                "trend": {"strength": 0.6},
                "volume": {"level": "medium"},
                "liquidity": {"sufficient": True},
            }

            # Update risk metrics
            self.risk_metrics = RiskMetrics(
                current_risk=self.calculate_current_risk(),
                historical_volatility=market_conditions["volatility"],
                expected_drawdown=self.calculate_expected_drawdown(),
                optimal_leverage=self.calculate_optimal_leverage(),
                kelly_fraction=self.calculate_kelly_fraction(),
            )

            # Emit risk metrics updated event (in FastAPI, this would be through dependency injection or signals)
            logger.info(
                "Risk metrics updated",
                extra={
                    "current_risk": self.risk_metrics.current_risk,
                    "historical_volatility": self.risk_metrics.historical_volatility,
                    "expected_drawdown": self.risk_metrics.expected_drawdown,
                    "optimal_leverage": self.risk_metrics.optimal_leverage,
                    "kelly_fraction": self.risk_metrics.kelly_fraction,
                },
            )
        except Exception as error:
            logger.error(f"Error updating risk assessment: {error}")

    def calculate_current_risk(self) -> float:
        """Calculate current risk exposure"""
        if not self.recent_trades:
            return 0.5  # Default medium risk

        # Calculate win rate and profit factor
        winning_trades = [t for t in self.recent_trades if t.pnl and t.pnl > 0]
        win_rate = len(winning_trades) / len(self.recent_trades)
        total_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_loss = sum(abs(t.pnl) for t in self.recent_trades if t.pnl and t.pnl <= 0)

        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

        # Count positions per symbol
        position_counts: dict[str, int] = {}
        for trade in self.recent_trades:
            position_counts[trade.symbol] = position_counts.get(trade.symbol, 0) + 1

        concentration_risk = sum(
            (count / len(self.recent_trades)) ** 2 for count in position_counts.values()
        )

        # Combine factors into risk score (0-1)
        risk_score = (
            0.4 * (1 - win_rate)
            + 0.3 * (1 - min(1, profit_factor / 5))
            + 0.3 * concentration_risk
        )

        return min(1.0, max(0.0, risk_score))

    def calculate_expected_drawdown(self) -> float:
        """Calculate expected maximum drawdown"""
        if len(self.historical_data) < 30:
            return 0.2  # Default

        # Calculate rolling volatility from price data
        returns = []
        for i in range(1, len(self.historical_data)):
            ret = np.log(
                self.historical_data[i].close / self.historical_data[i - 1].close
            )
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
        volatility_factor = (
            min(1.0, 0.2 / self.risk_metrics.historical_volatility)
            if self.risk_metrics.historical_volatility > 0
            else 1.0
        )

        return min(
            max_leverage,
            max(
                1.0,
                self.risk_metrics.kelly_fraction * safety_margin * volatility_factor,
            ),
        )

    def update_risk_metrics(self, market_conditions: dict[str, Any]):
        """Update risk metrics based on market conditions"""
        # Update risk metrics based on market conditions
        volatility = market_conditions.get("volatility", 0.02)
        regime = market_conditions.get("regime", "normal")

        if volatility > 0.3 or regime == "volatile":
            # In FastAPI, this would emit an event or notification
            logger.warning(
                "High risk alert triggered",
                extra={"volatility": volatility, "regime": regime},
            )

    def adjust_risk_parameters(self, performance_metrics: dict[str, Any]):
        """Adjust risk parameters based on performance"""
        # Adjust risk parameters based on performance
        consecutive_losses = performance_metrics.get("consecutive_losses", 0)

        if consecutive_losses > 3:
            self.reduce_risk_exposure()

    def reduce_risk_exposure(self):
        """Reduce risk exposure after consecutive losses"""
        self.risk_metrics.optimal_leverage *= 0.8
        logger.info(
            "Risk exposure reduced due to consecutive losses",
            extra={"new_leverage": self.risk_metrics.optimal_leverage},
        )

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

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_risk_updates()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_risk_updates()

    # --- Professional Math Methods (Migrated from advanced_risk_management.py) ---

    def calculate_position_size_v2(
        self,
        method: PositionSizingMethod,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float,
        win_rate: float | None = None,
        avg_win: float | None = None,
        avg_loss: float | None = None,
        volatility: float | None = None,
    ) -> float:
        """Calculate optimal position size using professional methods."""
        if method == PositionSizingMethod.FIXED_FRACTIONAL:
            return self._fixed_fractional_sizing(
                account_balance, risk_per_trade, entry_price, stop_loss
            )
        elif method == PositionSizingMethod.KELLY_CRITERION:
            if win_rate is None or avg_win is None or avg_loss is None:
                raise ValueError(
                    "Kelly Criterion requires win_rate, avg_win, and avg_loss"
                )
            return self._kelly_criterion_sizing(
                account_balance, win_rate, avg_win, avg_loss, entry_price, stop_loss
            )
        elif method == PositionSizingMethod.VOLATILITY_BASED:
            if volatility is None:
                raise ValueError(
                    "Volatility-based sizing requires volatility parameter"
                )
            return self._volatility_based_sizing(
                account_balance, risk_per_trade, volatility, entry_price
            )
        return 0.0

    def _fixed_fractional_sizing(
        self,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float,
    ) -> float:
        risk_amount = account_balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            return 0.0
        position_size = risk_amount / price_risk
        max_position = (
            account_balance * self.risk_limits.max_position_size / entry_price
        )
        return min(position_size, max_position)

    def _kelly_criterion_sizing(
        self,
        account_balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        entry_price: float,
        stop_loss: float,
    ) -> float:
        if avg_loss == 0:
            return 0.0
        b = abs(avg_win / avg_loss)
        p = win_rate
        q = 1 - win_rate
        kelly_fraction = (p * b - q) / b
        conservative_kelly = kelly_fraction * 0.5
        kelly_fraction = max(
            0.0, min(conservative_kelly, self.risk_limits.max_position_size)
        )
        return (account_balance * kelly_fraction) / entry_price

    def _volatility_based_sizing(
        self,
        account_balance: float,
        risk_per_trade: float,
        volatility: float,
        entry_price: float,
    ) -> float:
        target_volatility = 0.02
        if volatility == 0:
            return 0.0
        vol_adjustment = target_volatility / volatility
        risk_amount = account_balance * risk_per_trade * vol_adjustment
        position_size = risk_amount / (entry_price * volatility)
        max_position = (
            account_balance * self.risk_limits.max_position_size / entry_price
        )
        return min(position_size, max_position)

    def calculate_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        method: VaRMethod = VaRMethod.HISTORICAL,
        portfolio_value: float = 100000.0,
    ) -> tuple[float, float]:
        """Calculate Value at Risk."""
        if len(returns) == 0:
            return 0.0, 0.0
        if method == VaRMethod.HISTORICAL:
            return self._historical_var(returns, confidence_level, portfolio_value)
        # Add other methods as needed or import from scipy if available
        return self._historical_var(returns, confidence_level, portfolio_value)

    def _historical_var(
        self, returns: np.ndarray, confidence_level: float, portfolio_value: float
    ) -> tuple[float, float]:
        percentile = (1 - confidence_level) * 100
        var_return = np.percentile(returns, percentile)
        var = abs(var_return * portfolio_value)
        tail_losses = returns[returns <= var_return]
        expected_shortfall = (
            abs(np.mean(tail_losses) * portfolio_value) if len(tail_losses) > 0 else var
        )
        return var, expected_shortfall

    def check_risk_limits_v2(
        self, positions: list[dict], account_balance: float
    ) -> dict[str, Any]:
        """Check if current positions violate risk limits."""
        violations = []
        warnings = []
        total_exposure = sum(abs(p.get("value", 0)) for p in positions)
        exposure_ratio = total_exposure / account_balance if account_balance > 0 else 0
        if exposure_ratio > self.risk_limits.max_total_exposure:
            violations.append(
                f"Total exposure {exposure_ratio:.1%} exceeds limit {self.risk_limits.max_total_exposure:.1%}"
            )
        # Add more checks as needed
        return {
            "has_violations": len(violations) > 0,
            "violations": violations,
            "warnings": warnings,
            "metrics": {
                "total_exposure": exposure_ratio,
                "num_positions": len(positions),
            },
        }


# Global instance
advanced_risk_manager = AdvancedRiskManager.get_instance()
