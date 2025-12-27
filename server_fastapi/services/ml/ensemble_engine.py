from typing import Dict, Any, List, Optional, Tuple
import asyncio
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EnsemblePrediction(BaseModel):
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    votes: Dict[str, Dict[str, Any]]  # qLearning and neuralNetwork votes


class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class EnsembleEngine:
    def __init__(self):
        self.q_learning_engine = None
        self.neural_network_engine = None
        self.q_table: Dict[str, Dict[str, float]] = {}

        # Import the engines dynamically to avoid circular imports
        try:
            from .ml_service import MLModel  # Q-learning engine
            from .neural_network_engine import NeuralNetworkEngine

            self.q_learning_engine = MLModel()
            self.neural_network_engine = NeuralNetworkEngine()
        except ImportError as e:
            logger.warning(f"Could not import ML engines: {e}")

    async def initialize(self, bot_id: str) -> None:
        """Initialize the neural network model for the bot"""
        if self.neural_network_engine:
            # Assuming the neural network engine has a load method
            try:
                await self.neural_network_engine.load_model(bot_id)
                logger.info(f"Neural network model initialized for bot {bot_id}")
            except AttributeError:
                logger.warning("Neural network engine does not have load_model method")

    def set_q_table(self, q_table: Dict[str, Dict[str, float]]) -> None:
        """Set the Q-table for Q-learning predictions"""
        self.q_table = q_table

    async def train(self, market_data: List[MarketData]) -> None:
        """Train the neural network model"""
        if self.neural_network_engine:
            try:
                await self.neural_network_engine.train(market_data)
                logger.info("Neural network training completed")
            except Exception as error:
                logger.error(f"Neural network training failed: {error}")
        else:
            logger.warning("Neural network engine not available for training")

    def _calculate_q_learning_confidence_from_state_key(self, state_key: str) -> float:
        """Calculate confidence from Q-table values for a given state"""
        q_values = self.q_table.get(state_key, {"buy": 0.0, "sell": 0.0, "hold": 0.0})
        vals = list(q_values.values())
        if not vals:
            return 0.0
        max_q = max(vals)
        min_q = min(vals)
        return (max_q - min_q) / (abs(max_q) + 1) if (max_q - min_q) != 0 else 0.0

    async def predict(self, market_data: List[MarketData]) -> EnsemblePrediction:
        """Generate ensemble prediction from both models"""

        # Get predictions from both engines
        q_learning_prediction = await self._get_q_learning_prediction(market_data)
        nn_prediction = await self._get_neural_network_prediction(market_data)

        # Calculate Q-learning confidence from qTable using current state
        state = self._derive_state(market_data)
        state_key = self._get_state_key(state)
        q_learning_confidence = self._calculate_q_learning_confidence_from_state_key(
            state_key
        )

        # Get weights based on recent accuracy
        q_learning_weight = self._get_q_learning_accuracy()
        nn_weight = self._get_neural_network_accuracy()
        total_weight = q_learning_weight + nn_weight or 1.0

        # Calculate weighted votes
        votes: Dict[str, float] = {"buy": 0.0, "sell": 0.0, "hold": 0.0}

        votes[q_learning_prediction["action"]] += (
            q_learning_weight / total_weight
        ) * q_learning_confidence
        votes[nn_prediction["action"]] += (nn_weight / total_weight) * nn_prediction[
            "confidence"
        ]

        # Determine final action
        max_action = max(votes, key=votes.get)
        max_score = votes[max_action]

        return EnsemblePrediction(
            action=max_action,
            confidence=max_score,
            votes={
                "qLearning": {
                    "action": q_learning_prediction["action"],
                    "confidence": q_learning_confidence,
                },
                "neuralNetwork": nn_prediction,
            },
        )

    async def _get_q_learning_prediction(
        self, market_data: List[MarketData]
    ) -> Dict[str, Any]:
        """Get prediction from Q-learning engine"""
        if self.q_learning_engine:
            try:
                # Assuming the MLModel has a predict method
                result = self.q_learning_engine.predict(market_data)
                return {"action": result.get("prediction", "hold"), "confidence": 0.5}
            except Exception as e:
                logger.error(f"Q-learning prediction error: {e}")
                return {"action": "hold", "confidence": 0.0}
        return {"action": "hold", "confidence": 0.0}

    async def _get_neural_network_prediction(
        self, market_data: List[MarketData]
    ) -> Dict[str, Any]:
        """Get prediction from neural network engine"""
        if self.neural_network_engine:
            try:
                result = self.neural_network_engine.predict(market_data)
                return result
            except Exception as e:
                logger.error(f"Neural network prediction error: {e}")
                return {"action": "hold", "confidence": 0.0}
        return {"action": "hold", "confidence": 0.0}

    def _get_q_learning_accuracy(self) -> float:
        """Get recent accuracy of Q-learning engine"""
        if self.q_learning_engine and hasattr(self.q_learning_engine, "get_accuracy"):
            try:
                return self.q_learning_engine.get_accuracy()
            except:
                pass
        return 0.5  # Default neutral weight

    def _get_neural_network_accuracy(self) -> float:
        """Get recent accuracy of neural network engine"""
        if self.neural_network_engine and hasattr(
            self.neural_network_engine, "get_recent_accuracy"
        ):
            try:
                return self.neural_network_engine.get_recent_accuracy()
            except:
                pass
        return 0.5  # Default neutral weight

    def update_q_value(
        self,
        state: Dict[str, Any],
        action: str,
        reward: float,
        next_state: Dict[str, Any],
    ) -> None:
        """Update Q-value in the Q-table"""
        state_key = self._get_state_key(state)
        next_state_key = self._get_state_key(next_state)

        if state_key not in self.q_table:
            self.q_table[state_key] = {"buy": 0.0, "sell": 0.0, "hold": 0.0}

        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {"buy": 0.0, "sell": 0.0, "hold": 0.0}

        # Q-learning update
        learning_rate = 0.1
        discount_factor = 0.95

        old_value = self.q_table[state_key][action]
        next_max = max(self.q_table[next_state_key].values())
        new_value = old_value + learning_rate * (
            reward + discount_factor * next_max - old_value
        )
        self.q_table[state_key][action] = new_value

    def calculate_reward(
        self,
        action: str,
        entry_price: float,
        exit_price: float,
        position: Optional[str],
    ) -> float:
        """Calculate reward based on trading action and outcome"""
        if position == "long":
            if action == "sell":
                # Reward for selling when position is profitable
                return (exit_price - entry_price) / entry_price
            elif action == "hold":
                return 0.0  # Neutral for holding
            else:
                return -0.1  # Penalty for wrong action
        elif position == "short":
            if action == "buy":
                # Reward for buying back when position is profitable
                return (entry_price - exit_price) / entry_price
            elif action == "hold":
                return 0.0
            else:
                return -0.1
        else:
            # No position
            if action == "buy" or action == "sell":
                return -0.05  # Small penalty for opening positions
            return 0.0

    def _derive_state(
        self, market_data: List[MarketData], current_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Derive state from market data"""
        if not market_data:
            return {
                "price_direction": "stable",
                "rsi": "neutral",
                "volume": "medium",
                "volatility": "medium",
                "trend": "neutral",
            }

        index = current_index if current_index is not None else len(market_data) - 1
        if index < 0 or index >= len(market_data):
            index = len(market_data) - 1

        current = market_data[index]
        prev = market_data[index - 1] if index > 0 else current

        # Price direction
        price_change = (current.close - prev.close) / prev.close
        if price_change > 0.005:
            price_direction = "up"
        elif price_change < -0.005:
            price_direction = "down"
        else:
            price_direction = "stable"

        # RSI (simplified)
        if len(market_data) >= 14:
            rsi = self._calculate_rsi(market_data, index)
            if rsi < 30:
                rsi_state = "oversold"
            elif rsi > 70:
                rsi_state = "overbought"
            else:
                rsi_state = "neutral"
        else:
            rsi_state = "neutral"

        # Volume (relative to recent average)
        avg_volume = sum(
            d.volume for d in market_data[max(0, index - 20) : index + 1]
        ) / min(20, index + 1)
        volume_ratio = current.volume / avg_volume if avg_volume > 0 else 1.0
        if volume_ratio > 1.5:
            volume_state = "high"
        elif volume_ratio < 0.5:
            volume_state = "low"
        else:
            volume_state = "medium"

        # Volatility (simplified)
        if len(market_data) >= 20:
            returns = [
                (d.close - market_data[max(0, i - 1)].close)
                / market_data[max(0, i - 1)].close
                for i, d in enumerate(market_data[max(0, index - 19) : index + 1])
                if i > 0
            ]
            volatility = sum(abs(r) for r in returns) / len(returns) if returns else 0.0
            if volatility > 0.02:
                volatility_state = "high"
            elif volatility < 0.005:
                volatility_state = "low"
            else:
                volatility_state = "medium"
        else:
            volatility_state = "medium"

        # Trend (simplified moving average)
        if len(market_data) >= 20:
            sma_short = sum(
                d.close for d in market_data[max(0, index - 9) : index + 1]
            ) / min(10, index + 1)
            sma_long = sum(
                d.close for d in market_data[max(0, index - 19) : index + 1]
            ) / min(20, index + 1)
            if sma_short > sma_long * 1.005:
                trend = "bullish"
            elif sma_short < sma_long * 0.995:
                trend = "bearish"
            else:
                trend = "neutral"
        else:
            trend = "neutral"

        return {
            "price_direction": price_direction,
            "rsi": rsi_state,
            "volume": volume_state,
            "volatility": volatility_state,
            "trend": trend,
        }

    def _get_state_key(self, state: Dict[str, Any]) -> str:
        """Convert state to a string key for Q-table"""
        return f"{state['price_direction']}_{state['rsi']}_{state['volume']}_{state['volatility']}_{state['trend']}"

    def _calculate_rsi(
        self, data: List[MarketData], index: int, period: int = 14
    ) -> float:
        """Calculate RSI for the given index"""
        if index < period:
            return 50.0

        gains = 0.0
        losses = 0.0

        for i in range(index - period + 1, index + 1):
            change = data[i].close - data[i - 1].close
            if change > 0:
                gains += change
            else:
                losses += abs(change)

        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    async def save_model(self, bot_id: str) -> None:
        """Save the neural network model"""
        if self.neural_network_engine:
            try:
                await self.neural_network_engine.save_model(bot_id)
                logger.info(f"Neural network model saved for bot {bot_id}")
            except Exception as error:
                logger.error(f"Failed to save neural network model: {error}")

    def dispose(self) -> None:
        """Clean up resources"""
        if self.neural_network_engine and hasattr(
            self.neural_network_engine, "dispose"
        ):
            try:
                self.neural_network_engine.dispose()
            except:
                pass


# Global instance
ensemble_engine = EnsembleEngine()
