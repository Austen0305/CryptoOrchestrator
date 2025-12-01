# Sample Backtest Reports

## Overview

This document provides sample backtest reports demonstrating the reporting capabilities of CryptoOrchestrator's backtesting engine. These reports show various performance metrics, visualizations, and analysis.

## Report 1: RSI Mean Reversion Strategy

### Strategy Configuration

```json
{
  "name": "RSI Mean Reversion",
  "type": "technical",
  "symbol": "BTC/USD",
  "timeframe": "1h",
  "period": {
    "start": "2025-01-01",
    "end": "2025-11-15"
  },
  "initial_capital": 10000,
  "parameters": {
    "rsi_period": 14,
    "oversold": 30,
    "overbought": 70,
    "stop_loss": 0.02,
    "take_profit": 0.05
  }
}
```

### Performance Summary

| Metric | Value |
|--------|-------|
| **Total Return** | +24.5% |
| **Annualized Return** | +29.4% |
| **Sharpe Ratio** | 1.85 |
| **Sortino Ratio** | 2.12 |
| **Maximum Drawdown** | -8.3% |
| **Win Rate** | 58.2% |
| **Profit Factor** | 1.92 |
| **Total Trades** | 342 |
| **Winning Trades** | 199 |
| **Losing Trades** | 143 |
| **Average Win** | $125.50 |
| **Average Loss** | -$65.30 |
| **Largest Win** | $450.00 |
| **Largest Loss** | -$210.00 |
| **Average Trade Duration** | 4.2 hours |
| **Calmar Ratio** | 3.54 |

### Equity Curve

```
Initial Capital: $10,000
Peak Capital:    $12,780
Final Capital:   $12,450
Max Drawdown:    -$830 (from peak)
```

### Monthly Performance

| Month | Return | Cumulative Return | Trades | Win Rate |
|-------|--------|-------------------|--------|----------|
| Jan 2025 | +2.1% | +2.1% | 28 | 57.1% |
| Feb 2025 | +3.2% | +5.4% | 32 | 59.4% |
| Mar 2025 | -1.5% | +3.8% | 29 | 51.7% |
| Apr 2025 | +4.8% | +8.8% | 31 | 61.3% |
| May 2025 | +2.3% | +11.3% | 27 | 55.6% |
| Jun 2025 | +1.9% | +13.4% | 30 | 60.0% |
| Jul 2025 | -0.8% | +12.5% | 28 | 53.6% |
| Aug 2025 | +3.5% | +16.5% | 33 | 60.6% |
| Sep 2025 | +2.7% | +19.5% | 29 | 58.6% |
| Oct 2025 | +2.1% | +22.0% | 31 | 58.1% |
| Nov 2025 | +2.0% | +24.5% | 24 | 62.5% |

### Risk Metrics

- **Value at Risk (95%)**: $420 (one day)
- **Conditional VaR (95%)**: $580
- **Volatility**: 12.3% (annualized)
- **Beta**: 0.85
- **Alpha**: +8.2%

### Trade Distribution

- **Best Day**: +$325 (Mar 15, 2025)
- **Worst Day**: -$180 (Jul 22, 2025)
- **Consecutive Wins**: 8 trades
- **Consecutive Losses**: 4 trades
- **Average Drawdown**: -4.2%
- **Time to Recover**: 6 days (average)

### Recommendations

1. ✅ Strategy shows consistent positive returns
2. ✅ Risk-adjusted returns (Sharpe > 1.5) are excellent
3. ⚠️ Consider tighter stop-loss during volatile periods
4. 💡 Opportunity to increase position size during high-confidence setups

---

## Report 2: ML-Powered LSTM Strategy

### Strategy Configuration

```json
{
  "name": "LSTM Price Prediction",
  "type": "ml",
  "symbol": "ETH/USD",
  "timeframe": "4h",
  "period": {
    "start": "2025-01-01",
    "end": "2025-11-15"
  },
  "initial_capital": 10000,
  "ml_config": {
    "model_type": "lstm",
    "sequence_length": 60,
    "confidence_threshold": 0.65,
    "ensemble": true
  },
  "risk_config": {
    "risk_per_trade": 0.025,
    "stop_loss": 0.03,
    "take_profit": 0.08
  }
}
```

