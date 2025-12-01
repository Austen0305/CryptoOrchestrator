"""
Value at Risk (VaR) Service - Calculate VaR and CVaR for portfolio risk assessment
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


class VaRConfig(BaseModel):
    """VaR calculation configuration"""
    confidence_level: float = 0.95  # 95% confidence level
    time_horizon_days: int = 1  # 1 day horizon
    method: str = "historical"  # 'historical', 'parametric', 'monte_carlo'


class VaRResult(BaseModel):
    """VaR calculation result"""
    var_absolute: float  # VaR in absolute currency units
    var_percent: float  # VaR as percentage of portfolio
    cvar_absolute: float  # Conditional VaR (Expected Shortfall) in absolute units
    cvar_percent: float  # CVaR as percentage of portfolio
    confidence_level: float
    time_horizon_days: int
    method: str
    portfolio_value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VaRService:
    """Service for calculating Value at Risk (VaR) and Conditional VaR (CVaR)"""
    
    def __init__(self):
        logger.info("VaR Service initialized")
    
    def calculate_var(
        self,
        returns: List[float],
        portfolio_value: float,
        config: Optional[VaRConfig] = None
    ) -> VaRResult:
        """Calculate Value at Risk using specified method"""
        config = config or VaRConfig()
        
        try:
            if not returns or len(returns) < 2:
                # No data or insufficient data
                return VaRResult(
                    var_absolute=0.0,
                    var_percent=0.0,
                    cvar_absolute=0.0,
                    cvar_percent=0.0,
                    confidence_level=config.confidence_level,
                    time_horizon_days=config.time_horizon_days,
                    method=config.method,
                    portfolio_value=portfolio_value
                )
            
            returns_array = np.array(returns)
            
            if config.method == "historical":
                return self._calculate_historical_var(returns_array, portfolio_value, config)
            elif config.method == "parametric":
                return self._calculate_parametric_var(returns_array, portfolio_value, config)
            elif config.method == "monte_carlo":
                return self._calculate_monte_carlo_var(returns_array, portfolio_value, config)
            else:
                # Default to historical
                return self._calculate_historical_var(returns_array, portfolio_value, config)
        
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return VaRResult(
                var_absolute=0.0,
                var_percent=0.0,
                cvar_absolute=0.0,
                cvar_percent=0.0,
                confidence_level=config.confidence_level,
                time_horizon_days=config.time_horizon_days,
                method=config.method,
                portfolio_value=portfolio_value
            )
    
    def _calculate_historical_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        config: VaRConfig
    ) -> VaRResult:
        """Calculate VaR using historical simulation method"""
        # Sort returns
        sorted_returns = np.sort(returns)
        
        # Calculate VaR at confidence level
        percentile = (1 - config.confidence_level) * 100
        var_return = np.percentile(sorted_returns, percentile)
        
        # VaR is the negative of the percentile (loss)
        var_return = abs(var_return) if var_return < 0 else 0.0
        
        # Scale for time horizon
        horizon_scale = np.sqrt(config.time_horizon_days)
        var_return_scaled = var_return * horizon_scale
        
        # Calculate VaR in absolute terms
        var_absolute = portfolio_value * var_return_scaled
        var_percent = var_return_scaled * 100
        
        # Calculate Conditional VaR (Expected Shortfall)
        # Average of losses beyond VaR threshold
        threshold_idx = int((1 - config.confidence_level) * len(sorted_returns))
        tail_returns = sorted_returns[:threshold_idx] if threshold_idx > 0 else sorted_returns[:1]
        
        if len(tail_returns) > 0:
            cvar_return = abs(np.mean(tail_returns)) if np.mean(tail_returns) < 0 else 0.0
            cvar_return_scaled = cvar_return * horizon_scale
            cvar_absolute = portfolio_value * cvar_return_scaled
            cvar_percent = cvar_return_scaled * 100
        else:
            cvar_absolute = var_absolute
            cvar_percent = var_percent
        
        return VaRResult(
            var_absolute=var_absolute,
            var_percent=var_percent,
            cvar_absolute=cvar_absolute,
            cvar_percent=cvar_percent,
            confidence_level=config.confidence_level,
            time_horizon_days=config.time_horizon_days,
            method="historical",
            portfolio_value=portfolio_value
        )
    
    def _calculate_parametric_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        config: VaRConfig
    ) -> VaRResult:
        """Calculate VaR using parametric (variance-covariance) method"""
        # Assume returns are normally distributed
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Scale for time horizon
        horizon_scale = np.sqrt(config.time_horizon_days)
        std_scaled = std_return * horizon_scale
        
        # Calculate z-score for confidence level
        # Approximate z-scores for normal distribution
        # 90% = 1.28, 95% = 1.65, 99% = 2.33
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33,
            0.975: 1.96,
            0.995: 2.58
        }
        # Interpolate for other confidence levels or use default
        z_score = z_scores.get(config.confidence_level)
        if z_score is None:
            # Linear interpolation approximation
            if config.confidence_level < 0.95:
                z_score = 1.28 + (config.confidence_level - 0.90) * (1.65 - 1.28) / (0.95 - 0.90)
            elif config.confidence_level < 0.99:
                z_score = 1.65 + (config.confidence_level - 0.95) * (2.33 - 1.65) / (0.99 - 0.95)
            else:
                z_score = 2.33  # Default to 99% z-score
        
        # VaR calculation (assuming mean is zero for simplicity)
        var_return = abs(z_score * std_scaled)
        
        # Calculate VaR in absolute terms
        var_absolute = portfolio_value * var_return
        var_percent = var_return * 100
        
        # CVaR for normal distribution
        # CVaR ≈ VaR * (1 + z_score^2 / 2) for normal distribution
        cvar_multiplier = 1 + (z_score ** 2) / 2
        cvar_return = var_return * cvar_multiplier
        cvar_absolute = portfolio_value * cvar_return
        cvar_percent = cvar_return * 100
        
        return VaRResult(
            var_absolute=var_absolute,
            var_percent=var_percent,
            cvar_absolute=cvar_absolute,
            cvar_percent=cvar_percent,
            confidence_level=config.confidence_level,
            time_horizon_days=config.time_horizon_days,
            method="parametric",
            portfolio_value=portfolio_value
        )
    
    def _calculate_monte_carlo_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        config: VaRConfig,
        num_simulations: int = 10000
    ) -> VaRResult:
        """Calculate VaR using Monte Carlo simulation"""
        # Estimate parameters from historical returns
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Scale for time horizon
        horizon_scale = np.sqrt(config.time_horizon_days)
        
        # Generate Monte Carlo simulations
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(
            mean_return * config.time_horizon_days,
            std_return * horizon_scale,
            num_simulations
        )
        
        # Sort simulated returns
        sorted_simulated = np.sort(simulated_returns)
        
        # Calculate VaR
        percentile = (1 - config.confidence_level) * 100
        var_return = np.percentile(sorted_simulated, percentile)
        var_return = abs(var_return) if var_return < 0 else 0.0
        
        # Calculate VaR in absolute terms
        var_absolute = portfolio_value * var_return
        var_percent = var_return * 100
        
        # Calculate CVaR
        threshold_idx = int((1 - config.confidence_level) * len(sorted_simulated))
        tail_returns = sorted_simulated[:threshold_idx] if threshold_idx > 0 else sorted_simulated[:1]
        
        if len(tail_returns) > 0:
            cvar_return = abs(np.mean(tail_returns)) if np.mean(tail_returns) < 0 else 0.0
            cvar_absolute = portfolio_value * cvar_return
            cvar_percent = cvar_return * 100
        else:
            cvar_absolute = var_absolute
            cvar_percent = var_percent
        
        return VaRResult(
            var_absolute=var_absolute,
            var_percent=var_percent,
            cvar_absolute=cvar_absolute,
            cvar_percent=cvar_percent,
            confidence_level=config.confidence_level,
            time_horizon_days=config.time_horizon_days,
            method="monte_carlo",
            portfolio_value=portfolio_value
        )
    
    def calculate_multi_horizon_var(
        self,
        returns: List[float],
        portfolio_value: float,
        confidence_level: float = 0.95,
        horizons: List[int] = [1, 7, 30]
    ) -> List[Dict[str, Any]]:
        """Calculate VaR for multiple time horizons"""
        results = []
        
        for horizon in horizons:
            config = VaRConfig(
                confidence_level=confidence_level,
                time_horizon_days=horizon,
                method="historical"
            )
            var_result = self.calculate_var(returns, portfolio_value, config)
            
            results.append({
                'horizon_days': horizon,
                'var_absolute': var_result.var_absolute,
                'var_percent': var_result.var_percent,
                'cvar_absolute': var_result.cvar_absolute,
                'cvar_percent': var_result.cvar_percent
            })
        
        return results


# Global service instance
var_service = VaRService()
