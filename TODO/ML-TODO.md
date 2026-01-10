
# ML / Strategy Engine TODOs

## Phase 3: Infrastructure & Baseline
- [ ] **Smart Bot Engine Refactor**
  - [ ] Audit `smart_bot_engine.py` for hardcoded thresholds.
  - [ ] Extract feature engineering into dedicated pipeline (`features.py`).
- [ ] **Infrastructure & MLOps**
  - [ ] **Dependency Stability**: Remove "TensorFlow hacking" in setup scripts; standardise on PyTorch 2.5+ (2026 standard) for all agents.
  - [ ] **Model Registry**:
    - [ ] Create `ModelRegistry` service to load models by version (e.g., `v1.0.0_TFT`).
    - [ ] **Removal**: Delete hardcoded `ml_model.pkl` loading in `MLService`.
  - [ ] **Data Pipeline**:
    - [ ] **Ingestion**: Implement `CCXT` based historical fetcher (replaces mocked data).
    - [ ] **Feature Store**: Redis for real-time features (Volume Profile, Volatility).
    - [ ] **Validator**: Strict schema validation for all inputs (reject NaNs).

## Phase 4: Model Development (State of the Art)
- [ ] **Advanced Forecasting**
  - [ ] **Architecture**: Implement **Temporal Fusion Transformer (TFT)** using `pytorch-forecasting`.
    - [ ] **Why**: Inherently interpretable (attention weights), handles static covariates (coin metadata) + time-varying inputs (price, volume).
    - [ ] **Inputs**: OHLCV, Order Book Depth (Bid/Ask spread), Global Macro (DXY/SPX correlation).
  - [ ] **Training**: Set up GPU-based training pipeline using PyTorch Lightning.
- [ ] **Validation Guardrails**
  - [ ] **Backtesting**: Validate model vs "Buy & Hold" and "Simple Grid" on 2022-2025 data (Bear & Bull markets).
  - [ ] **Confidence Thresholds**: Reject signals where model attention weights are diffuse/uncertain.

## Phase 5: Advanced capabilities
- [ ] **Reinforcement Learning (RL)**
  - [ ] **Execution Agent**: Train PPO agent (Stable Baselines3) to optimize *execution* slippage, NOT direction.
    - [ ] Reward: Implementation Shortfall (Slippage vs Arrival Price).
    - [ ] **Safety Constraint**: RL Agent must output *suggested* parameters, which must pass strictly validated `RiskManager` checks before execution.
  - [ ] **Model Fairness**:
    - [ ] **Bias Check**: Ensure model recall is consistent across different asset classes (e.g., don't overfit to Memecoins).
- [ ] **Sentiment Analysis**
  - [ ] Connect to `LunarCrush` or Twitter API v2.
  - [ ] Use FinBERT for sentiment classification of headlines.