### Performance Summary

| Metric | Value |
|--------|-------|
| **Total Return** | +32.8% |
| **Annualized Return** | +39.4% |
| **Sharpe Ratio** | 2.15 |
| **Sortino Ratio** | 2.48 |
| **Maximum Drawdown** | -9.1% |
| **Win Rate** | 62.5% |
| **Profit Factor** | 2.18 |
| **Total Trades** | 156 |
| **Winning Trades** | 98 |
| **Losing Trades** | 58 |
| **Average Win** | $210.40 |
| **Average Loss** | -$96.60 |
| **Largest Win** | $680.00 |
| **Largest Loss** | -$310.00 |
| **Average Trade Duration** | 18.5 hours |
| **Calmar Ratio** | 4.33 |

### ML Model Performance

- **Model Accuracy**: 67.3%
- **Precision**: 0.72
- **Recall**: 0.65
- **F1-Score**: 0.68
- **Prediction Confidence**: 0.71 (average)

### Equity Curve

```
Initial Capital: $10,000
Peak Capital:    $13,650
Final Capital:   $13,280
Max Drawdown:    -$910 (from peak)
```

### Monthly Performance

| Month | Return | Cumulative Return | Trades | Win Rate | Avg Confidence |
|-------|--------|-------------------|--------|----------|----------------|
| Jan 2025 | +3.2% | +3.2% | 12 | 66.7% | 0.72 |
| Feb 2025 | +4.1% | +7.5% | 14 | 64.3% | 0.69 |
| Mar 2025 | -2.1% | +5.2% | 13 | 53.8% | 0.68 |
| Apr 2025 | +5.5% | +11.1% | 15 | 73.3% | 0.75 |
| May 2025 | +3.8% | +15.3% | 12 | 66.7% | 0.71 |
| Jun 2025 | +2.9% | +18.7% | 13 | 61.5% | 0.70 |
| Jul 2025 | -1.2% | +17.2% | 14 | 57.1% | 0.66 |
| Aug 2025 | +4.2% | +22.1% | 16 | 68.8% | 0.73 |
| Sep 2025 | +3.1% | +25.9% | 13 | 61.5% | 0.71 |
| Oct 2025 | +3.5% | +30.2% | 15 | 66.7% | 0.74 |
| Nov 2025 | +2.0% | +32.8% | 9 | 66.7% | 0.72 |

### Risk Metrics

- **Value at Risk (95%)**: $540 (one day)
- **Conditional VaR (95%)**: $720
- **Volatility**: 14.2% (annualized)
- **Beta**: 0.92
- **Alpha**: +12.5%

### ML Model Insights

- **Best Predictions**: Trend-following scenarios (72% accuracy)
- **Worst Predictions**: Volatile/choppy markets (58% accuracy)
- **Feature Importance**: Volume (32%), Price momentum (28%), RSI (18%)
- **Model Stability**: Consistent performance across time periods

### Recommendations

1. ✅ ML model shows superior risk-adjusted returns
2. ✅ Higher win rate and profit factor than technical-only strategies
3. ⚠️ Model struggles during high volatility periods - consider regime filtering
4. 💡 Opportunity to increase position size for high-confidence predictions (>0.75)

---

## Report 3: Multi-Strategy Ensemble

### Strategy Configuration

```json
{
  "name": "Ensemble Strategy",
  "type": "hybrid",
  "symbol": "BTC/USD",
  "timeframe": "1h",
  "period": {
    "start": "2025-01-01",
    "end": "2025-11-15"
  },
  "initial_capital": 10000,
  "strategies": [
    {
      "name": "RSI Strategy",
      "weight": 0.3,
      "config": {...}
    },
    {
      "name": "LSTM Strategy",
      "weight": 0.5,
      "config": {...}
    },
    {
      "name": "MACD Strategy",
      "weight": 0.2,
      "config": {...}
    }
  ]
}
```

