from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime
import math
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"


class VolatilityTrend(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class Position(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    INSIDE = "inside"


class Direction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TimeFrame(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


@dataclass
class MarketData:
    timestamp: int
    close: float
    high: float
    low: float
    open: float
    volume: float


@dataclass
class Portfolio:
    positions: Dict[str, Dict[str, Any]]
    totalBalance: float
    profitLossTotal: float


@dataclass
class Trade:
    timestamp: int
    side: str
    total: float
    pair: str


class MarketAnalysisResult(BaseModel):
    pair: str
    timestamp: int
    trend: Dict[str, Any]
    volatility: Dict[str, Any]
    support: Dict[str, Any]
    resistance: Dict[str, Any]
    volume: Dict[str, Any]
    indicators: Dict[str, Any]
    prediction: Dict[str, Any]


class PortfolioAnalysisResult(BaseModel):
    timestamp: int
    totalValue: float
    totalReturn: float
    totalReturnPercent: float
    dailyReturn: float
    dailyReturnPercent: float
    volatility: float
    sharpeRatio: float
    maxDrawdown: float
    maxDrawdownPercent: float
    var: Dict[str, float]
    correlationMatrix: Dict[str, Dict[str, float]]
    riskContribution: Dict[str, float]
    performanceAttribution: Dict[str, float]
    diversificationRatio: float
    efficientFrontier: Dict[str, Dict[str, float]]


class TradeAnalysisResult(BaseModel):
    timestamp: int
    totalTrades: int
    winningTrades: int
    losingTrades: int
    winRate: float
    averageWin: float
    averageLoss: float
    profitFactor: float
    expectancy: float
    largestWin: float
    largestLoss: float
    averageTradeDuration: float
    averageWinDuration: float
    averageLossDuration: float
    consecutiveWins: int
    consecutiveLosses: int
    monthlyReturns: Dict[str, float]
    tradeDistribution: Dict[str, Dict[str, float]]
    performanceByPair: Dict[str, Dict[str, Any]]


class AdvancedAnalyticsEngine:
    async def analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data based on type and parameters"""
        analysis_type = params.get("type")
        user_id = params.get("user_id")

        if analysis_type == "risk":
            return await self._analyze_risk(user_id)
        elif analysis_type == "portfolio":
            period = params.get("period", "30d")
            return await self._analyze_portfolio(user_id, period)
        elif analysis_type == "backtesting":
            strategy_id = params.get("strategy_id")
            backtest_id = params.get("backtest_id")
            return await self._analyze_backtesting(user_id, strategy_id, backtest_id)
        elif analysis_type == "dashboard":
            return await self._analyze_dashboard(user_id)
        elif analysis_type == "realtime":
            return await self._analyze_realtime(user_id)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

    async def _analyze_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Analyze dashboard data for comprehensive summary"""
        try:
            # Get portfolio data
            portfolio_result = await self._analyze_portfolio(user_id, "1d")

            # Get risk data
            risk_result = await self._analyze_risk(user_id)

            # Combine results
            dashboard_data = {
                "summary": {
                    "total_portfolio_value": portfolio_result.summary.get(
                        "totalValue", 100000.0
                    ),
                    "daily_pnl": portfolio_result.summary.get("dailyReturn", 0.0),
                    "daily_pnl_percent": portfolio_result.summary.get(
                        "dailyReturnPercent", 0.0
                    ),
                    "sharpe_ratio": risk_result.summary.get("sharpeRatio", 0.0),
                    "volatility": risk_result.summary.get("volatility", 0.0),
                    "max_drawdown": risk_result.summary.get("maxDrawdown", 0.0),
                },
                "details": {
                    "portfolio": portfolio_result.details,
                    "risk": risk_result.details,
                },
            }

            return dashboard_data
        except Exception as e:
            logger.error(f"Error in dashboard analysis: {e}")
            return {"summary": {}, "details": {}}

    async def _analyze_realtime(self, user_id: int) -> Dict[str, Any]:
        """Analyze real-time metrics"""
        try:
            # Get current portfolio status
            portfolio_result = await self._analyze_portfolio(user_id, "1d")

            # Simulate real-time data
            realtime_data = {
                "summary": {
                    "portfolio_value": portfolio_result.summary.get(
                        "totalValue", 100000.0
                    ),
                    "active_positions": 5,  # Mock
                    "system_health": "healthy",
                    "last_update": datetime.now().isoformat(),
                },
                "details": {
                    "active_trades": [],  # Would be populated with actual trade data
                    "performance_metrics": {
                        "win_rate_today": 0.65,
                        "avg_trade_duration": "4.2h",
                        "total_trades_today": 12,
                    },
                },
            }

            return realtime_data
        except Exception as e:
            logger.error(f"Error in realtime analysis: {e}")
            return {"summary": {}, "details": {}}

    @staticmethod
    async def analyze_market(
        pair: str, data: List[MarketData]
    ) -> Optional[MarketAnalysisResult]:
        try:
            if len(data) < 50:
                logger.warning(
                    "市场分析数据不足", extra={"pair": pair, "dataLength": len(data)}
                )
                return None

            # Calculate trend
            trend = AdvancedAnalyticsEngine._calculate_trend(data)

            # Calculate volatility
            volatility = AdvancedAnalyticsEngine._calculate_volatility(data)

            # Calculate support and resistance
            support = AdvancedAnalyticsEngine._calculate_support(data)
            resistance = AdvancedAnalyticsEngine._calculate_resistance(data)

            # Calculate volume metrics
            volume = AdvancedAnalyticsEngine._calculate_volume_metrics(data)

            # Calculate indicators
            indicators = AdvancedAnalyticsEngine._calculate_indicators(data)

            # Generate prediction
            prediction = AdvancedAnalyticsEngine._generate_prediction(
                trend, volatility, indicators
            )

            result = MarketAnalysisResult(
                pair=pair,
                timestamp=int(datetime.now().timestamp() * 1000),
                trend=trend,
                volatility=volatility,
                support=support,
                resistance=resistance,
                volume=volume,
                indicators=indicators,
                prediction=prediction,
            )

            return result
        except Exception as error:
            logger.error("市场分析失败", extra={"error": str(error), "pair": pair})
            return None

    @staticmethod
    async def analyze_portfolio(
        portfolio: Portfolio, trades: List[Trade]
    ) -> Optional[PortfolioAnalysisResult]:
        try:
            if not portfolio.positions or len(portfolio.positions) == 0:
                logger.warning("投资组合为空")
                return None

            # Calculate basic metrics
            total_value = portfolio.totalBalance
            total_return = portfolio.profitLossTotal
            total_return_percent = (total_return / (total_value - total_return)) * 100

            # Calculate daily returns
            daily_returns = AdvancedAnalyticsEngine._calculate_daily_returns(trades)
            daily_return = daily_returns[-1] if daily_returns else 0
            daily_return_percent = daily_return * 100

            # Calculate volatility
            volatility = AdvancedAnalyticsEngine._calculate_returns_volatility(
                daily_returns
            )

            # Calculate Sharpe ratio
            sharpe_ratio = AdvancedAnalyticsEngine._calculate_sharpe_ratio(
                daily_returns
            )

            # Calculate max drawdown
            max_drawdown = AdvancedAnalyticsEngine._calculate_max_drawdown(trades)
            max_drawdown_percent = (max_drawdown / total_value) * 100

            # Calculate VaR
            var_95 = AdvancedAnalyticsEngine._calculate_var(daily_returns, 0.95)
            var_99 = AdvancedAnalyticsEngine._calculate_var(daily_returns, 0.99)

            # Calculate correlation matrix
            correlation_matrix = AdvancedAnalyticsEngine._calculate_correlation_matrix(
                portfolio, trades
            )

            # Calculate risk contribution
            risk_contribution = AdvancedAnalyticsEngine._calculate_risk_contribution(
                portfolio, correlation_matrix
            )

            # Calculate performance attribution
            performance_attribution = (
                AdvancedAnalyticsEngine._calculate_performance_attribution(
                    portfolio, trades
                )
            )

            # Calculate diversification ratio
            diversification_ratio = (
                AdvancedAnalyticsEngine._calculate_diversification_ratio(
                    correlation_matrix
                )
            )

            # Calculate efficient frontier
            efficient_frontier = AdvancedAnalyticsEngine._calculate_efficient_frontier(
                portfolio, trades
            )

            result = PortfolioAnalysisResult(
                timestamp=int(datetime.now().timestamp() * 1000),
                totalValue=total_value,
                totalReturn=total_return,
                totalReturnPercent=total_return_percent,
                dailyReturn=daily_return,
                dailyReturnPercent=daily_return_percent,
                volatility=volatility,
                sharpeRatio=sharpe_ratio,
                maxDrawdown=max_drawdown,
                maxDrawdownPercent=max_drawdown_percent,
                var={"daily95": var_95, "daily99": var_99},
                correlationMatrix=correlation_matrix,
                riskContribution=risk_contribution,
                performanceAttribution=performance_attribution,
                diversificationRatio=diversification_ratio,
                efficientFrontier=efficient_frontier,
            )

            return result
        except Exception as error:
            logger.error("投资组合分析失败", extra={"error": str(error)})
            return None

    @staticmethod
    async def analyze_trades(trades: List[Trade]) -> Optional[TradeAnalysisResult]:
        try:
            if not trades:
                logger.warning("没有交易数据可分析")
                return None

            # Calculate basic statistics
            total_trades = len(trades)
            winning_trades = len(
                [t for t in trades if t.side == "sell" and t.total > 0]
            )
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades) * 100

            # Calculate average win/loss
            profits = [t.total for t in trades if t.side == "sell" and t.total > 0]
            losses = [abs(t.total) for t in trades if t.side == "sell" and t.total < 0]

            average_win = sum(profits) / len(profits) if profits else 0
            average_loss = sum(losses) / len(losses) if losses else 0

            # Calculate profit factor and expectancy
            profit_factor = sum(profits) / sum(losses) if losses else 0
            expectancy = (win_rate / 100 * average_win) - (
                (100 - win_rate) / 100 * average_loss
            )

            # Calculate largest win/loss
            largest_win = max(profits) if profits else 0
            largest_loss = max(losses) if losses else 0

            # Calculate average trade duration (simplified)
            average_trade_duration = 24  # hours

            # Calculate consecutive stats (simplified)
            consecutive_wins, consecutive_losses = (
                AdvancedAnalyticsEngine._calculate_consecutive_stats(trades)
            )

            # Calculate monthly returns (simplified)
            monthly_returns = AdvancedAnalyticsEngine._calculate_monthly_returns(trades)

            # Calculate trade distribution (simplified)
            trade_distribution = AdvancedAnalyticsEngine._calculate_trade_distribution(
                trades
            )

            # Calculate performance by pair (simplified)
            performance_by_pair = (
                AdvancedAnalyticsEngine._calculate_performance_by_pair(trades)
            )

            result = TradeAnalysisResult(
                timestamp=int(datetime.now().timestamp() * 1000),
                totalTrades=total_trades,
                winningTrades=winning_trades,
                losingTrades=losing_trades,
                winRate=win_rate,
                averageWin=average_win,
                averageLoss=average_loss,
                profitFactor=profit_factor,
                expectancy=expectancy,
                largestWin=largest_win,
                largestLoss=largest_loss,
                averageTradeDuration=average_trade_duration,
                averageWinDuration=24,  # simplified
                averageLossDuration=24,  # simplified
                consecutiveWins=consecutive_wins,
                consecutiveLosses=consecutive_losses,
                monthlyReturns=monthly_returns,
                tradeDistribution=trade_distribution,
                performanceByPair=performance_by_pair,
            )

            return result
        except Exception as error:
            logger.error(
                "交易分析失败", extra={"error": str(error), "tradesCount": len(trades)}
            )
            return None

    @staticmethod
    def _calculate_trend(data: List[MarketData]) -> Dict[str, Any]:
        # Linear regression trend calculation
        n = len(data)
        x_values = list(range(n))
        y_values = [d.close for d in data]

        # Calculate linear regression coefficients
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

        # Determine direction and strength
        if slope > 0.001:
            direction = TrendDirection.BULLISH
            strength = min(slope * 100, 1)
        elif slope < -0.001:
            direction = TrendDirection.BEARISH
            strength = min(abs(slope) * 100, 1)
        else:
            direction = TrendDirection.SIDEWAYS
            strength = 0.1

        duration = strength * 24  # hours

        return {
            "direction": direction.value,
            "strength": strength,
            "duration": duration,
        }

    @staticmethod
    def _calculate_volatility(data: List[MarketData]) -> Dict[str, Any]:
        # Calculate daily returns
        returns = []
        for i in range(1, len(data)):
            returns.append((data[i].close - data[i - 1].close) / data[i - 1].close)

        # Current volatility (recent 20 days)
        recent_returns = returns[-20:]
        current = math.sqrt(sum(r * r for r in recent_returns) / len(recent_returns))

        # Average volatility
        average = math.sqrt(sum(r * r for r in returns) / len(returns))

        # Volatility trend
        recent_volatility = math.sqrt(
            sum(r * r for r in recent_returns) / len(recent_returns)
        )
        older_volatility = math.sqrt(sum(r * r for r in returns[-40:-20]) / 20)

        if recent_volatility > older_volatility * 1.1:
            trend = VolatilityTrend.INCREASING
        elif recent_volatility < older_volatility * 0.9:
            trend = VolatilityTrend.DECREASING
        else:
            trend = VolatilityTrend.STABLE

        return {"current": current, "average": average, "trend": trend.value}

    @staticmethod
    def _calculate_support(data: List[MarketData]) -> Dict[str, Any]:
        recent_data = data[-50:]
        local_minima = []

        for i in range(1, len(recent_data) - 1):
            if (
                recent_data[i].low < recent_data[i - 1].low
                and recent_data[i].low < recent_data[i + 1].low
            ):
                local_minima.append(recent_data[i].low)

        current_price = recent_data[-1].close
        valid_supports = [m for m in local_minima if m < current_price]

        if not valid_supports:
            return {"level": current_price * 0.95, "strength": 0.3}

        support_level = sum(valid_supports) / len(valid_supports)
        strength = (
            min(len(valid_supports) / len(local_minima), 1) if local_minima else 0.3
        )

        return {"level": support_level, "strength": strength}

    @staticmethod
    def _calculate_resistance(data: List[MarketData]) -> Dict[str, Any]:
        recent_data = data[-50:]
        local_maxima = []

        for i in range(1, len(recent_data) - 1):
            if (
                recent_data[i].high > recent_data[i - 1].high
                and recent_data[i].high > recent_data[i + 1].high
            ):
                local_maxima.append(recent_data[i].high)

        current_price = recent_data[-1].close
        valid_resistances = [m for m in local_maxima if m > current_price]

        if not valid_resistances:
            return {"level": current_price * 1.05, "strength": 0.3}

        resistance_level = sum(valid_resistances) / len(valid_resistances)
        strength = (
            min(len(valid_resistances) / len(local_maxima), 1) if local_maxima else 0.3
        )

        return {"level": resistance_level, "strength": strength}

    @staticmethod
    def _calculate_volume_metrics(data: List[MarketData]) -> Dict[str, Any]:
        current = data[-1].volume
        average = sum(d.volume for d in data) / len(data)
        ratio = current / average

        return {"current": current, "average": average, "ratio": ratio}

    @staticmethod
    def _calculate_indicators(data: List[MarketData]) -> Dict[str, Any]:
        rsi = AdvancedAnalyticsEngine._calculate_rsi(data)
        macd = AdvancedAnalyticsEngine._calculate_macd(data)
        bollinger = AdvancedAnalyticsEngine._calculate_bollinger_bands(data)

        return {"rsi": rsi, "macd": macd, "bollinger": bollinger}

    @staticmethod
    def _generate_prediction(
        trend: Dict[str, Any], volatility: Dict[str, Any], indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        reasoning = []
        direction = Direction.HOLD.value
        confidence = 0.5
        timeframe = TimeFrame.MEDIUM.value

        # Trend-based prediction
        if (
            trend["direction"] == TrendDirection.BULLISH.value
            and trend["strength"] > 0.6
        ):
            direction = Direction.BUY.value
            confidence += 0.2
            reasoning.append(f"强上升趋势 ({trend['strength'] * 100:.1f}%)")
            timeframe = (
                TimeFrame.LONG.value
                if trend["duration"] > 12
                else TimeFrame.MEDIUM.value
            )
        elif (
            trend["direction"] == TrendDirection.BEARISH.value
            and trend["strength"] > 0.6
        ):
            direction = Direction.SELL.value
            confidence += 0.2
            reasoning.append(f"强下降趋势 ({trend['strength'] * 100:.1f}%)")
            timeframe = (
                TimeFrame.LONG.value
                if trend["duration"] > 12
                else TimeFrame.MEDIUM.value
            )

        # RSI-based prediction
        if indicators["rsi"] < 30:
            if direction != Direction.BUY.value:
                direction = Direction.BUY.value
                confidence = 0.6
            else:
                confidence += 0.1
            reasoning.append(f"RSI超卖 ({indicators['rsi']:.1f})")
        elif indicators["rsi"] > 70:
            if direction != Direction.SELL.value:
                direction = Direction.SELL.value
                confidence = 0.6
            else:
                confidence += 0.1
            reasoning.append(f"RSI超买 ({indicators['rsi']:.1f})")

        # MACD-based prediction
        if (
            indicators["macd"]["histogram"] > 0
            and indicators["macd"]["value"] > indicators["macd"]["signal"]
        ):
            if direction != Direction.BUY.value:
                direction = Direction.BUY.value
                confidence = 0.55
            else:
                confidence += 0.1
            reasoning.append("MACD看涨信号")

        # Bollinger bands-based prediction
        if indicators["bollinger"]["position"] == Position.BELOW.value:
            if direction != Direction.BUY.value:
                direction = Direction.BUY.value
                confidence = 0.5
            else:
                confidence += 0.05
            reasoning.append("价格低于布林带下轨")

        # Volatility adjustment
        if volatility["trend"] == VolatilityTrend.INCREASING.value:
            confidence = max(confidence - 0.1, 0.3)
            reasoning.append("高波动率降低预测置信度")

        confidence = min(max(confidence, 0.3), 0.9)

        return {
            "direction": direction,
            "confidence": confidence,
            "timeframe": timeframe,
            "reasoning": reasoning,
        }

    @staticmethod
    def _calculate_rsi(data: List[MarketData], period: int = 14) -> float:
        if len(data) < period + 1:
            return 50

        gains = []
        losses = []

        for i in range(1, min(len(data), period + 1)):
            change = data[i].close - data[i - 1].close
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    @staticmethod
    def _calculate_macd(
        data: List[MarketData],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, float]:
        if len(data) < slow_period:
            return {"value": 0, "signal": 0, "histogram": 0}

        # Simplified EMA calculation
        def ema(data: List[float], period: int) -> float:
            if not data:
                return 0
            multiplier = 2 / (period + 1)
            ema_val = data[0]
            for val in data[1:]:
                ema_val = (val - ema_val) * multiplier + ema_val
            return ema_val

        closes = [d.close for d in data]
        fast_ema = ema(closes, fast_period)
        slow_ema = ema(closes, slow_period)

        macd_value = fast_ema - slow_ema
        signal = macd_value * 0.2  # Simplified signal calculation
        histogram = macd_value - signal

        return {"value": macd_value, "signal": signal, "histogram": histogram}

    @staticmethod
    def _calculate_bollinger_bands(
        data: List[MarketData], period: int = 20, std_dev: float = 2
    ) -> Dict[str, Any]:
        if len(data) < period:
            current = data[-1].close
            return {
                "upper": current,
                "middle": current,
                "lower": current,
                "position": Position.INSIDE.value,
            }

        recent_data = data[-period:]
        closes = [d.close for d in recent_data]

        middle = sum(closes) / period
        variance = sum((close - middle) ** 2 for close in closes) / period
        standard_deviation = math.sqrt(variance)

        upper = middle + (standard_deviation * std_dev)
        lower = middle - (standard_deviation * std_dev)

        current_price = data[-1].close
        if current_price > upper:
            position = Position.ABOVE.value
        elif current_price < lower:
            position = Position.BELOW.value
        else:
            position = Position.INSIDE.value

        return {"upper": upper, "middle": middle, "lower": lower, "position": position}

    @staticmethod
    def _calculate_daily_returns(trades: List[Trade]) -> List[float]:
        # Simplified implementation
        return [0.01, 0.005, -0.002]  # Mock daily returns

    @staticmethod
    def _calculate_returns_volatility(returns: List[float]) -> float:
        if not returns:
            return 0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)

        return math.sqrt(variance)

    @staticmethod
    def _calculate_sharpe_ratio(
        returns: List[float], risk_free_rate: float = 0.02
    ) -> float:
        if not returns:
            return 0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        standard_deviation = math.sqrt(variance)

        if standard_deviation == 0:
            return 0

        annualized_return = mean * 252
        annualized_volatility = standard_deviation * math.sqrt(252)
        daily_risk_free_rate = risk_free_rate / 252

        return (annualized_return - risk_free_rate) / annualized_volatility

    @staticmethod
    def _calculate_max_drawdown(trades: List[Trade]) -> float:
        if not trades:
            return 0

        cumulative_profit = 0
        peak = 0
        max_drawdown = 0

        for trade in trades:
            cumulative_profit += trade.total

            if cumulative_profit > peak:
                peak = cumulative_profit

            drawdown = peak - cumulative_profit
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    @staticmethod
    def _calculate_var(returns: List[float], confidence: float) -> float:
        if not returns:
            return 0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))

        return sorted_returns[index]

    @staticmethod
    def _calculate_correlation_matrix(
        portfolio: Portfolio, trades: List[Trade]
    ) -> Dict[str, Dict[str, float]]:
        assets = list(portfolio.positions.keys())
        matrix = {}

        for asset1 in assets:
            matrix[asset1] = {}

            for asset2 in assets:
                if asset1 == asset2:
                    matrix[asset1][asset2] = 1.0
                else:
                    # Simplified correlation calculation
                    matrix[asset1][asset2] = 0.2 + hash(asset1 + asset2) % 600 / 1000

        return matrix

    @staticmethod
    def _calculate_risk_contribution(
        portfolio: Portfolio, correlation_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        assets = list(portfolio.positions.keys())
        contributions = {}

        total_risk = sum(portfolio.positions[asset]["totalValue"] for asset in assets)

        for asset in assets:
            weight = portfolio.positions[asset]["totalValue"] / total_risk
            contribution = weight

            # Add correlation-based contribution
            for other_asset in assets:
                if asset != other_asset:
                    other_weight = (
                        portfolio.positions[other_asset]["totalValue"] / total_risk
                    )
                    contribution += (
                        weight
                        * other_weight
                        * correlation_matrix[asset][other_asset]
                        * 0.5
                    )

            contributions[asset] = contribution

        return contributions

    @staticmethod
    def _calculate_performance_attribution(
        portfolio: Portfolio, trades: List[Trade]
    ) -> Dict[str, float]:
        return {"assetAllocation": 0.4, "securitySelection": 0.5, "interaction": 0.1}

    @staticmethod
    def _calculate_diversification_ratio(
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> float:
        assets = list(correlation_matrix.keys())

        if len(assets) <= 1:
            return 1

        total_correlation = 0
        count = 0

        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                total_correlation += abs(correlation_matrix[assets[i]][assets[j]])
                count += 1

        average_correlation = total_correlation / count if count > 0 else 0

        return 1 / (1 + average_correlation)

    @staticmethod
    def _calculate_efficient_frontier(
        portfolio: Portfolio, trades: List[Trade]
    ) -> Dict[str, Dict[str, float]]:
        current_return = portfolio.profitLossTotal / (
            portfolio.totalBalance - portfolio.profitLossTotal
        )
        current_risk = 0.15

        return {
            "lowRisk": {"risk": 0.08, "return": 0.05},
            "mediumRisk": {"risk": current_risk, "return": current_return},
            "highRisk": {"risk": 0.25, "return": 0.20},
        }

    @staticmethod
    def _calculate_consecutive_stats(trades: List[Trade]) -> tuple[int, int]:
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.side == "sell" and trade.total > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade.side == "sell" and trade.total < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    @staticmethod
    def _calculate_monthly_returns(trades: List[Trade]) -> Dict[str, float]:
        monthly_returns = {}

        for trade in trades:
            date = datetime.fromtimestamp(trade.timestamp / 1000)
            month_key = f"{date.year}-{date.month:02d}"

            if month_key not in monthly_returns:
                monthly_returns[month_key] = 0
            monthly_returns[month_key] += trade.total

        return monthly_returns

    @staticmethod
    def _calculate_trade_distribution(
        trades: List[Trade],
    ) -> Dict[str, Dict[str, float]]:
        time_of_day = {}
        day_of_week = {}

        for trade in trades:
            date = datetime.fromtimestamp(trade.timestamp / 1000)
            hour = str(date.hour)
            day = str(date.weekday())

            if hour not in time_of_day:
                time_of_day[hour] = 0
            time_of_day[hour] += 1

            if day not in day_of_week:
                day_of_week[day] = 0
            day_of_week[day] += 1

        return {"timeOfDay": time_of_day, "dayOfWeek": day_of_week}

    @staticmethod
    def _calculate_performance_by_pair(
        trades: List[Trade],
    ) -> Dict[str, Dict[str, Any]]:
        performance_by_pair = {}

        trades_by_pair = {}
        for trade in trades:
            if trade.pair not in trades_by_pair:
                trades_by_pair[trade.pair] = []
            trades_by_pair[trade.pair].append(trade)

        for pair, pair_trades in trades_by_pair.items():
            total_trades = len(pair_trades)
            winning_trades = len(
                [t for t in pair_trades if t.side == "sell" and t.total > 0]
            )
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            profits = [t.total for t in pair_trades if t.side == "sell" and t.total > 0]
            losses = [t.total for t in pair_trades if t.side == "sell" and t.total < 0]

            total_profit = sum(profits) + sum(losses)
            profit_percent = (
                total_profit / 10000
            ) * 100  # Assuming initial capital of 10000

            performance_by_pair[pair] = {
                "trades": total_trades,
                "winRate": win_rate,
                "profit": total_profit,
                "profitPercent": profit_percent,
            }

        return performance_by_pair
