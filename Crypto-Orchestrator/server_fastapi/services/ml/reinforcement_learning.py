"""
Reinforcement Learning Service - Q-learning and PPO agents for trading
"""

from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel
from datetime import datetime
import logging
from enum import Enum

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available; RL service will be limited.")

logger = logging.getLogger(__name__)

# Try importing RL libraries
try:
    import gymnasium as gym
    from stable_baselines3 import PPO, DQN
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import BaseCallback

    STABLE_BASELINES_AVAILABLE = True
except (ImportError, RuntimeError, Exception) as e:
    STABLE_BASELINES_AVAILABLE = False
    logger.warning(f"stable-baselines3 not available: {e}. PPO agent will be limited.")
    # Create dummy classes to prevent import errors
    PPO = None
    DQN = None
    make_vec_env = None
    BaseCallback = None


class Action(str, Enum):
    """Trading actions"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class RLConfig(BaseModel):
    """Reinforcement Learning configuration"""

    learning_rate: float = 0.0003
    gamma: float = 0.99  # Discount factor
    epsilon: float = 1.0  # Exploration rate
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    memory_size: int = 10000
    batch_size: int = 32
    update_frequency: int = 4
    target_update_frequency: int = 1000


class TradingState(BaseModel):
    """Trading state representation"""

    price: float
    volume: float
    technical_indicators: Dict[str, float]
    position: Optional[str] = None  # 'long', 'short', None
    balance: float = 10000.0
    portfolio_value: float = 10000.0


class QLearningAgent:
    """Q-learning agent for trading"""

    def __init__(self, config: Optional[RLConfig] = None):
        self.config = config or RLConfig()
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.epsilon = self.config.epsilon
        self.learning_rate = self.config.learning_rate
        self.gamma = self.config.gamma

        # Statistics
        self.training_episodes = 0
        self.total_reward = 0.0
        self.episode_rewards = []

        logger.info("Q-learning agent initialized")

    def _get_state_key(self, state: Dict[str, Any]) -> str:
        """Convert state to string key for Q-table"""
        # Discretize continuous values
        price_bin = int(state.get("price", 0) / 10)  # Bin price by $10
        volume_bin = int(state.get("volume", 0) / 1000)  # Bin volume by 1000
        rsi_bin = int(state.get("rsi", 50) / 10)  # Bin RSI by 10
        position = state.get("position", "none")

        return f"{price_bin}_{volume_bin}_{rsi_bin}_{position}"

    def get_action(self, state: Dict[str, Any], training: bool = True) -> str:
        """Get action from state using epsilon-greedy policy"""
        import random

        state_key = self._get_state_key(state)

        # Initialize Q-table entry if not exists
        if state_key not in self.q_table:
            self.q_table[state_key] = {
                Action.BUY.value: 0.0,
                Action.SELL.value: 0.0,
                Action.HOLD.value: 0.0,
            }

        # Epsilon-greedy exploration
        if training and random.random() < self.epsilon:
            action = random.choice(
                [Action.BUY.value, Action.SELL.value, Action.HOLD.value]
            )
        else:
            # Exploitation: choose best action
            q_values = self.q_table[state_key]
            action = max(q_values, key=q_values.get)

        return action

    def update_q_value(
        self,
        state: Dict[str, Any],
        action: str,
        reward: float,
        next_state: Dict[str, Any],
        done: bool = False,
    ) -> None:
        """Update Q-value using Q-learning algorithm"""
        state_key = self._get_state_key(state)
        next_state_key = self._get_state_key(next_state)

        # Initialize Q-table entries if not exist
        if state_key not in self.q_table:
            self.q_table[state_key] = {
                Action.BUY.value: 0.0,
                Action.SELL.value: 0.0,
                Action.HOLD.value: 0.0,
            }

        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {
                Action.BUY.value: 0.0,
                Action.SELL.value: 0.0,
                Action.HOLD.value: 0.0,
            }

        # Q-learning update
        current_q = self.q_table[state_key][action]

        if done:
            next_max_q = 0.0
        else:
            next_max_q = max(self.q_table[next_state_key].values())

        new_q = current_q + self.learning_rate * (
            reward + self.gamma * next_max_q - current_q
        )
        self.q_table[state_key][action] = new_q

        # Decay epsilon
        if self.epsilon > self.config.epsilon_min:
            self.epsilon *= self.config.epsilon_decay

    def calculate_reward(
        self,
        action: str,
        entry_price: float,
        exit_price: float,
        position: Optional[str],
        balance: float,
        portfolio_value: float,
    ) -> float:
        """Calculate reward for trading action"""
        if action == Action.HOLD.value:
            return 0.0

        if action == Action.BUY.value and position != "long":
            # Reward for buying (will be realized on sell)
            return 0.0

        if action == Action.SELL.value and position == "long":
            # Reward based on profit/loss
            pnl = (exit_price - entry_price) / entry_price
            return pnl * 100  # Scale reward

        return -0.1  # Small penalty for invalid actions

    def get_statistics(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            "training_episodes": self.training_episodes,
            "total_reward": self.total_reward,
            "epsilon": self.epsilon,
            "q_table_size": len(self.q_table),
            "average_reward": self.total_reward / max(self.training_episodes, 1),
        }


class PPOAgent:
    """Proximal Policy Optimization agent for trading"""

    def __init__(self, config: Optional[RLConfig] = None):
        self.config = config or RLConfig()
        self.model: Optional[Any] = None
        self.env = None

        if not STABLE_BASELINES_AVAILABLE:
            logger.warning(
                "PPO agent requires stable-baselines3, falling back to Q-learning"
            )

        logger.info("PPO agent initialized")

    def create_trading_env(self, market_data: List[Dict[str, Any]]) -> Any:
        """Create trading environment for PPO"""
        # This would create a custom Gymnasium environment
        # For now, return None as full implementation requires custom environment
        if not STABLE_BASELINES_AVAILABLE:
            return None

        logger.warning(
            "Custom trading environment not yet implemented, using Q-learning instead"
        )
        return None

    def train(
        self, env: Any, total_timesteps: int = 100000, log_interval: int = 10
    ) -> Dict[str, Any]:
        """Train PPO agent"""
        if not STABLE_BASELINES_AVAILABLE or env is None:
            logger.warning("PPO training requires stable-baselines3 and environment")
            return {"status": "error", "message": "PPO training not available"}

        try:
            # Create PPO model
            self.model = PPO(
                "MlpPolicy",
                env,
                learning_rate=self.config.learning_rate,
                gamma=self.config.gamma,
                verbose=1,
            )

            # Train model
            self.model.learn(total_timesteps=total_timesteps, log_interval=log_interval)

            return {
                "status": "success",
                "total_timesteps": total_timesteps,
                "message": "PPO training completed",
            }
        except Exception as e:
            logger.error(f"PPO training failed: {e}")
            return {"status": "error", "message": str(e)}

    def predict(self, observation: Any) -> Tuple[str, float]:
        """Predict action using trained PPO model"""
        if self.model is None:
            # Fallback to random action
            return Action.HOLD.value, 0.33

        try:
            # Convert observation to numpy array if needed
            if NUMPY_AVAILABLE:
                import numpy as np

                if not isinstance(observation, np.ndarray):
                    observation = np.array(observation)

            action, _states = self.model.predict(observation, deterministic=True)

            # Map action index to action string
            actions = [Action.BUY.value, Action.SELL.value, Action.HOLD.value]
            action_str = actions[int(action) % len(actions)]

            return action_str, 0.5
        except Exception as e:
            logger.error(f"PPO prediction failed: {e}")
            return Action.HOLD.value, 0.33

    def save_model(self, path: str) -> bool:
        """Save trained PPO model"""
        if self.model is None:
            return False

        try:
            self.model.save(path)
            return True
        except Exception as e:
            logger.error(f"Failed to save PPO model: {e}")
            return False

    def load_model(self, path: str) -> bool:
        """Load trained PPO model"""
        if not STABLE_BASELINES_AVAILABLE:
            return False

        try:
            self.model = PPO.load(path)
            return True
        except Exception as e:
            logger.error(f"Failed to load PPO model: {e}")
            return False


class RLService:
    """Service for managing reinforcement learning agents"""

    def __init__(self):
        self.q_learning_agent = QLearningAgent()
        self.ppo_agent = PPOAgent()
        logger.info("Reinforcement Learning service initialized")

    def get_q_learning_agent(self) -> QLearningAgent:
        """Get Q-learning agent"""
        return self.q_learning_agent

    def get_ppo_agent(self) -> PPOAgent:
        """Get PPO agent"""
        return self.ppo_agent

    def train_q_learning(
        self,
        episodes: int,
        market_data: List[Dict[str, Any]],
        initial_balance: float = 10000.0,
    ) -> Dict[str, Any]:
        """Train Q-learning agent on market data"""
        try:
            agent = self.q_learning_agent
            episode_rewards = []

            for episode in range(episodes):
                balance = initial_balance
                position = None
                entry_price = 0.0
                episode_reward = 0.0

                for i in range(len(market_data) - 1):
                    # Get current state
                    current_data = market_data[i]
                    state = {
                        "price": current_data.get("close", 0),
                        "volume": current_data.get("volume", 0),
                        "rsi": current_data.get("rsi", 50),
                        "position": position,
                    }

                    # Get action
                    action = agent.get_action(state, training=True)

                    # Execute action and get reward
                    next_data = market_data[i + 1]
                    next_price = next_data.get("close", 0)

                    reward = agent.calculate_reward(
                        action, entry_price, next_price, position, balance, balance
                    )

                    # Update position
                    if action == Action.BUY.value and position is None:
                        position = "long"
                        entry_price = current_data.get("close", 0)
                    elif action == Action.SELL.value and position == "long":
                        position = None
                        pnl = (next_price - entry_price) / entry_price
                        balance *= 1 + pnl

                    # Get next state
                    next_state = {
                        "price": next_price,
                        "volume": next_data.get("volume", 0),
                        "rsi": next_data.get("rsi", 50),
                        "position": position,
                    }

                    # Update Q-value
                    done = i == len(market_data) - 2
                    agent.update_q_value(state, action, reward, next_state, done)

                    episode_reward += reward

                episode_rewards.append(episode_reward)
                agent.total_reward += episode_reward
                agent.training_episodes += 1

            agent.episode_rewards = episode_rewards

            # Calculate average reward
            avg_reward = (
                sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
            )

            return {
                "status": "success",
                "episodes": episodes,
                "total_reward": agent.total_reward,
                "average_reward": avg_reward,
                "final_epsilon": agent.epsilon,
                "q_table_size": len(agent.q_table),
            }

        except Exception as e:
            logger.error(f"Q-learning training failed: {e}")
            return {"status": "error", "message": str(e)}


# Global service instance
rl_service = RLService()
