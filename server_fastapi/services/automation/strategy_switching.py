"""
Strategy Switching Service - Adaptive strategy selection
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """Market regime types"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BEARISH = "bearish"
    BULLISH = "bullish"


class StrategySwitchConfig(BaseModel):
    """Strategy switching configuration"""
    enabled: bool = True
    switch_on_regime_change: bool = True
    switch_on_performance: bool = True
    performance_threshold: float = -0.10  # Switch if strategy underperforms by 10%
    check_interval_seconds: int = 3600  # Check every hour
    min_performance_period_hours: int = 24  # Minimum period before switching


class StrategyPerformance(BaseModel):
    """Strategy performance metrics"""
    strategy_id: str
    strategy_name: str
    returns: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    period_hours: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StrategySwitch(BaseModel):
    """Strategy switch record"""
    from_strategy: str
    to_strategy: str
    reason: str
    regime: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StrategySwitchingService:
    """Strategy switching service for adaptive strategy selection"""
    
    def __init__(self):
        self.active_strategies: Dict[str, str] = {}  # bot_id -> strategy_id
        self.strategy_performances: Dict[str, List[StrategyPerformance]] = {}
        self.switch_history: List[StrategySwitch] = []
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        logger.info("Strategy Switching Service initialized")
    
    async def start_monitoring(
        self,
        bot_id: str,
        config: StrategySwitchConfig
    ) -> bool:
        """Start monitoring bot for strategy switching"""
        try:
            if bot_id in self.monitoring_tasks:
                logger.warning(f"Strategy switching already monitoring bot {bot_id}")
                return False
            
            self.monitoring_tasks[bot_id] = asyncio.create_task(
                self._monitor_and_switch(bot_id, config)
            )
            
            logger.info(f"Started strategy switching monitoring for bot {bot_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting strategy switching: {e}")
            return False
    
    async def stop_monitoring(self, bot_id: str) -> bool:
        """Stop monitoring bot for strategy switching"""
        try:
            if bot_id in self.monitoring_tasks:
                self.monitoring_tasks[bot_id].cancel()
                try:
                    await self.monitoring_tasks[bot_id]
                except asyncio.CancelledError:
                    pass
                del self.monitoring_tasks[bot_id]
                
                logger.info(f"Stopped strategy switching monitoring for bot {bot_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error stopping strategy switching: {e}")
            return False
    
    async def _monitor_and_switch(
        self,
        bot_id: str,
        config: StrategySwitchConfig
    ) -> None:
        """Monitor bot performance and switch strategies"""
        while True:
            try:
                if not config.enabled:
                    await asyncio.sleep(config.check_interval_seconds)
                    continue
                
                # Detect market regime
                regime = await self._detect_market_regime(bot_id)
                
                # Get current strategy performance
                current_strategy = self.active_strategies.get(bot_id)
                if current_strategy:
                    performance = await self._evaluate_strategy_performance(
                        bot_id,
                        current_strategy,
                        config
                    )
                    
                    if performance:
                        self.strategy_performances.setdefault(bot_id, []).append(performance)
                        
                        # Check if switching needed
                        if config.switch_on_performance:
                            should_switch = await self._should_switch_on_performance(
                                bot_id,
                                performance,
                                config
                            )
                            
                            if should_switch:
                                await self._switch_strategy(bot_id, current_strategy, regime, "performance")
                        
                        if config.switch_on_regime_change:
                            should_switch = await self._should_switch_on_regime(
                                bot_id,
                                current_strategy,
                                regime,
                                config
                            )
                            
                            if should_switch:
                                await self._switch_strategy(bot_id, current_strategy, regime, "regime_change")
                
                await asyncio.sleep(config.check_interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in strategy switching monitor: {e}")
                await asyncio.sleep(config.check_interval_seconds)
    
    async def _detect_market_regime(self, bot_id: str) -> MarketRegime:
        """Detect current market regime"""
        # Mock implementation - would use market regime detection service
        # For now, return a default regime
        return MarketRegime.TRENDING
    
    async def _evaluate_strategy_performance(
        self,
        bot_id: str,
        strategy_id: str,
        config: StrategySwitchConfig
    ) -> Optional[StrategyPerformance]:
        """Evaluate strategy performance"""
        # Mock implementation - would query actual performance data
        return StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=f"Strategy {strategy_id}",
            returns=0.05,
            sharpe_ratio=1.5,
            max_drawdown=0.08,
            win_rate=0.55,
            period_hours=24
        )
    
    async def _should_switch_on_performance(
        self,
        bot_id: str,
        performance: StrategyPerformance,
        config: StrategySwitchConfig
    ) -> bool:
        """Determine if strategy should switch based on performance"""
        if performance.period_hours < config.min_performance_period_hours:
            return False
        
        # Check if performance is below threshold
        if performance.returns < config.performance_threshold:
            return True
        
        # Check if drawdown is excessive
        if abs(performance.max_drawdown) > 0.15:
            return True
        
        # Check if Sharpe ratio is too low
        if performance.sharpe_ratio < 0.5:
            return True
        
        return False
    
    async def _should_switch_on_regime(
        self,
        bot_id: str,
        current_strategy: str,
        regime: MarketRegime,
        config: StrategySwitchConfig
    ) -> bool:
        """Determine if strategy should switch based on regime"""
        # Mock implementation - would check if current strategy is suitable for regime
        regime_strategies = {
            MarketRegime.TRENDING: ["trend_following", "momentum"],
            MarketRegime.RANGING: ["mean_reversion", "scalping"],
            MarketRegime.VOLATILE: ["volatility_breakout", "gap_trading"],
            MarketRegime.BEARISH: ["short_biases", "inverse_strategies"],
            MarketRegime.BULLISH: ["long_biases", "trend_following"]
        }
        
        suitable_strategies = regime_strategies.get(regime, [])
        return current_strategy not in suitable_strategies
    
    async def _switch_strategy(
        self,
        bot_id: str,
        from_strategy: str,
        regime: MarketRegime,
        reason: str
    ) -> bool:
        """Switch bot to a new strategy"""
        try:
            # Select new strategy based on regime
            new_strategy = await self._select_strategy_for_regime(regime, from_strategy)
            
            # Record switch
            switch = StrategySwitch(
                from_strategy=from_strategy,
                to_strategy=new_strategy,
                reason=reason,
                regime=regime.value
            )
            self.switch_history.append(switch)
            
            # Update active strategy
            self.active_strategies[bot_id] = new_strategy
            
            logger.info(
                f"Switched bot {bot_id} from {from_strategy} to {new_strategy} "
                f"(reason: {reason}, regime: {regime.value})"
            )
            
            # In production, would update bot configuration in database
            return True
        
        except Exception as e:
            logger.error(f"Error switching strategy: {e}")
            return False
    
    async def _select_strategy_for_regime(
        self,
        regime: MarketRegime,
        current_strategy: str
    ) -> str:
        """Select appropriate strategy for market regime"""
        regime_strategies = {
            MarketRegime.TRENDING: "trend_following",
            MarketRegime.RANGING: "mean_reversion",
            MarketRegime.VOLATILE: "volatility_breakout",
            MarketRegime.BEARISH: "short_bias",
            MarketRegime.BULLISH: "long_bias"
        }
        
        return regime_strategies.get(regime, "trend_following")
    
    def get_switch_history(self, bot_id: Optional[str] = None, limit: int = 50) -> List[StrategySwitch]:
        """Get strategy switch history"""
        history = self.switch_history
        
        if bot_id:
            # Filter by bot_id if provided (would need to track bot_id in switch records)
            pass
        
        return history[-limit:] if history else []


# Global service instance
strategy_switching_service = StrategySwitchingService()
