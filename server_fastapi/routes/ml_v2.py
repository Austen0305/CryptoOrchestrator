"""
ML V2 Routes - AutoML, Reinforcement Learning, Sentiment AI, Market Regime Detection
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..services.ml.automl_service import (
    HyperparameterRange,
    OptimizationConfig,
    SearchStrategy,
    automl_service,
)
from ..services.ml.market_regime import (
    MarketRegime,
    market_regime_service,
)
from ..services.ml.reinforcement_learning import rl_service
from ..services.ml.sentiment_ai import (
    NewsArticle,
    SocialMediaPost,
    sentiment_ai_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml-v2", tags=["ML V2"])


# ===== AutoML Routes =====


class HyperparameterRangeRequest(BaseModel):
    """Hyperparameter range request"""

    name: str
    param_type: str
    min: float | None = None
    max: float | None = None
    step: float | None = None
    values: list[Any] | None = None


class OptimizationRequest(BaseModel):
    """Optimization request"""

    model_config = {"protected_namespaces": ()}

    model_type: str
    hyperparameter_ranges: dict[str, HyperparameterRangeRequest]
    search_strategy: str = "bayesian"
    n_trials: int = 100
    n_jobs: int = 1
    timeout: int | None = None
    metric: str = "accuracy"
    direction: str = "maximize"


@router.post("/automl/optimize", response_model=dict)
async def optimize_hyperparameters(
    request: OptimizationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Optimize hyperparameters using AutoML"""
    try:
        # Convert request to config
        hyperparameter_ranges = {}
        for name, param_request in request.hyperparameter_ranges.items():
            hyperparameter_ranges[name] = HyperparameterRange(
                name=param_request.name,
                param_type=param_request.param_type,
                min=param_request.min,
                max=param_request.max,
                step=param_request.step,
                values=param_request.values,
            )

        config = OptimizationConfig(
            model_type=request.model_type,
            hyperparameter_ranges=hyperparameter_ranges,
            search_strategy=SearchStrategy(request.search_strategy),
            n_trials=request.n_trials,
            n_jobs=request.n_jobs,
            timeout=request.timeout,
            metric=request.metric,
            direction=request.direction,
        )

        # Define objective function (placeholder - should use actual model evaluation)
        def objective_function(params: dict[str, Any]) -> float:
            # This should evaluate model with given parameters
            # For now, return mock score
            return 0.75

        result = automl_service.optimize_hyperparameters(config, objective_function)

        return {
            "status": "success",
            "best_params": result.best_params,
            "best_score": result.best_score,
            "n_trials": result.n_trials,
            "optimization_time": result.optimization_time,
        }

    except Exception as e:
        logger.error(f"AutoML optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# ===== Reinforcement Learning Routes =====


class RLTrainingRequest(BaseModel):
    """RL training request"""

    agent_type: str = "q_learning"  # 'q_learning' or 'ppo'
    episodes: int = 100
    market_data: list[dict[str, Any]]
    initial_balance: float = 10000.0
    config: dict[str, Any] | None = None


@router.post("/rl/train", response_model=dict)
async def train_rl_agent(
    request: RLTrainingRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Train reinforcement learning agent"""
    try:
        if request.agent_type == "q_learning":
            result = rl_service.train_q_learning(
                episodes=request.episodes,
                market_data=request.market_data,
                initial_balance=request.initial_balance,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown agent type: {request.agent_type}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RL training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/rl/q-learning/stats", response_model=dict)
async def get_q_learning_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get Q-learning agent statistics"""
    try:
        agent = rl_service.get_q_learning_agent()
        stats = agent.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get Q-learning stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# ===== Sentiment AI Routes =====


class TextAnalysisRequest(BaseModel):
    """Text analysis request"""

    text: str
    method: str = "vader"  # 'vader', 'textblob', 'transformer'


@router.post("/sentiment/analyze", response_model=dict)
async def analyze_sentiment(
    request: TextAnalysisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Analyze sentiment of text"""
    try:
        sentiment = sentiment_ai_service.analyze_text(request.text, request.method)
        return sentiment.dict()
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


class AggregateSentimentRequest(BaseModel):
    """Aggregate sentiment request"""

    symbol: str
    news_articles: list[dict[str, Any]] = []
    social_posts: list[dict[str, Any]] = []
    method: str = "vader"


@router.post("/sentiment/aggregate", response_model=dict)
async def aggregate_sentiment(
    request: AggregateSentimentRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Aggregate sentiment from multiple sources"""
    try:
        # Convert dicts to models
        news_articles = [NewsArticle(**article) for article in request.news_articles]
        social_posts = [SocialMediaPost(**post) for post in request.social_posts]

        aggregated = sentiment_ai_service.aggregate_sentiment(
            symbol=request.symbol,
            news_articles=news_articles,
            social_posts=social_posts,
            method=request.method,
        )

        return aggregated.dict()
    except Exception as e:
        logger.error(f"Sentiment aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")


# ===== Market Regime Detection Routes =====


class RegimeDetectionRequest(BaseModel):
    """Regime detection request"""

    prices: list[float]
    volumes: list[float] | None = None
    lookback_period: int = 20


@router.post("/regime/detect", response_model=dict)
async def detect_market_regime(
    request: RegimeDetectionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Detect market regime"""
    try:
        regime = market_regime_service.detect_regime(
            prices=request.prices,
            volumes=request.volumes or [],
            lookback_period=request.lookback_period,
        )

        return regime.dict()
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/regime/strategy/{regime}", response_model=dict)
async def get_regime_strategy(
    regime: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    base_strategy: str = "default",
):
    """Get regime-aware strategy recommendations"""
    try:
        market_regime = MarketRegime(regime)
        strategy = market_regime_service.get_regime_aware_strategy(
            regime=market_regime, base_strategy=base_strategy
        )
        return strategy
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid regime: {regime}")
    except Exception as e:
        logger.error(f"Failed to get regime strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to get strategy")
