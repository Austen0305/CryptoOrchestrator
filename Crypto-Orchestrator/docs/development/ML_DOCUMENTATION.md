# Machine Learning Documentation

## Overview

CryptoOrchestrator provides comprehensive machine learning capabilities for trading, including deep learning models, reinforcement learning agents, sentiment analysis, and automated optimization. This document covers all ML features and their usage.

## ML Architecture

```
┌─────────────────────────────────────────┐
│         ML Pipeline                      │
├─────────────────────────────────────────┤
│  Data Loader → Feature Engineering       │
│       ↓                                   │
│  Windowing → Normalization               │
│       ↓                                   │
│  Model Training → Evaluation             │
│       ↓                                   │
│  Model Persistence → Deployment          │
└─────────────────────────────────────────┘
```

## ML Models

### Deep Learning Models

#### LSTM (Long Short-Term Memory)

**Use Case**: Time-series price prediction

**Features:**
- Handles long-term dependencies
- Captures temporal patterns
- Good for trend prediction

**Usage:**
```python
from server_fastapi.services.ml.lstm_engine import LSTMEngine

engine = LSTMEngine()
engine.train(X_train, y_train, X_val, y_val)
prediction = engine.predict(market_data)
```

**Configuration:**
```python
{
    "sequence_length": 60,
    "hidden_units": 128,
    "dropout": 0.2,
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100
}
```

#### GRU (Gated Recurrent Unit)

**Use Case**: Faster alternative to LSTM

**Features:**
- Similar to LSTM but simpler
- Faster training and inference
- Good for shorter sequences

**Usage:**
```python
from server_fastapi.services.ml.gru_engine import GRUEngine

engine = GRUEngine()
engine.train(X_train, y_train)
prediction = engine.predict(market_data)
```

#### Transformer

**Use Case**: Advanced pattern recognition

**Features:**
- Self-attention mechanism
- Parallel processing
- Excellent for complex patterns

**Usage:**
```python
from server_fastapi.services.ml.transformer_engine import TransformerEngine

engine = TransformerEngine()
engine.train(X_train, y_train)
prediction = engine.predict(market_data)
```

### Gradient Boosting

#### XGBoost

**Use Case**: Feature-based prediction

**Features:**
- Fast training and inference
- Handles non-linear relationships
- Good interpretability

**Usage:**
```python
from server_fastapi.services.ml.xgboost_engine import XGBoostEngine

engine = XGBoostEngine()
engine.train(X_train, y_train)
prediction = engine.predict(market_data)
```

**Configuration:**
```python
{
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8
}
```

## ML Pipeline

### Data Loading

```python
from server_fastapi.services.ml.ml_pipeline import MLPipeline

pipeline = MLPipeline()

# Load market data
market_data = pipeline.load_market_data(
    symbol="BTC/USD",
    timeframe="1h",
    limit=1000
)
```

### Feature Engineering

```python
# Extract features
features = pipeline.extract_features(market_data)

# Features include:
# - OHLCV data
# - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
# - Volume indicators
# - Price patterns
```

### Windowing

```python
# Create sequences for time-series models
X, y = pipeline.create_sequences(
    data=features,
    sequence_length=60,
    prediction_horizon=1
)
```

### Normalization

```python
# Normalize features
normalized = pipeline.normalize_features(
    features,
    method="minmax"  # or "standard"
)
```

### Training

```python
# Train model
result = engine.train(
    X_train=X_train,
    y_train=y_train,
    X_val=X_val,
    y_val=y_val
)

print(f"Training Loss: {result['train_loss']}")
print(f"Validation Loss: {result['val_loss']}")
print(f"Accuracy: {result['accuracy']}")
```

## AutoML

### Hyperparameter Optimization