### Performance Summary

| Metric | Value |
|--------|-------|
| **Total Return** | +28.3% |
| **Annualized Return** | +34.0% |
| **Sharpe Ratio** | 2.05 |
| **Sortino Ratio** | 2.35 |
| **Maximum Drawdown** | -7.8% |
| **Win Rate** | 60.8% |
| **Profit Factor** | 2.05 |
| **Total Trades** | 245 |
| **Winning Trades** | 149 |
| **Losing Trades** | 96 |
| **Average Win** | $115.80 |
| **Average Loss** | -$56.50 |
| **Largest Win** | $420.00 |
| **Largest Loss** | -$185.00 |
| **Average Trade Duration** | 6.8 hours |
| **Calmar Ratio** | 4.36 |

### Strategy Contribution

| Strategy | Weight | Return | Contribution | Trades | Win Rate |
|----------|--------|--------|--------------|--------|----------|
| LSTM | 50% | +16.2% | +8.1% | 156 | 62.5% |
| RSI | 30% | +12.5% | +3.75% | 342 | 58.2% |
| MACD | 20% | +11.8% | +2.36% | 198 | 59.6% |

### Equity Curve

```
Initial Capital: $10,000
Peak Capital:    $13,150
Final Capital:   $12,830
Max Drawdown:    -$780 (from peak)
```

### Risk Metrics

- **Value at Risk (95%)**: $450 (one day)
- **Conditional VaR (95%)**: $620
- **Volatility**: 11.8% (annualized)
- **Beta**: 0.88
- **Alpha**: +10.2%

### Ensemble Benefits

- ✅ **Lower Drawdown**: -7.8% vs -9.1% (best single strategy)
- ✅ **Higher Sharpe**: 2.05 vs 2.15 (slightly lower but more consistent)
- ✅ **Diversification**: Multiple strategies reduce single-strategy risk
- ✅ **Smoother Equity Curve**: Less volatile than individual strategies

### Recommendations

1. ✅ Ensemble provides balanced risk-adjusted returns
2. ✅ Lower maximum drawdown than individual strategies
3. 💡 Consider rebalancing strategy weights based on recent performance
4. 💡 Opportunity to add sentiment analysis for additional alpha

---

## Report Format

All backtest reports include:

1. **Executive Summary**: High-level performance overview
2. **Performance Metrics**: Comprehensive quantitative metrics
3. **Equity Curve**: Visual representation of capital over time
4. **Trade Analysis**: Detailed trade statistics
5. **Risk Analysis**: Risk metrics and drawdown analysis
6. **Monthly Breakdown**: Performance by time period
7. **Recommendations**: AI-generated optimization suggestions

## AI-Generated Summaries

Each backtest report includes an AI-generated natural language summary:

> "The RSI Mean Reversion strategy demonstrated strong performance over the test period, generating a 24.5% return with a Sharpe ratio of 1.85. The strategy showed consistent profitability with a 58.2% win rate and a profit factor of 1.92. Risk management was effective, with a maximum drawdown of only 8.3% and quick recovery times. The strategy performed best during trending market conditions and struggled slightly during high volatility periods. Recommendations include tightening stop-losses during volatile markets and considering position size increases during high-confidence setups."

## Export Options

Backtest reports can be exported in multiple formats:

- **PDF**: Professional formatted reports
- **JSON**: Machine-readable format
- **CSV**: Data tables for analysis
- **HTML**: Interactive web reports

## Comparison Reports

Compare multiple strategies side-by-side:

| Metric | Strategy A | Strategy B | Strategy C | Best |
|--------|------------|------------|------------|------|
| Total Return | +24.5% | +32.8% | +28.3% | B |
| Sharpe Ratio | 1.85 | 2.15 | 2.05 | B |
| Max Drawdown | -8.3% | -9.1% | -7.8% | C |
| Win Rate | 58.2% | 62.5% | 60.8% | B |

