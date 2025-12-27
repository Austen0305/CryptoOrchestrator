"""
ML Services Module - Machine Learning engines and utilities
"""

from .lstm_engine import LSTMEngine, LSTMConfig
from .gru_engine import GRUEngine, GRUConfig
from .transformer_engine import TransformerEngine, TransformerConfig
from .xgboost_engine import XGBoostEngine, XGBoostConfig
from .ml_pipeline import MLPipeline, PipelineConfig
from .model_persistence import ModelPersistence, ModelMetadata
from .model_evaluation import ModelEvaluation, ClassificationMetrics, RegressionMetrics
from .enhanced_ml_engine import EnhancedMLEngine
from .neural_network_engine import NeuralNetworkEngine
from .ensemble_engine import EnsembleEngine
from .automl_service import (
    AutoMLService,
    OptimizationConfig,
    OptimizationResult,
    HyperparameterRange,
    SearchStrategy,
    automl_service,
)

try:
    from .reinforcement_learning import (
        RLService,
        QLearningAgent,
        PPOAgent,
        RLConfig,
        Action,
        TradingState,
        rl_service,
    )
except (ImportError, RuntimeError, Exception) as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        f"Failed to import reinforcement_learning: {e}. RL features will be disabled."
    )
    # Create dummy classes to prevent import errors
    RLService = None
    QLearningAgent = None
    PPOAgent = None
    RLConfig = None
    Action = None
    TradingState = None
    rl_service = None

try:
    from .sentiment_ai import (
        SentimentAIService,
        SentimentScore,
        NewsArticle,
        SocialMediaPost,
        AggregatedSentiment,
        sentiment_ai_service,
    )
except (ImportError, RuntimeError, Exception) as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        f"Failed to import sentiment_ai: {e}. Sentiment analysis features will be disabled."
    )
    # Create dummy classes to prevent import errors
    SentimentAIService = None
    SentimentScore = None
    NewsArticle = None
    SocialMediaPost = None
    AggregatedSentiment = None
    sentiment_ai_service = None

from .market_regime import (
    MarketRegimeService,
    MarketRegime,
    RegimeMetrics,
    market_regime_service,
)

__all__ = [
    # Phase 4 - ML V1
    "LSTMEngine",
    "LSTMConfig",
    "GRUEngine",
    "GRUConfig",
    "TransformerEngine",
    "TransformerConfig",
    "XGBoostEngine",
    "XGBoostConfig",
    "MLPipeline",
    "PipelineConfig",
    "ModelPersistence",
    "ModelMetadata",
    "ModelEvaluation",
    "ClassificationMetrics",
    "RegressionMetrics",
    "EnhancedMLEngine",
    "NeuralNetworkEngine",
    "EnsembleEngine",
    # Phase 6 - ML V2
    "AutoMLService",
    "OptimizationConfig",
    "OptimizationResult",
    "HyperparameterRange",
    "SearchStrategy",
    "automl_service",
    "RLService",
    "QLearningAgent",
    "PPOAgent",
    "RLConfig",
    "Action",
    "TradingState",
    "rl_service",
    "SentimentAIService",
    "SentimentScore",
    "NewsArticle",
    "SocialMediaPost",
    "AggregatedSentiment",
    "sentiment_ai_service",
    "MarketRegimeService",
    "MarketRegime",
    "RegimeMetrics",
    "market_regime_service",
]
