# Smart Bot Quick Start Guide

## Overview

Get your intelligent trading bot running in 5 minutes with the new **Smart Adaptive Strategy** - featuring multi-indicator analysis, risk management, and adaptive parameter optimization.

## Quick Setup

### 1. Start the Backend

```bash
npm run dev:fastapi
```

### 2. Create a Smart Bot

```bash
POST http://localhost:8000/api/bots
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "name": "BTC Smart Trader",
  "symbol": "BTC/USDT",
  "strategy": "smart_adaptive",
  "config": {
    "account_balance": 10000,
    "risk_per_trade": 0.02,
    "confidence_threshold": 0.65,
    "use_smart_engine": true
  }
}
```

**Response:**

```json
{
  "id": "bot-user1-abc123",
  "name": "BTC Smart Trader",
  "symbol": "BTC/USDT",
  "strategy": "smart_adaptive",
  "is_active": false,
  "config": { ... },
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 3. Start Trading

```bash
POST http://localhost:8000/api/bots/{bot_id}/start
Authorization: Bearer YOUR_JWT_TOKEN
```

### 4. Monitor Intelligence

#### Get Real-Time Analysis

```bash
GET http://localhost:8000/api/bots/{bot_id}/analysis
```

**Response:**

```json
{
  "bot_id": "bot-user1-abc123",
  "symbol": "BTC/USDT",
  "analysis": {
    "action": "buy",
    "confidence": 0.78,
    "strength": 0.65,
    "risk_score": 0.35,
    "reasoning": [
      "Strong bullish EMA alignment (9 > 21 > 50)",
      "RSI oversold at 28.5, potential reversal",
      "MACD bullish crossover with strong histogram",
      "Volume spike confirms momentum (1.8x average)"
    ],
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "market_condition": "bull"
}
```

#### Check Risk Metrics

```bash
GET http://localhost:8000/api/bots/{bot_id}/risk-metrics
```

**Response:**

```json
{
  "risk_metrics": {
    "overall_risk_score": 0.42,
    "volatility": 0.35,
    "sharpe_ratio": 1.85,
    "max_drawdown": -0.08,
    "current_confidence": 0.78,
    "market_regime": "bull"
  },
  "recommendations": {
    "suggested_position_size": "moderate",
    "stop_loss_adjustment": "normal",
    "warnings": []
  }
}
```

#### Optimize Parameters

```bash
POST http://localhost:8000/api/bots/{bot_id}/optimize
```

**Response:**

```json
{
  "optimized_parameters": {
    "market_regime": "bull",
    "confidence_threshold": 0.65,
    "position_multiplier": 1.2,
    "risk_per_trade": 0.015,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.05,
    "trailing_stop_enabled": true,
    "adaptive_reasoning": [
      "Bull market detected: increased position sizing by 20%",
      "Low volatility environment: tighter stops for better risk/reward",
      "Strong trend present: enabled trailing stops to capture momentum"
    ]
  }
}
```

## Key Features

### 🧠 9 Technical Indicators

- **Trend**: EMA crossovers (9/21/50)
- **Momentum**: RSI, MACD, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Volume**: OBV, volume spikes
- **Levels**: Support/resistance detection

### ⚡ Smart Signal Synthesis

- Weighted indicator combination (Trend 30%, Momentum 40%, Volatility 30%)
- Human-readable reasoning for every decision
- Confidence scoring (0-1 scale)

### 🛡️ Advanced Risk Management

- Volatility-based risk scoring
- Liquidity analysis (bid-ask spreads)
- Drawdown monitoring
- Dynamic position sizing (max 2% risk per trade)

### 🔄 Adaptive Intelligence

- Market regime detection (bull/bear/sideways/volatile)
- Dynamic confidence thresholds
- Automatic parameter optimization
- Position multiplier adjustments

## Configuration Examples

### Conservative Bot (Low Risk)

```json
{
  "name": "BTC Conservative",
  "symbol": "BTC/USDT",
  "strategy": "smart_adaptive",
  "config": {
    "account_balance": 10000,
    "risk_per_trade": 0.01,
    "confidence_threshold": 0.75,
    "use_smart_engine": true
  }
}
```

- **Risk per trade**: 1%
- **Confidence threshold**: 75% (only high-confidence signals)
- **Best for**: Stable, long-term growth

### Moderate Bot (Balanced)

```json
{
  "name": "ETH Moderate",
  "symbol": "ETH/USDT",
  "strategy": "smart_adaptive",
  "config": {
    "account_balance": 10000,
    "risk_per_trade": 0.02,
    "confidence_threshold": 0.65,
    "use_smart_engine": true
  }
}
```

- **Risk per trade**: 2%
- **Confidence threshold**: 65% (moderate signals)
- **Best for**: Balanced risk/reward

### Aggressive Bot (High Risk/Reward)

```json
{
  "name": "SOL Aggressive",
  "symbol": "SOL/USDT",
  "strategy": "smart_adaptive",
  "config": {
    "account_balance": 10000,
    "risk_per_trade": 0.03,
    "confidence_threshold": 0.55,
    "use_smart_engine": true
  }
}
```

- **Risk per trade**: 3%
- **Confidence threshold**: 55% (more frequent trades)
- **Best for**: Active trading, higher volatility tolerance

## Understanding Signals

### Confidence Levels

| Confidence | Interpretation | Action |
|------------|---------------|--------|
| 0.75 - 1.0 | Strong signal | Full position size |
| 0.65 - 0.75 | Moderate signal | Standard position size |
| 0.55 - 0.65 | Weak signal | Reduced position size |
| < 0.55 | No confidence | Hold, no trade |

### Risk Score Interpretation

| Risk Score | Market Condition | Position Adjustment |
|-----------|------------------|---------------------|
| 0.0 - 0.3 | Low risk | Normal to aggressive sizing |
| 0.3 - 0.5 | Moderate risk | Standard sizing |
| 0.5 - 0.7 | Elevated risk | Conservative sizing (70%) |
| 0.7 - 1.0 | High risk | Very conservative (50%) or hold |

### Market Regimes

- **Bull**: Strong uptrend → Increase positions, use trailing stops
- **Bear**: Strong downtrend → Reduce positions, tight stops
- **Sideways**: Range-bound → Mean reversion, wider stops
- **Volatile**: High ATR → Smaller positions, higher confidence threshold

## Monitoring Dashboard

### Key Metrics to Watch

1. **Confidence Trend**: Are signals getting stronger or weaker?
2. **Risk Score**: Is market volatility increasing?
3. **Win Rate**: Track via `/api/bots/{bot_id}/performance`
4. **Market Regime**: Has it changed recently?
5. **Reasoning Patterns**: What indicators are driving decisions?

### Alert Conditions

- ⚠️ Risk score > 0.7: Consider pausing trading
- ⚠️ Max drawdown < -15%: Review strategy
- ⚠️ Confidence < 0.5 for 5+ signals: Wait for clearer conditions
- ✅ Confidence > 0.8: Strong opportunity

## Troubleshooting

### Bot Not Trading

**Issue**: Bot started but no trades executed

**Checks**:

1. Verify confidence threshold isn't too high:

   ```bash
   GET /api/bots/{bot_id}/analysis
   # Check if analysis.confidence < config.confidence_threshold
   ```

2. Check risk score isn't blocking trades:

   ```bash
   GET /api/bots/{bot_id}/risk-metrics
   # risk_score > 0.7 may trigger conservative mode
   ```

3. Review market regime:

   ```bash
   GET /api/bots/{bot_id}/analysis
   # Sideways markets produce fewer signals
   ```

### Low Confidence Signals

**Issue**: Analysis always returns confidence < 0.5

**Solutions**:

1. **Check data quality**: Need minimum 100 candles
2. **Timeframe**: Use 1h or 4h candles (more stable than 1m)
3. **Market condition**: Sideways markets naturally have low confidence
4. **Lower threshold temporarily**: Set confidence_threshold to 0.55

### High Risk Scores

**Issue**: Risk metrics always show risk_score > 0.7

**This is normal during**:

- Major news events
- Market crashes/pumps
- Low liquidity periods
- Weekends (for crypto)

**Actions**:

- Wait for volatility to decrease
- Reduce position sizes
- Increase confidence threshold to 0.75
- Consider pausing bot temporarily

## Best Practices

### 1. Start Small

- Begin with minimum account_balance
- Use conservative confidence_threshold (0.75)
- Monitor for 24 hours before scaling up

### 2. Diversify

```json
// Run multiple bots on different assets
[
  {"symbol": "BTC/USDT", "strategy": "smart_adaptive"},
  {"symbol": "ETH/USDT", "strategy": "smart_adaptive"},
  {"symbol": "SOL/USDT", "strategy": "smart_adaptive"}
]
```

### 3. Regular Monitoring

- Check `/analysis` endpoint every hour
- Review `/risk-metrics` daily
- Run `/optimize` weekly or after major market changes
- Track performance via `/performance` endpoint

### 4. Risk Management

- Never risk more than 2% per trade
- Keep max exposure under 10% of portfolio
- Use stop-losses on all positions (built-in)
- Respect the adaptive position sizing

### 5. Continuous Optimization

```bash
# Weekly optimization
POST /api/bots/{bot_id}/optimize

# Update bot with new parameters
PATCH /api/bots/{bot_id}
{
  "config": {
    ...optimized_parameters
  }
}
```

## Example Trading Flow

```bash
# 1. Create bot
curl -X POST http://localhost:8000/api/bots \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BTC Smart",
    "symbol": "BTC/USDT",
    "strategy": "smart_adaptive",
    "config": {
      "account_balance": 10000,
      "risk_per_trade": 0.02,
      "confidence_threshold": 0.65
    }
  }'

