"""
AI Copilot Service - Explain trades, generate strategies, optimize strategies, summarize backtesting
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TradeExplanation(BaseModel):
    """Trade explanation"""
    trade_id: str
    explanation: str
    reasoning: str
    technical_analysis: Dict[str, Any]
    risk_assessment: str
    confidence_score: float
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StrategyGenerationRequest(BaseModel):
    """Strategy generation request"""
    description: str
    timeframe: str = "1h"
    risk_level: str = "moderate"  # conservative, moderate, aggressive
    market_conditions: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class GeneratedStrategy(BaseModel):
    """Generated strategy"""
    name: str
    description: str
    strategy_type: str
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    risk_parameters: Dict[str, Any]
    code: Optional[str] = None
    confidence_score: float
    backtesting_ready: bool


class StrategyOptimizationRequest(BaseModel):
    """Strategy optimization request"""
    strategy_id: str
    optimization_goals: List[str]  # e.g., ["maximize_sharpe", "minimize_drawdown", "maximize_returns"]
    constraints: Optional[Dict[str, Any]] = None
    market_data_period: int = 30  # days


class OptimizationResult(BaseModel):
    """Strategy optimization result"""
    strategy_id: str
    original_params: Dict[str, Any]
    optimized_params: Dict[str, Any]
    improvements: Dict[str, float]  # e.g., {"sharpe_ratio": 0.15, "max_drawdown": -0.05}
    recommendations: List[str]
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BacktestSummaryRequest(BaseModel):
    """Backtest summary request"""
    backtest_id: str
    include_charts: bool = True
    include_detailed_metrics: bool = True
    focus_areas: Optional[List[str]] = None  # e.g., ["risk", "performance", "optimization"]


class BacktestSummary(BaseModel):
    """Backtest summary"""
    backtest_id: str
    executive_summary: str
    key_metrics: Dict[str, Any]
    performance_analysis: str
    risk_analysis: str
    optimization_opportunities: List[str]
    recommendations: List[str]
    charts_description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AICopilotService:
    """AI Copilot service for trading assistance"""
    
    def __init__(self):
        logger.info("AI Copilot Service initialized")
    
    async def explain_trade(
        self,
        trade_id: str,
        trade_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None
    ) -> TradeExplanation:
        """Generate natural language explanation of a trade"""
        try:
            # Extract trade information
            symbol = trade_data.get("symbol", "UNKNOWN")
            side = trade_data.get("side", "unknown")
            amount = trade_data.get("amount", 0)
            price = trade_data.get("price", 0)
            timestamp = trade_data.get("timestamp", datetime.utcnow().isoformat())
            
            # Generate explanation
            explanation = (
                f"This was a {side.upper()} order for {amount} {symbol} at ${price:,.2f}. "
                f"The trade was executed based on technical indicators suggesting "
            )
            
            # Add technical analysis context
            if market_data:
                explanation += self._generate_technical_context(market_data)
            else:
                explanation += "market conditions favorable for this position."
            
            # Generate reasoning
            reasoning = self._generate_reasoning(trade_data, market_data)
            
            # Technical analysis summary
            technical_analysis = self._extract_technical_indicators(market_data or {})
            
            # Risk assessment
            risk_assessment = self._assess_trade_risk(trade_data, market_data)
            
            # Confidence score
            confidence_score = self._calculate_confidence(trade_data, market_data)
            
            # Recommendations
            recommendations = self._generate_recommendations(trade_data, market_data)
            
            return TradeExplanation(
                trade_id=trade_id,
                explanation=explanation,
                reasoning=reasoning,
                technical_analysis=technical_analysis,
                risk_assessment=risk_assessment,
                confidence_score=confidence_score,
                recommendations=recommendations
            )
        
        except Exception as e:
            logger.error(f"Error explaining trade: {e}")
            raise
    
    def _generate_technical_context(self, market_data: Dict[str, Any]) -> str:
        """Generate technical analysis context"""
        indicators = market_data.get("indicators", {})
        
        context_parts = []
        
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            if rsi < 30:
                context_parts.append("oversold conditions (RSI < 30)")
            elif rsi > 70:
                context_parts.append("overbought conditions (RSI > 70)")
        
        if "macd" in indicators:
            macd_signal = indicators["macd"].get("signal", "neutral")
            if macd_signal == "bullish":
                context_parts.append("bullish MACD crossover")
            elif macd_signal == "bearish":
                context_parts.append("bearish MACD crossover")
        
        if "trend" in indicators:
            trend = indicators["trend"]
            if trend == "uptrend":
                context_parts.append("strong uptrend")
            elif trend == "downtrend":
                context_parts.append("downtrend with potential reversal")
        
        if context_parts:
            return ", ".join(context_parts) + "."
        return "standard technical indicators."
    
    def _generate_reasoning(
        self,
        trade_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate reasoning for trade"""
        side = trade_data.get("side", "unknown")
        
        if not market_data:
            return f"The {side} decision was based on configured strategy parameters."
        
        indicators = market_data.get("indicators", {})
        reasoning_parts = [f"Decided to {side.upper()} based on:"]
        
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            if rsi < 30:
                reasoning_parts.append(f"• RSI at {rsi:.1f} indicates oversold conditions")
            elif rsi > 70:
                reasoning_parts.append(f"• RSI at {rsi:.1f} indicates overbought conditions")
        
        if "support_resistance" in indicators:
            levels = indicators["support_resistance"]
            price = trade_data.get("price", 0)
            if "support" in levels and price <= levels["support"] * 1.02:
                reasoning_parts.append(f"• Price near support level at ${levels['support']:.2f}")
            elif "resistance" in levels and price >= levels["resistance"] * 0.98:
                reasoning_parts.append(f"• Price near resistance level at ${levels['resistance']:.2f}")
        
        if "volume" in indicators:
            volume_trend = indicators["volume"].get("trend", "neutral")
            if volume_trend == "increasing":
                reasoning_parts.append("• Increasing volume confirms trend strength")
        
        if len(reasoning_parts) == 1:
            reasoning_parts.append("• Strategy-based signal")
        
        return "\n".join(reasoning_parts)
    
    def _extract_technical_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract technical indicators from market data"""
        return market_data.get("indicators", {
            "rsi": None,
            "macd": None,
            "bollinger_bands": None,
            "moving_averages": None,
            "volume": None
        })
    
    def _assess_trade_risk(
        self,
        trade_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]]
    ) -> str:
        """Assess trade risk"""
        side = trade_data.get("side", "unknown")
        amount = trade_data.get("amount", 0)
        price = trade_data.get("price", 0)
        trade_value = amount * price
        
        risk_level = "MODERATE"
        risk_factors = []
        
        if trade_value > 10000:
            risk_level = "HIGH"
            risk_factors.append("Large position size")
        elif trade_value < 100:
            risk_level = "LOW"
            risk_factors.append("Small position size")
        
        if market_data:
            volatility = market_data.get("volatility", 0.02)
            if volatility > 0.05:
                risk_level = "HIGH"
                risk_factors.append("High market volatility")
            elif volatility < 0.01:
                risk_level = "LOW"
                risk_factors.append("Low market volatility")
        
        if risk_factors:
            return f"{risk_level} risk due to: {', '.join(risk_factors)}"
        return f"{risk_level} risk - Standard trading conditions"
    
    def _calculate_confidence(
        self,
        trade_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score"""
        base_confidence = 0.5
        
        if market_data:
            indicators = market_data.get("indicators", {})
            
            # RSI confidence
            if "rsi" in indicators:
                rsi = indicators["rsi"]
                if rsi < 30 or rsi > 70:
                    base_confidence += 0.15  # Strong signal
            
            # MACD confidence
            if "macd" in indicators and indicators["macd"].get("signal") != "neutral":
                base_confidence += 0.1
            
            # Volume confirmation
            if "volume" in indicators and indicators["volume"].get("trend") == "increasing":
                base_confidence += 0.1
        
        return min(1.0, max(0.0, base_confidence))
    
    def _generate_recommendations(
        self,
        trade_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate trade recommendations"""
        recommendations = []
        
        # Position sizing recommendation
        amount = trade_data.get("amount", 0)
        price = trade_data.get("price", 0)
        trade_value = amount * price
        
        if trade_value > 10000:
            recommendations.append("Consider reducing position size for better risk management")
        
        # Stop loss recommendation
        recommendations.append("Set a stop-loss at 2-3% below entry price")
        
        # Take profit recommendation
        recommendations.append("Set take-profit targets at 5-7% above entry price")
        
        # Market condition recommendations
        if market_data:
            volatility = market_data.get("volatility", 0.02)
            if volatility > 0.05:
                recommendations.append("High volatility detected - consider wider stop-loss")
        
        return recommendations
    
    async def generate_strategy_from_text(
        self,
        request: StrategyGenerationRequest
    ) -> GeneratedStrategy:
        """Generate trading strategy from natural language description"""
        try:
            description_lower = request.description.lower()
            
            # Determine strategy type
            strategy_type = "mean_reversion"
            if "trend" in description_lower or "momentum" in description_lower:
                strategy_type = "trend_following"
            elif "breakout" in description_lower:
                strategy_type = "breakout"
            elif "scalping" in description_lower or "quick" in description_lower:
                strategy_type = "scalping"
            elif "swing" in description_lower:
                strategy_type = "swing_trading"
            
            # Generate strategy name
            name = self._generate_strategy_name(request.description, strategy_type)
            
            # Generate entry conditions
            entry_conditions = self._generate_entry_conditions(request, strategy_type)
            
            # Generate exit conditions
            exit_conditions = self._generate_exit_conditions(request, strategy_type)
            
            # Generate risk parameters
            risk_parameters = self._generate_risk_parameters(request)
            
            # Generate strategy code (simplified)
            code = self._generate_strategy_code(name, entry_conditions, exit_conditions, risk_parameters)
            
            return GeneratedStrategy(
                name=name,
                description=request.description,
                strategy_type=strategy_type,
                entry_conditions=entry_conditions,
                exit_conditions=exit_conditions,
                risk_parameters=risk_parameters,
                code=code,
                confidence_score=0.75,
                backtesting_ready=True
            )
        
        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            raise
    
    def _generate_strategy_name(self, description: str, strategy_type: str) -> str:
        """Generate strategy name from description"""
        # Extract key words
        words = description.split()[:3]
        name = " ".join(words).title()
        return f"{name} {strategy_type.replace('_', ' ').title()} Strategy"
    
    def _generate_entry_conditions(
        self,
        request: StrategyGenerationRequest,
        strategy_type: str
    ) -> Dict[str, Any]:
        """Generate entry conditions based on strategy type"""
        base_conditions = {
            "timeframe": request.timeframe,
            "indicators": []
        }
        
        if strategy_type == "trend_following":
            base_conditions["indicators"] = [
                {"type": "moving_average", "fast": 20, "slow": 50, "condition": "crossover_up"},
                {"type": "macd", "condition": "bullish_signal"}
            ]
        elif strategy_type == "mean_reversion":
            base_conditions["indicators"] = [
                {"type": "rsi", "condition": "oversold", "threshold": 30},
                {"type": "bollinger_bands", "condition": "lower_band_touch"}
            ]
        elif strategy_type == "breakout":
            base_conditions["indicators"] = [
                {"type": "price", "condition": "above_resistance"},
                {"type": "volume", "condition": "above_average"}
            ]
        
        return base_conditions
    
    def _generate_exit_conditions(
        self,
        request: StrategyGenerationRequest,
        strategy_type: str
    ) -> Dict[str, Any]:
        """Generate exit conditions"""
        return {
            "stop_loss_percent": 2.0,
            "take_profit_percent": 5.0,
            "trailing_stop": True,
            "time_based_exit": False
        }
    
    def _generate_risk_parameters(self, request: StrategyGenerationRequest) -> Dict[str, Any]:
        """Generate risk parameters based on risk level"""
        risk_levels = {
            "conservative": {
                "risk_per_trade": 0.01,
                "max_position_size": 0.05,
                "max_daily_loss": 0.02
            },
            "moderate": {
                "risk_per_trade": 0.02,
                "max_position_size": 0.10,
                "max_daily_loss": 0.05
            },
            "aggressive": {
                "risk_per_trade": 0.05,
                "max_position_size": 0.20,
                "max_daily_loss": 0.10
            }
        }
        
        return risk_levels.get(request.risk_level, risk_levels["moderate"])
    
    def _generate_strategy_code(
        self,
        name: str,
        entry_conditions: Dict[str, Any],
        exit_conditions: Dict[str, Any],
        risk_parameters: Dict[str, Any]
    ) -> str:
        """Generate strategy code (simplified Python-like pseudocode)"""
        code = f"""
# {name}
# Generated Strategy Code

def should_enter_position(market_data):
    # Entry conditions
    indicators = market_data.get('indicators', {{}})
    {self._code_conditions(entry_conditions)}
    return True

def should_exit_position(position, market_data):
    # Exit conditions
    stop_loss = position['entry_price'] * (1 - {exit_conditions['stop_loss_percent'] / 100})
    take_profit = position['entry_price'] * (1 + {exit_conditions['take_profit_percent'] / 100})
    
    current_price = market_data.get('price', 0)
    if current_price <= stop_loss or current_price >= take_profit:
        return True
    return False
"""
        return code.strip()
    
    def _code_conditions(self, conditions: Dict[str, Any]) -> str:
        """Generate code for conditions"""
        # Simplified - in production would generate proper Python code
        return "# Check entry conditions"
    
    async def optimize_strategy(
        self,
        request: StrategyOptimizationRequest
    ) -> OptimizationResult:
        """Generate strategy optimization recommendations"""
        try:
            # Mock optimization - in production would use actual optimization algorithms
            original_params = {
                "risk_per_trade": 0.02,
                "stop_loss": 2.0,
                "take_profit": 5.0,
                "rsi_period": 14,
                "ma_fast": 20,
                "ma_slow": 50
            }
            
            optimized_params = original_params.copy()
            
            # Optimize based on goals
            improvements = {}
            recommendations = []
            
            if "maximize_sharpe" in request.optimization_goals:
                optimized_params["take_profit"] = 6.0
                optimized_params["stop_loss"] = 2.5
                improvements["sharpe_ratio"] = 0.15
                recommendations.append("Increased take-profit to 6% improves risk-adjusted returns")
            
            if "minimize_drawdown" in request.optimization_goals:
                optimized_params["stop_loss"] = 1.5
                optimized_params["risk_per_trade"] = 0.015
                improvements["max_drawdown"] = -0.05
                recommendations.append("Tighter stop-loss at 1.5% reduces maximum drawdown")
            
            if "maximize_returns" in request.optimization_goals:
                optimized_params["take_profit"] = 7.0
                optimized_params["risk_per_trade"] = 0.025
                improvements["total_return"] = 0.12
                recommendations.append("Increased position size and take-profit targets boost returns")
            
            return OptimizationResult(
                strategy_id=request.strategy_id,
                original_params=original_params,
                optimized_params=optimized_params,
                improvements=improvements,
                recommendations=recommendations,
                confidence_score=0.80
            )
        
        except Exception as e:
            logger.error(f"Error optimizing strategy: {e}")
            raise
    
    async def summarize_backtest(
        self,
        request: BacktestSummaryRequest,
        backtest_data: Dict[str, Any]
    ) -> BacktestSummary:
        """Generate AI summary of backtesting results"""
        try:
            # Extract key metrics
            metrics = backtest_data.get("metrics", {})
            
            # Generate executive summary
            total_return = metrics.get("total_return_pct", 0)
            sharpe_ratio = metrics.get("sharpe_ratio", 0)
            max_drawdown = metrics.get("max_drawdown", 0)
            
            executive_summary = (
                f"The backtest over {backtest_data.get('period_days', 30)} days "
                f"showed a total return of {total_return:.2f}% with a Sharpe ratio of {sharpe_ratio:.2f}. "
                f"Maximum drawdown was {abs(max_drawdown * 100):.2f}%. "
            )
            
            if sharpe_ratio > 1.5:
                executive_summary += "The strategy demonstrates strong risk-adjusted performance."
            elif sharpe_ratio > 1.0:
                executive_summary += "The strategy shows acceptable risk-adjusted returns."
            else:
                executive_summary += "The strategy may need optimization to improve risk-adjusted returns."
            
            # Performance analysis
            performance_analysis = self._analyze_performance(metrics)
            
            # Risk analysis
            risk_analysis = self._analyze_risk(metrics)
            
            # Optimization opportunities
            optimization_opportunities = self._identify_optimization_opportunities(metrics)
            
            # Recommendations
            recommendations = self._generate_backtest_recommendations(metrics)
            
            return BacktestSummary(
                backtest_id=request.backtest_id,
                executive_summary=executive_summary,
                key_metrics=metrics,
                performance_analysis=performance_analysis,
                risk_analysis=risk_analysis,
                optimization_opportunities=optimization_opportunities,
                recommendations=recommendations
            )
        
        except Exception as e:
            logger.error(f"Error summarizing backtest: {e}")
            raise
    
    def _analyze_performance(self, metrics: Dict[str, Any]) -> str:
        """Analyze backtest performance"""
        total_return = metrics.get("total_return_pct", 0)
        win_rate = metrics.get("win_rate", 0)
        profit_factor = metrics.get("profit_factor", 0)
        
        analysis = f"Performance Analysis:\n"
        analysis += f"• Total Return: {total_return:.2f}%\n"
        analysis += f"• Win Rate: {win_rate * 100:.1f}%\n"
        analysis += f"• Profit Factor: {profit_factor:.2f}\n"
        
        if win_rate > 0.55:
            analysis += "The strategy shows a strong win rate, indicating good entry/exit timing."
        elif win_rate < 0.45:
            analysis += "The win rate is below 50%, suggesting entry conditions may need refinement."
        
        return analysis
    
    def _analyze_risk(self, metrics: Dict[str, Any]) -> str:
        """Analyze backtest risk"""
        max_drawdown = abs(metrics.get("max_drawdown", 0) * 100)
        sharpe_ratio = metrics.get("sharpe_ratio", 0)
        volatility = metrics.get("volatility", 0)
        
        analysis = f"Risk Analysis:\n"
        analysis += f"• Maximum Drawdown: {max_drawdown:.2f}%\n"
        analysis += f"• Sharpe Ratio: {sharpe_ratio:.2f}\n"
        analysis += f"• Volatility: {volatility * 100:.2f}%\n"
        
        if max_drawdown > 20:
            analysis += "High drawdown detected - consider tighter risk controls."
        elif max_drawdown < 10:
            analysis += "Drawdown is well-controlled, indicating good risk management."
        
        return analysis
    
    def _identify_optimization_opportunities(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []
        
        win_rate = metrics.get("win_rate", 0)
        if win_rate < 0.50:
            opportunities.append("Improve entry conditions to increase win rate")
        
        sharpe_ratio = metrics.get("sharpe_ratio", 0)
        if sharpe_ratio < 1.0:
            opportunities.append("Optimize risk-reward ratios to improve Sharpe ratio")
        
        max_drawdown = abs(metrics.get("max_drawdown", 0))
        if max_drawdown > 0.15:
            opportunities.append("Implement tighter stop-losses to reduce drawdown")
        
        return opportunities
    
    def _generate_backtest_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations from backtest"""
        recommendations = []
        
        total_return = metrics.get("total_return_pct", 0)
        if total_return > 0:
            recommendations.append("Strategy shows positive returns - consider paper trading")
        else:
            recommendations.append("Strategy needs refinement before live trading")
        
        sharpe_ratio = metrics.get("sharpe_ratio", 0)
        if sharpe_ratio < 1.0:
            recommendations.append("Consider optimizing parameters to improve risk-adjusted returns")
        
        recommendations.append("Continue monitoring performance with additional backtests")
        recommendations.append("Consider implementing the strategy with small position sizes initially")
        
        return recommendations


# Global service instance
copilot_service = AICopilotService()
