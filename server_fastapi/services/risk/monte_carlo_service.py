"""
Monte Carlo Simulation Service - Portfolio risk analysis through simulation
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


class MonteCarloConfig(BaseModel):
    """Monte Carlo simulation configuration"""
    num_simulations: int = 10000
    time_horizon_days: int = 30
    confidence_level: float = 0.95
    random_seed: Optional[int] = 42


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation result"""
    simulations: List[float]  # Simulated portfolio values
    mean_return: float
    std_return: float
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    cvar_95: float  # 95% Conditional VaR
    probability_of_loss: float  # Probability of negative return
    expected_shortfall: float
    best_case: float  # Best case scenario (top 5%)
    worst_case: float  # Worst case scenario (bottom 5%)
    median_return: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MonteCarloService:
    """Service for Monte Carlo simulation of portfolio returns"""
    
    def __init__(self):
        logger.info("Monte Carlo Service initialized")
    
    def run_simulation(
        self,
        historical_returns: List[float],
        initial_value: float,
        config: Optional[MonteCarloConfig] = None
    ) -> MonteCarloResult:
        """Run Monte Carlo simulation"""
        config = config or MonteCarloConfig()
        
        try:
            if not historical_returns or len(historical_returns) < 2:
                # Insufficient data
                return MonteCarloResult(
                    simulations=[],
                    mean_return=0.0,
                    std_return=0.0,
                    var_95=0.0,
                    var_99=0.0,
                    cvar_95=0.0,
                    probability_of_loss=0.0,
                    expected_shortfall=0.0,
                    best_case=initial_value,
                    worst_case=initial_value,
                    median_return=0.0
                )
            
            returns_array = np.array(historical_returns)
            
            # Estimate parameters from historical data
            mean_daily_return = np.mean(returns_array)
            std_daily_return = np.std(returns_array)
            
            # Set random seed for reproducibility
            if config.random_seed:
                np.random.seed(config.random_seed)
            
            # Simulate returns for each day
            simulated_returns = []
            
            for _ in range(config.num_simulations):
                # Generate daily returns for time horizon
                daily_returns = np.random.normal(
                    mean_daily_return,
                    std_daily_return,
                    config.time_horizon_days
                )
                
                # Calculate cumulative return
                cumulative_return = np.prod(1 + daily_returns) - 1
                simulated_returns.append(cumulative_return)
            
            simulated_returns = np.array(simulated_returns)
            
            # Calculate final portfolio values
            simulated_values = initial_value * (1 + simulated_returns)
            
            # Calculate statistics
            mean_return = np.mean(simulated_returns)
            std_return = np.std(simulated_returns)
            median_return = np.median(simulated_returns)
            
            # Calculate VaR at different confidence levels
            var_95 = np.percentile(simulated_returns, 5)  # 5th percentile (95% VaR)
            var_99 = np.percentile(simulated_returns, 1)  # 1st percentile (99% VaR)
            
            # Make VaR positive (it's a loss)
            var_95 = abs(var_95) if var_95 < 0 else 0.0
            var_99 = abs(var_99) if var_99 < 0 else 0.0
            
            # Calculate Conditional VaR (Expected Shortfall) at 95%
            tail_returns_95 = simulated_returns[simulated_returns <= np.percentile(simulated_returns, 5)]
            if len(tail_returns_95) > 0:
                cvar_95 = abs(np.mean(tail_returns_95)) if np.mean(tail_returns_95) < 0 else 0.0
            else:
                cvar_95 = var_95
            
            # Probability of loss
            probability_of_loss = np.sum(simulated_returns < 0) / len(simulated_returns)
            
            # Expected shortfall (average of all negative returns)
            negative_returns = simulated_returns[simulated_returns < 0]
            expected_shortfall = abs(np.mean(negative_returns)) if len(negative_returns) > 0 else 0.0
            
            # Best and worst cases (top and bottom 5%)
            best_case = np.percentile(simulated_values, 95)
            worst_case = np.percentile(simulated_values, 5)
            
            return MonteCarloResult(
                simulations=simulated_values.tolist(),
                mean_return=float(mean_return),
                std_return=float(std_return),
                var_95=float(var_95),
                var_99=float(var_99),
                cvar_95=float(cvar_95),
                probability_of_loss=float(probability_of_loss),
                expected_shortfall=float(expected_shortfall),
                best_case=float(best_case),
                worst_case=float(worst_case),
                median_return=float(median_return)
            )
        
        except Exception as e:
            logger.error(f"Error running Monte Carlo simulation: {e}")
            return MonteCarloResult(
                simulations=[],
                mean_return=0.0,
                std_return=0.0,
                var_95=0.0,
                var_99=0.0,
                cvar_95=0.0,
                probability_of_loss=0.0,
                expected_shortfall=0.0,
                best_case=initial_value,
                worst_case=initial_value,
                median_return=0.0
            )
    
    def calculate_risk_of_ruin(
        self,
        historical_returns: List[float],
        initial_value: float,
        target_value: float = 0.0,  # Ruin threshold (0 = total loss)
        num_simulations: int = 10000,
        time_horizon_days: int = 365
    ) -> Dict[str, float]:
        """Calculate risk of ruin (probability of falling below target value)"""
        try:
            if not historical_returns or len(historical_returns) < 2:
                return {
                    'risk_of_ruin': 0.0,
                    'expected_time_to_ruin': None,
                    'probability_below_target': 0.0
                }
            
            returns_array = np.array(historical_returns)
            mean_daily = np.mean(returns_array)
            std_daily = np.std(returns_array)
            
            np.random.seed(42)
            ruin_count = 0
            times_to_ruin = []
            
            for _ in range(num_simulations):
                current_value = initial_value
                days_to_ruin = None
                
                for day in range(time_horizon_days):
                    # Generate daily return
                    daily_return = np.random.normal(mean_daily, std_daily)
                    current_value *= (1 + daily_return)
                    
                    # Check for ruin
                    if current_value <= target_value:
                        ruin_count += 1
                        if days_to_ruin is None:
                            days_to_ruin = day + 1
                        break
                
                if days_to_ruin is not None:
                    times_to_ruin.append(days_to_ruin)
            
            risk_of_ruin = ruin_count / num_simulations
            expected_time_to_ruin = np.mean(times_to_ruin) if times_to_ruin else None
            
            return {
                'risk_of_ruin': float(risk_of_ruin),
                'expected_time_to_ruin': float(expected_time_to_ruin) if expected_time_to_ruin else None,
                'probability_below_target': float(risk_of_ruin)
            }
        
        except Exception as e:
            logger.error(f"Error calculating risk of ruin: {e}")
            return {
                'risk_of_ruin': 0.0,
                'expected_time_to_ruin': None,
                'probability_below_target': 0.0
            }


# Global service instance
monte_carlo_service = MonteCarloService()
