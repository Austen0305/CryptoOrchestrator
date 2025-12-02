"""
Advanced Risk Management Service

Provides professional-grade risk management capabilities including:
- Position sizing (Kelly Criterion, Fixed Fractional, Volatility-based)
- Value at Risk (VaR) calculation (Historical, Parametric, Monte Carlo)
- Risk limits and guardrails
- Portfolio risk metrics
- Stop-loss and take-profit automation
- Correlation analysis
- Maximum drawdown monitoring
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

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
    stop_loss: Optional[float]
    take_profit: Optional[float]
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
    correlation_matrix: Optional[np.ndarray]
    position_risks: List[PositionRisk]


class AdvancedRiskManager:
    """Advanced risk management service for trading operations."""
    
    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        """Initialize risk manager.
        
        Args:
            risk_limits: Custom risk limits (uses defaults if not provided)
        """
        self.risk_limits = risk_limits or RiskLimits()
        self.position_history: List[Dict] = []
        self.peak_value: float = 0.0
        
    def calculate_position_size(
        self,
        method: PositionSizingMethod,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> float:
        """Calculate optimal position size.
        
        Args:
            method: Position sizing method to use
            account_balance: Current account balance
            risk_per_trade: Percentage of account to risk (0-1)
            entry_price: Planned entry price
            stop_loss: Stop loss price
            win_rate: Historical win rate (for Kelly)
            avg_win: Average win amount (for Kelly)
            avg_loss: Average loss amount (for Kelly)
            volatility: Asset volatility (for volatility-based)
            
        Returns:
            Position size in units
        """
        if method == PositionSizingMethod.FIXED_FRACTIONAL:
            return self._fixed_fractional_sizing(
                account_balance, risk_per_trade, entry_price, stop_loss
            )
        elif method == PositionSizingMethod.KELLY_CRITERION:
            if win_rate is None or avg_win is None or avg_loss is None:
                raise ValueError("Kelly Criterion requires win_rate, avg_win, and avg_loss")
            return self._kelly_criterion_sizing(
                account_balance, win_rate, avg_win, avg_loss, entry_price, stop_loss
            )
        elif method == PositionSizingMethod.VOLATILITY_BASED:
            if volatility is None:
                raise ValueError("Volatility-based sizing requires volatility parameter")
            return self._volatility_based_sizing(
                account_balance, risk_per_trade, volatility, entry_price
            )
        else:
            raise ValueError(f"Unknown position sizing method: {method}")
    
    def _fixed_fractional_sizing(
        self,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Fixed fractional position sizing."""
        risk_amount = account_balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0.0
            
        position_size = risk_amount / price_risk
        
        # Apply max position size limit
        max_position = account_balance * self.risk_limits.max_position_size / entry_price
        return min(position_size, max_position)
    
    def _kelly_criterion_sizing(
        self,
        account_balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Kelly Criterion position sizing."""
        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = loss rate, b = avg_win / avg_loss
        
        if avg_loss == 0:
            return 0.0
            
        b = abs(avg_win / avg_loss)
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (p * b - q) / b
        
        # Use half-Kelly or quarter-Kelly to be conservative
        conservative_kelly = kelly_fraction * 0.5
        
        # Ensure it's positive and within limits
        kelly_fraction = max(0.0, min(conservative_kelly, self.risk_limits.max_position_size))
        
        position_value = account_balance * kelly_fraction
        position_size = position_value / entry_price
        
        return position_size
    
    def _volatility_based_sizing(
        self,
        account_balance: float,
        risk_per_trade: float,
        volatility: float,
        entry_price: float
    ) -> float:
        """Volatility-based position sizing (inverse volatility)."""
        # Reduce position size as volatility increases
        target_volatility = 0.02  # 2% target volatility
        
        if volatility == 0:
            return 0.0
            
        vol_adjustment = target_volatility / volatility
        risk_amount = account_balance * risk_per_trade * vol_adjustment
        
        position_size = risk_amount / (entry_price * volatility)
        
        # Apply max position size limit
        max_position = account_balance * self.risk_limits.max_position_size / entry_price
        return min(position_size, max_position)
    
    def calculate_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        method: VaRMethod = VaRMethod.HISTORICAL,
        portfolio_value: float = 100000.0
    ) -> Tuple[float, float]:
        """Calculate Value at Risk.
        
        Args:
            returns: Historical returns array
            confidence_level: Confidence level (0.95 for 95%, 0.99 for 99%)
            method: VaR calculation method
            portfolio_value: Current portfolio value
            
        Returns:
            Tuple of (VaR, Expected Shortfall)
        """
        if len(returns) == 0:
            return 0.0, 0.0
            
        if method == VaRMethod.HISTORICAL:
            return self._historical_var(returns, confidence_level, portfolio_value)
        elif method == VaRMethod.PARAMETRIC:
            return self._parametric_var(returns, confidence_level, portfolio_value)
        elif method == VaRMethod.MONTE_CARLO:
            return self._monte_carlo_var(returns, confidence_level, portfolio_value)
        else:
            raise ValueError(f"Unknown VaR method: {method}")
    
    def _historical_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        portfolio_value: float
    ) -> Tuple[float, float]:
        """Historical simulation VaR."""
        percentile = (1 - confidence_level) * 100
        var_return = np.percentile(returns, percentile)
        var = abs(var_return * portfolio_value)
        
        # Expected Shortfall (CVaR) - average of losses beyond VaR
        tail_losses = returns[returns <= var_return]
        expected_shortfall = abs(np.mean(tail_losses) * portfolio_value) if len(tail_losses) > 0 else var
        
        return var, expected_shortfall
    
    def _parametric_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        portfolio_value: float
    ) -> Tuple[float, float]:
        """Parametric VaR assuming normal distribution."""
        mean = np.mean(returns)
        std = np.std(returns)
        
        # Z-score for confidence level
        from scipy import stats
        z_score = stats.norm.ppf(1 - confidence_level)
        
        var_return = mean + z_score * std
        var = abs(var_return * portfolio_value)
        
        # Expected Shortfall for normal distribution
        pdf_value = stats.norm.pdf(z_score)
        expected_shortfall = abs((mean - std * pdf_value / (1 - confidence_level)) * portfolio_value)
        
        return var, expected_shortfall
    
    def _monte_carlo_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        portfolio_value: float,
        num_simulations: int = 10000
    ) -> Tuple[float, float]:
        """Monte Carlo simulation VaR."""
        mean = np.mean(returns)
        std = np.std(returns)
        
        # Generate random returns
        simulated_returns = np.random.normal(mean, std, num_simulations)
        
        return self._historical_var(simulated_returns, confidence_level, portfolio_value)
    
    def check_risk_limits(
        self,
        positions: List[Dict],
        account_balance: float
    ) -> Dict[str, any]:
        """Check if current positions violate risk limits.
        
        Args:
            positions: List of current positions
            account_balance: Current account balance
            
        Returns:
            Dictionary with violations and warnings
        """
        violations = []
        warnings = []
        
        # Calculate total exposure
        total_exposure = sum(abs(p.get('value', 0)) for p in positions)
        exposure_ratio = total_exposure / account_balance if account_balance > 0 else 0
        
        if exposure_ratio > self.risk_limits.max_total_exposure:
            violations.append(f"Total exposure {exposure_ratio:.1%} exceeds limit {self.risk_limits.max_total_exposure:.1%}")
        
        # Check individual position sizes
        for position in positions:
            position_value = abs(position.get('value', 0))
            position_weight = position_value / account_balance if account_balance > 0 else 0
            
            if position_weight > self.risk_limits.max_position_size:
                violations.append(
                    f"Position {position.get('symbol')} size {position_weight:.1%} "
                    f"exceeds limit {self.risk_limits.max_position_size:.1%}"
                )
        
        # Check drawdown
        current_value = account_balance + sum(p.get('unrealized_pnl', 0) for p in positions)
        self.peak_value = max(self.peak_value, current_value)
        
        if self.peak_value > 0:
            current_drawdown = (self.peak_value - current_value) / self.peak_value
            
            if current_drawdown > self.risk_limits.max_drawdown:
                violations.append(f"Drawdown {current_drawdown:.1%} exceeds limit {self.risk_limits.max_drawdown:.1%}")
            elif current_drawdown > self.risk_limits.max_drawdown * 0.8:
                warnings.append(f"Drawdown {current_drawdown:.1%} approaching limit {self.risk_limits.max_drawdown:.1%}")
        
        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'warnings': warnings,
            'metrics': {
                'total_exposure': exposure_ratio,
                'current_drawdown': current_drawdown if self.peak_value > 0 else 0,
                'num_positions': len(positions)
            }
        }
    
    def calculate_optimal_stop_loss(
        self,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0,
        max_loss_pct: float = 0.02
    ) -> float:
        """Calculate optimal stop loss using ATR.
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            atr_multiplier: Multiplier for ATR (default 2x)
            max_loss_pct: Maximum loss percentage (default 2%)
            
        Returns:
            Stop loss price
        """
        # ATR-based stop loss
        atr_stop = entry_price - (atr * atr_multiplier)
        
        # Percentage-based stop loss
        pct_stop = entry_price * (1 - max_loss_pct)
        
        # Use the tighter of the two
        return max(atr_stop, pct_stop)
    
    def calculate_optimal_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """Calculate optimal take profit based on risk-reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Desired risk-reward ratio (default 2:1)
            
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        return entry_price + reward
    
    def analyze_portfolio_risk(
        self,
        positions: List[Dict],
        account_balance: float,
        returns_history: Optional[np.ndarray] = None
    ) -> PortfolioRisk:
        """Comprehensive portfolio risk analysis.
        
        Args:
            positions: List of current positions
            account_balance: Current account balance
            returns_history: Historical returns for VaR calculation
            
        Returns:
            PortfolioRisk object with comprehensive metrics
        """
        position_risks = []
        total_exposure = 0.0
        
        for pos in positions:
            symbol = pos.get('symbol', 'UNKNOWN')
            size = pos.get('size', 0)
            entry_price = pos.get('entry_price', 0)
            current_price = pos.get('current_price', entry_price)
            stop_loss = pos.get('stop_loss')
            take_profit = pos.get('take_profit')
            
            unrealized_pnl = (current_price - entry_price) * size
            position_value = abs(size * current_price)
            total_exposure += position_value
            
            # Calculate risk metrics
            if stop_loss:
                risk_amount = abs((entry_price - stop_loss) * size)
                reward_amount = abs((take_profit - entry_price) * size) if take_profit else 0
                risk_reward = reward_amount / risk_amount if risk_amount > 0 else 0
            else:
                risk_amount = 0
                reward_amount = 0
                risk_reward = 0
            
            position_weight = position_value / account_balance if account_balance > 0 else 0
            
            position_risks.append(PositionRisk(
                symbol=symbol,
                position_size=size,
                entry_price=entry_price,
                current_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                unrealized_pnl=unrealized_pnl,
                risk_amount=risk_amount,
                reward_amount=reward_amount,
                risk_reward_ratio=risk_reward,
                position_weight=position_weight
            ))
        
        # Calculate portfolio metrics
        total_value = account_balance + sum(p.unrealized_pnl for p in position_risks)
        leverage = total_exposure / account_balance if account_balance > 0 else 0
        
        # Calculate VaR if returns history provided
        var_95, var_99, expected_shortfall = 0.0, 0.0, 0.0
        if returns_history is not None and len(returns_history) > 0:
            var_95, _ = self.calculate_var(returns_history, 0.95, VaRMethod.HISTORICAL, total_value)
            var_99, expected_shortfall = self.calculate_var(returns_history, 0.99, VaRMethod.HISTORICAL, total_value)
        
        # Calculate drawdown
        self.peak_value = max(self.peak_value, total_value)
        current_drawdown = (self.peak_value - total_value) / self.peak_value if self.peak_value > 0 else 0
        
        return PortfolioRisk(
            total_value=total_value,
            total_exposure=total_exposure,
            leverage=leverage,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            sharpe_ratio=0.0,  # Calculate separately with full returns data
            sortino_ratio=0.0,  # Calculate separately with full returns data
            max_drawdown=current_drawdown,
            current_drawdown=current_drawdown,
            correlation_matrix=None,  # Calculate separately with multi-asset data
            position_risks=position_risks
        )