# 2. Get analysis before starting
curl -X GET http://localhost:8000/api/bots/BOT_ID/analysis \
  -H "Authorization: Bearer TOKEN"

# 3. Start if conditions are good
curl -X POST http://localhost:8000/api/bots/BOT_ID/start \
  -H "Authorization: Bearer TOKEN"

# 4. Monitor regularly
while true; do
  curl -X GET http://localhost:8000/api/bots/BOT_ID/analysis \
    -H "Authorization: Bearer TOKEN"
  sleep 300  # Check every 5 minutes
done
```

## Performance Expectations

### Typical Results (Backtested)

- **Win Rate**: 55-65% (good strategies are around 60%)
- **Risk/Reward**: 1:1.5 to 1:2.5
- **Sharpe Ratio**: 1.5+ in favorable markets
- **Max Drawdown**: -10% to -15% (normal range)

### Market-Specific

- **Bull Markets**: Best performance, 65%+ win rate
- **Bear Markets**: Reduced frequency, focus on quality
- **Sideways**: Lower win rate (50-55%), but better R:R
- **Volatile**: Mixed results, requires tight risk management

## Next Steps

1. **Read Full Documentation**: `/docs/SMART_TRADING_ENGINE.md`
2. **Explore API Reference**: `/docs/API_REFERENCE.md`
3. **Review Architecture**: `.github/copilot-instructions.md`
4. **Run Tests**: `npm test` to verify setup
5. **Join Community**: [Link to Discord/Forum]

## Support

- **Documentation**: `/docs/`
- **Issues**: GitHub Issues
- **API Help**: `/docs/API_REFERENCE.md`
- **Examples**: `/examples/` (coming soon)

---

**Happy Smart Trading! 🚀**