```python
from server_fastapi.services.ml.automl_service import automl_service, SearchStrategy

config = OptimizationConfig(
    model_type="lstm",
    hyperparameter_ranges=[
        HyperparameterRange(
            name="learning_rate",
            param_type="float",
            min=0.0001,
            max=0.01
        ),
        HyperparameterRange(
            name="hidden_units",
            param_type="int",
            min=32,
            max=256
        )
    ],
    search_strategy=SearchStrategy.BAYESIAN,
    n_trials=100
)

def objective_function(params: Dict[str, Any]) -> float:
    # Train model with params and return score
    model = train_model(params)
    return evaluate_model(model)

result = automl_service.optimize_hyperparameters(config, objective_function)
print(f"Best Params: {result.best_params}")
print(f"Best Score: {result.best_score}")
```

### Search Strategies

- **Grid Search**: Exhaustive search of parameter space
- **Random Search**: Random sampling of parameters
- **Bayesian Optimization**: Intelligent parameter search (requires Optuna/scikit-optimize)

## Reinforcement Learning

### Q-Learning Agent

**Use Case**: Adaptive trading strategies

**Features:**
- Learns from experience
- Adapts to market conditions
- No labeled data required

**Usage:**
```python
from server_fastapi.services.ml.reinforcement_learning import QLearningAgent

agent = QLearningAgent()

# Train agent
for episode in range(1000):
    state = get_market_state()
    action = agent.get_action(state)
    reward = execute_action(action)
    agent.update(state, action, reward, next_state)

# Use trained agent
state = get_current_market_state()
action, confidence = agent.get_action(state)
```

### PPO (Proximal Policy Optimization)

**Use Case**: Advanced RL for trading

**Requirements**: `stable-baselines3`

**Usage:**
```python
from server_fastapi.services.ml.reinforcement_learning import PPOAgent

agent = PPOAgent()

# Create trading environment
env = agent.create_trading_env(market_data)

# Train agent
result = agent.train(env, total_timesteps=100000)

# Use trained agent
observation = get_market_observation()
action, confidence = agent.predict(observation)
```

## Sentiment Analysis

### Text Sentiment

```python
from server_fastapi.services.ml.sentiment_ai import sentiment_ai_service

# Analyze single text
score = sentiment_ai_service.analyze_text(
    "Bitcoin is going to the moon! 🚀"
)
print(f"Sentiment: {score.compound:.2f}")  # -1 to 1

# Analyze news articles
articles = [
    NewsArticle(title="...", content="..."),
    NewsArticle(title="...", content="...")
]
news_sentiment = sentiment_ai_service.analyze_news(articles)

# Analyze social media
posts = [
    SocialMediaPost(text="...", engagement=1000),
    SocialMediaPost(text="...", engagement=500)
]
social_sentiment = sentiment_ai_service.analyze_social_media(posts)

# Get aggregated sentiment
aggregated = sentiment_ai_service.aggregate_sentiment(
    news_sentiment,
    social_sentiment
)
```

### Sentiment Sources

- **VADER**: Rule-based sentiment analyzer
- **TextBlob**: Text processing and sentiment
- **Transformers (DistilBERT)**: Deep learning sentiment (requires transformers)

## Market Regime Detection

### Regime Types

- **Bullish**: Strong uptrend
- **Bearish**: Strong downtrend
- **Ranging**: Sideways movement
- **Volatile**: High volatility, unpredictable
- **Trending**: Clear directional movement

### Usage

```python
from server_fastapi.services.ml.market_regime import market_regime_service

# Detect current regime
regime = market_regime_service.detect_regime(
    prices=[50000, 50100, 50200, ...],
    volumes=[1000, 1100, 1200, ...]
)

print(f"Regime: {regime.regime.value}")
print(f"Trend Strength: {regime.metrics.trend_strength:.2f}")
print(f"Volatility: {regime.metrics.volatility:.2f}")
```

### Regime Metrics

```python
class RegimeMetrics:
    regime: MarketRegime
    trend_strength: float  # 0 to 1
    volatility: float  # 0 to 1
    volume_trend: float  # -1 to 1
    rsi: float
    macd_signal: float
    timestamp: datetime
```

## Model Persistence

### Saving Models

