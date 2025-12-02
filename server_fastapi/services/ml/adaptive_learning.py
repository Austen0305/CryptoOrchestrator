"""
Adaptive Learning Service for Trading Bots
Continuously learns from trading history and adapts strategies
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveLearningService:
    """
    Service that learns from trading history and adapts bot strategies
    """
    
    def __init__(self):
        self.pattern_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.strategy_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.market_regime_memory: Dict[str, Dict[str, Any]] = {}
        self.learning_metrics: Dict[str, float] = {
            "total_trades_analyzed": 0,
            "successful_patterns": 0,
            "failed_patterns": 0,
            "learning_accuracy": 0.0,
            "confidence_improvement": 0.0,
            "adaptation_rate": 0.0,
        }
    
    async def analyze_trade_pattern(self, trade: Dict[str, Any], market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a completed trade to extract learning patterns
        
        Args:
            trade: Completed trade data
            market_data: Market data at time of trade
            
        Returns:
            Pattern analysis with insights
        """
        try:
            # Extract pattern from market data before trade
            if len(market_data) < 10:
                return {"pattern": None, "confidence": 0.0}
            
            # Detect pattern type (simplified - in production, use full pattern recognition)
            closes = [m["close"] for m in market_data[-20:]]
            pattern_type = self._detect_simple_pattern(closes)
            
            # Record pattern outcome
            is_successful = (trade.get("pnl", 0) or 0) > 0
            pattern_key = f"{pattern_type}_{trade.get('symbol', 'UNKNOWN')}"
            
            self.pattern_history[pattern_key].append({
                "timestamp": datetime.now(),
                "trade_id": trade.get("id"),
                "successful": is_successful,
                "pnl": trade.get("pnl", 0),
                "market_condition": self._detect_market_regime(closes),
            })
            
            # Update learning metrics
            self.learning_metrics["total_trades_analyzed"] += 1
            if is_successful:
                self.learning_metrics["successful_patterns"] += 1
            else:
                self.learning_metrics["failed_patterns"] += 1
            
            # Recalculate learning accuracy
            total_patterns = (
                self.learning_metrics["successful_patterns"] + 
                self.learning_metrics["failed_patterns"]
            )
            if total_patterns > 0:
                self.learning_metrics["learning_accuracy"] = (
                    self.learning_metrics["successful_patterns"] / total_patterns * 100
                )
            
            return {
                "pattern": pattern_type,
                "confidence": self.learning_metrics["learning_accuracy"] / 100,
                "pattern_key": pattern_key,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trade pattern: {e}", exc_info=True)
            return {"pattern": None, "confidence": 0.0}
    
    def get_pattern_success_rate(self, pattern_key: str) -> float:
        """Get success rate for a specific pattern"""
        if pattern_key not in self.pattern_history or not self.pattern_history[pattern_key]:
            return 0.5  # Default to neutral
        
        patterns = self.pattern_history[pattern_key]
        successful = sum(1 for p in patterns if p["successful"])
        total = len(patterns)
        
        return successful / total if total > 0 else 0.5
    
    def get_recommendation(self, pattern_key: str) -> str:
        """Get recommendation for a pattern (favor/neutral/avoid)"""
        success_rate = self.get_pattern_success_rate(pattern_key)
        
        if success_rate >= 0.70:
            return "favor"
        elif success_rate >= 0.55:
            return "neutral"
        else:
            return "avoid"
    
    def adapt_strategy_parameters(
        self, 
        market_regime: str, 
        historical_performance: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Adapt bot parameters based on market regime and historical performance
        
        Args:
            market_regime: Current market condition (bull/bear/ranging)
            historical_performance: Historical trade performance data
            
        Returns:
            Optimized parameters for current regime
        """
        try:
            # Calculate performance metrics for regime
            regime_trades = [t for t in historical_performance 
                           if t.get("market_regime") == market_regime]
            
            if not regime_trades:
                # Default parameters
                return {
                    "confidence_threshold": 0.65,
                    "position_size_multiplier": 1.0,
                    "stop_loss_pct": 0.02,
                    "take_profit_pct": 0.05,
                }
            
            # Calculate optimal parameters based on performance
            win_rate = sum(1 for t in regime_trades if t.get("pnl", 0) > 0) / len(regime_trades)
            avg_return = np.mean([t.get("pnl", 0) for t in regime_trades]) if regime_trades else 0.0
            volatility = np.std([t.get("pnl", 0) for t in regime_trades]) if len(regime_trades) > 1 else 0.0
            
            # Adapt based on regime
            if market_regime == "bull":
                return {
                    "confidence_threshold": max(0.6, min(0.75, 0.7 - (win_rate - 0.6) * 0.2)),
                    "position_size_multiplier": max(0.8, min(1.5, 1.0 + (win_rate - 0.6) * 0.5)),
                    "stop_loss_pct": max(0.015, min(0.03, 0.02 + volatility * 0.5)),
                    "take_profit_pct": max(0.04, min(0.08, 0.05 + (win_rate - 0.6) * 0.1)),
                }
            elif market_regime == "bear":
                return {
                    "confidence_threshold": max(0.7, min(0.85, 0.75 + (1 - win_rate) * 0.2)),
                    "position_size_multiplier": max(0.5, min(1.0, 0.8 - (1 - win_rate) * 0.3)),
                    "stop_loss_pct": max(0.01, min(0.025, 0.015 - volatility * 0.3)),
                    "take_profit_pct": max(0.02, min(0.05, 0.03 - (1 - win_rate) * 0.05)),
                }
            else:  # ranging
                return {
                    "confidence_threshold": max(0.65, min(0.75, 0.7)),
                    "position_size_multiplier": 1.0,
                    "stop_loss_pct": max(0.015, min(0.025, 0.018)),
                    "take_profit_pct": max(0.03, min(0.05, 0.035)),
                }
                
        except Exception as e:
            logger.error(f"Error adapting strategy parameters: {e}", exc_info=True)
            return {
                "confidence_threshold": 0.65,
                "position_size_multiplier": 1.0,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.05,
            }
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics"""
        return self.learning_metrics.copy()
    
    def get_pattern_analysis(self, min_occurrences: int = 5) -> List[Dict[str, Any]]:
        """Get analysis of all learned patterns"""
        results = []
        
        for pattern_key, patterns in self.pattern_history.items():
            if len(patterns) < min_occurrences:
                continue
            
            successful = [p for p in patterns if p["successful"]]
            failed = [p for p in patterns if not p["successful"]]
            
            success_rate = len(successful) / len(patterns) * 100
            avg_profit = np.mean([p["pnl"] for p in patterns]) if patterns else 0.0
            
            results.append({
                "pattern": pattern_key.split("_")[0],
                "success_rate": success_rate,
                "avg_profit": avg_profit,
                "occurrences": len(patterns),
                "last_seen": max(p["timestamp"] for p in patterns).isoformat(),
                "recommendation": self.get_recommendation(pattern_key),
            })
        
        # Sort by success rate descending
        results.sort(key=lambda x: x["success_rate"], reverse=True)
        return results
    
    def _detect_simple_pattern(self, closes: List[float]) -> str:
        """Detect simple chart patterns (simplified version)"""
        if len(closes) < 5:
            return "unknown"
        
        # Simple trend detection
        recent_trend = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
        
        if recent_trend > 0.02:
            return "uptrend"
        elif recent_trend < -0.02:
            return "downtrend"
        else:
            return "range"
    
    def _detect_market_regime(self, closes: List[float]) -> str:
        """Detect market regime from price data"""
        if len(closes) < 20:
            return "unknown"
        
        # Simple regime detection based on volatility and trend
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns)
        trend = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0
        
        if volatility > 0.03:
            return "volatile"
        elif trend > 0.05:
            return "bull"
        elif trend < -0.05:
            return "bear"
        else:
            return "ranging"


# Global instance
adaptive_learning_service = AdaptiveLearningService()