```python
from server_fastapi.services.ml.model_persistence import save_model

metadata = {
    "model_type": "lstm",
    "version": "1.0.0",
    "performance": {
        "accuracy": 0.75,
        "sharpe_ratio": 1.5
    },
    "config": model_config
}

save_model(
    model=model,
    metadata=metadata,
    path="models/my_lstm_model"
)
```

### Loading Models

```python
from server_fastapi.services.ml.model_persistence import load_model

model, metadata = load_model("models/my_lstm_model")
print(f"Model Type: {metadata.model_type}")
print(f"Accuracy: {metadata.performance['accuracy']}")
```

## Model Evaluation

### Classification Metrics

```python
from server_fastapi.services.ml.model_evaluation import evaluate_classification

metrics = evaluate_classification(
    y_true=actual_labels,
    y_pred=predicted_labels
)

print(f"Accuracy: {metrics['accuracy']:.2f}")
print(f"Precision: {metrics['precision']:.2f}")
print(f"Recall: {metrics['recall']:.2f}")
print(f"F1-Score: {metrics['f1_score']:.2f}")
```

### Regression Metrics

```python
from server_fastapi.services.ml.model_evaluation import evaluate_regression

metrics = evaluate_regression(
    y_true=actual_prices,
    y_pred=predicted_prices
)

print(f"MSE: {metrics['mse']:.2f}")
print(f"RMSE: {metrics['rmse']:.2f}")
print(f"R2 Score: {metrics['r2_score']:.2f}")
```

## ML V2 Features

### AutoML API

```python
POST /api/ml-v2/optimize
{
    "model_type": "lstm",
    "hyperparameter_ranges": [...],
    "search_strategy": "bayesian",
    "n_trials": 100
}
```

### Reinforcement Learning API

```python
POST /api/ml-v2/rl/train
{
    "agent_type": "ppo",
    "market_data": [...],
    "total_timesteps": 100000
}
```

### Sentiment Analysis API

```python
POST /api/ml-v2/sentiment/analyze
{
    "text": "Bitcoin is going to the moon!",
    "sources": ["vader", "textblob", "transformer"]
}
```

### Market Regime API

```python
POST /api/ml-v2/regime/detect
{
    "prices": [50000, 50100, ...],
    "volumes": [1000, 1100, ...]
}
```

## Best Practices

1. **Data Quality**: Clean and validate input data
2. **Feature Engineering**: Create meaningful features
3. **Train/Val/Test Split**: Use proper data splits
4. **Cross-Validation**: Validate model performance
5. **Overfitting Prevention**: Use regularization and early stopping
6. **Model Selection**: Compare multiple models
7. **Hyperparameter Tuning**: Optimize model parameters
8. **Ensemble Methods**: Combine multiple models
9. **Backtesting**: Test on historical data
10. **Production Monitoring**: Monitor model performance in production

## Performance Optimization

### GPU Acceleration

Set environment variable to enable GPU:
```bash
CUDA_VISIBLE_DEVICES=0 python train_model.py
```

### Model Quantization

Reduce model size for faster inference:
```python
# Quantize model (for TensorFlow)
converter = tf.lite.TFLiteConverter.from_saved_model(model_path)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()
```

### Batch Processing

Process multiple predictions in batches:
```python
predictions = model.predict_batch(market_data_batch)
```

## Troubleshooting

### Common Issues

1. **Low Accuracy**: Increase model complexity, add features, tune hyperparameters
2. **Overfitting**: Add regularization, reduce model complexity, use more data
3. **Slow Training**: Use GPU, reduce batch size, optimize data pipeline
4. **Memory Issues**: Reduce batch size, use data generators, optimize model size

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See `/examples/ml` for complete ML examples:

- `train_lstm.py` - Train LSTM model
- `backtest_ml_strategy.py` - Backtest ML strategy
- `sentiment_analysis.py` - Analyze market sentiment
- `regime_detection.py` - Detect market regimes
- `automl_optimization.py` - Hyperparameter optimization

## Support

- **Documentation**: Full API docs at `/docs`
- **Examples**: See `/examples/ml` directory
- **Community**: Join Discord for ML discussions
- **Support**: Email ml-support@cryptoorchestrator.com

