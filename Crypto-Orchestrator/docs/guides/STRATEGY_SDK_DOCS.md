# Strategy SDK Documentation

## Overview

The CryptoOrchestrator Strategy SDK allows developers to create custom trading strategies that integrate seamlessly with the platform. Strategies can be written in Python or JavaScript/TypeScript and can leverage all platform features including ML models, risk management, and exchange integrations.

## Quick Start

### Python Strategy

```python
from cryptoorchestrator.strategy import Strategy, MarketData, Signal

class MyCustomStrategy(Strategy):
    """My custom trading strategy"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.rsi_period = config.get('rsi_period', 14)
        self.overbought = config.get('overbought', 70)
        self.oversold = config.get('oversold', 30)
    
    def initialize(self):
        """Initialize strategy resources"""
        self.logger.info("Strategy initialized")
    
    def analyze(self, market_data: MarketData) -> Signal:
        """Analyze market data and generate trading signal"""
        # Calculate RSI
        rsi = self.calculate_rsi(market_data.close_prices, self.rsi_period)
        
        # Generate signal
        if rsi < self.oversold:
            return Signal(
                action="buy",
                confidence=0.8,
                reasoning=f"RSI {rsi:.2f} indicates oversold conditions"
            )
        elif rsi > self.overbought:
            return Signal(
                action="sell",
                confidence=0.75,
                reasoning=f"RSI {rsi:.2f} indicates overbought conditions"
            )
        else:
            return Signal(
                action="hold",
                confidence=0.5,
                reasoning=f"RSI {rsi:.2f} in neutral range"
            )
    
    def calculate_rsi(self, prices: list, period: int) -> float:
        """Calculate Relative Strength Index"""
        # Implementation here
        return 50.0  # Placeholder
```

### JavaScript/TypeScript Strategy

```typescript
import { Strategy, MarketData, Signal } from '@cryptoorchestrator/strategy-sdk';

class MyCustomStrategy extends Strategy {
  private rsiPeriod: number = 14;
  private overbought: number = 70;
  private oversold: number = 30;

  constructor(config: any) {
    super(config);
    this.rsiPeriod = config.rsi_period || 14;
    this.overbought = config.overbought || 70;
    this.oversold = config.oversold || 30;
  }

  initialize(): void {
    this.logger.info('Strategy initialized');
  }

  analyze(marketData: MarketData): Signal {
    // Calculate RSI
    const rsi = this.calculateRSI(marketData.closePrices, this.rsiPeriod);

    // Generate signal
    if (rsi < this.oversold) {
      return {
        action: 'buy',
        confidence: 0.8,
        reasoning: `RSI ${rsi.toFixed(2)} indicates oversold conditions`
      };
    } else if (rsi > this.overbought) {
      return {
        action: 'sell',
        confidence: 0.75,
        reasoning: `RSI ${rsi.toFixed(2)} indicates overbought conditions`
      };
    } else {
      return {
        action: 'hold',
        confidence: 0.5,
        reasoning: `RSI ${rsi.toFixed(2)} in neutral range`
      };
    }
  }

  private calculateRSI(prices: number[], period: number): number {
    // Implementation here
    return 50.0; // Placeholder
  }
}
```

## Strategy Interface

### Base Strategy Class

All strategies must extend the base `Strategy` class:

```python
class Strategy:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.indicators = IndicatorLibrary()
        self.ml_models = MLModelLibrary()
        self.risk_manager = RiskManager()
    
    def initialize(self):
        """Called once when strategy is loaded"""
        pass
    
    def analyze(self, market_data: MarketData) -> Signal:
        """Main analysis method - must be implemented"""
        raise NotImplementedError
    
    def on_trade_executed(self, trade: Trade):
        """Called when a trade is executed"""
        pass
    
    def on_trade_closed(self, trade: Trade):
        """Called when a trade is closed"""
        pass
    
    def cleanup(self):
        """Called when strategy is unloaded"""
        pass
```

## Market Data

### MarketData Object

```python
class MarketData:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    candles: List[Candle]  # Historical candles
    indicators: Dict[str, Any]  # Pre-calculated indicators
```

### Accessing Historical Data

```python
def analyze(self, market_data: MarketData) -> Signal:
    # Get last 100 candles
    recent_candles = market_data.candles[-100:]
    
    # Access OHLCV data
    closes = [c.close for c in recent_candles]
    volumes = [c.volume for c in recent_candles]
    
    # Calculate indicators
    sma_20 = self.indicators.sma(closes, 20)
    ema_50 = self.indicators.ema(closes, 50)
    rsi = self.indicators.rsi(closes, 14)
    
    # Use in strategy logic
    if rsi[-1] < 30 and closes[-1] < sma_20[-1]:
        return Signal(action="buy", confidence=0.8)
```

## Trading Signals

### Signal Object

```python
class Signal:
    action: str  # "buy", "sell", "hold"
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Human-readable explanation
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    metadata: Dict[str, Any] = {}
```

### Generating Signals

```python
def analyze(self, market_data: MarketData) -> Signal:
    # Your analysis logic
    price = market_data.close
    
    # Calculate stop loss and take profit
    stop_loss = price * 0.98  # 2% stop loss
    take_profit = price * 1.05  # 5% take profit
    
    # Calculate position size (optional)
    position_size = self.risk_manager.calculate_position_size(
        entry_price=price,
        stop_loss=stop_loss,
        risk_per_trade=0.02  # 2% risk
    )
    
    return Signal(
        action="buy",
        confidence=0.75,
        reasoning="Strong bullish signal detected",
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size
    )
```

## Indicator Library

The SDK provides a comprehensive indicator library:

```python
# Moving Averages
sma = self.indicators.sma(prices, period=20)
ema = self.indicators.ema(prices, period=50)
wma = self.indicators.wma(prices, period=20)

# Momentum Indicators
rsi = self.indicators.rsi(prices, period=14)
stoch = self.indicators.stochastic(high, low, close, period=14)
williams_r = self.indicators.williams_r(high, low, close, period=14)

# Trend Indicators
macd = self.indicators.macd(prices, fast=12, slow=26, signal=9)
adx = self.indicators.adx(high, low, close, period=14)
aroon = self.indicators.aroon(high, low, period=14)

# Volatility Indicators
bollinger = self.indicators.bollinger_bands(prices, period=20, std=2)
atr = self.indicators.atr(high, low, close, period=14)

# Volume Indicators
obv = self.indicators.obv(close, volume)
vwap = self.indicators.vwap(high, low, close, volume)

# Custom Indicators
custom = self.indicators.custom(indicator_name, params)
```

## Machine Learning Integration

### Using ML Models in Strategies

```python
def analyze(self, market_data: MarketData) -> Signal:
    # Get ML prediction
    prediction = self.ml_models.predict(
        model_type="lstm",
        market_data=market_data,
        lookback_period=60
    )
    
    # Combine ML prediction with technical analysis
    rsi = self.indicators.rsi(market_data.close_prices, 14)
    macd = self.indicators.macd(market_data.close_prices)
    
    # Weighted decision
    ml_weight = 0.6
    ta_weight = 0.4
    
    if prediction.action == "buy" and rsi[-1] < 40:
        confidence = (prediction.confidence * ml_weight) + (0.7 * ta_weight)
        return Signal(
            action="buy",
            confidence=confidence,
            reasoning=f"ML predicts buy ({prediction.confidence:.2f}), RSI confirms"
        )
```

### Available ML Models

- `lstm`: LSTM neural network
- `gru`: GRU neural network
- `transformer`: Transformer model
- `xgboost`: XGBoost gradient boosting
- `ensemble`: Ensemble of multiple models

## Risk Management Integration

### Using Risk Manager

```python
def analyze(self, market_data: MarketData) -> Signal:
    price = market_data.close
    
    # Get risk limits
    max_position_size = self.risk_manager.get_max_position_size()
    max_daily_loss = self.risk_manager.get_max_daily_loss()
    
    # Calculate position size based on risk
    stop_loss = price * 0.02  # 2% stop loss
    position_size = self.risk_manager.calculate_position_size(
        entry_price=price,
        stop_loss=stop_loss,
        risk_per_trade=0.02
    )
    
    # Check if trade is allowed
    if not self.risk_manager.can_trade(position_size):
        return Signal(action="hold", confidence=0.0, reasoning="Risk limits exceeded")
    
    return Signal(
        action="buy",
        confidence=0.75,
        stop_loss=stop_loss,
        position_size=position_size
    )
```

## Strategy Configuration

### Config Schema

```python
{
    "name": "My Strategy",
    "type": "technical",  # "technical", "ml", "hybrid"
    "symbol": "BTC/USD",
    "timeframe": "1h",
    "indicators": {
        "rsi_period": 14,
        "macd_fast": 12,
        "macd_slow": 26
    },
    "risk": {
        "risk_per_trade": 0.02,
        "max_position_size": 0.1,
        "stop_loss": 0.02,
        "take_profit": 0.05
    },
    "ml": {
        "enabled": True,
        "model_type": "lstm",
        "confidence_threshold": 0.6
    }
}
```

## Strategy Lifecycle

### 1. Initialization

```python
def initialize(self):
    """Called when strategy is loaded"""
    # Load ML models
    if self.config.get('ml', {}).get('enabled'):
        self.ml_model = self.ml_models.load(
            model_type=self.config['ml']['model_type']
        )
    
    # Initialize indicators
    self.rsi = self.indicators.rsi
    self.macd = self.indicators.macd
    
    # Setup risk manager
    self.risk_manager.configure(self.config.get('risk', {}))
```

### 2. Analysis Loop

```python
def analyze(self, market_data: MarketData) -> Signal:
    """Called on each market data update"""
    # Your strategy logic here
    return Signal(action="hold", confidence=0.5)
```

### 3. Trade Callbacks

```python
def on_trade_executed(self, trade: Trade):
    """Called when a trade is executed"""
    self.logger.info(f"Trade executed: {trade.id}")
    # Update strategy state if needed

def on_trade_closed(self, trade: Trade):
    """Called when a trade is closed"""
    self.logger.info(f"Trade closed: {trade.id}, PnL: {trade.pnl}")
    # Learn from trade outcome if needed
```

### 4. Cleanup

```python
def cleanup(self):
    """Called when strategy is unloaded"""
    # Save state, close connections, etc.
    if hasattr(self, 'ml_model'):
        self.ml_model.save_state()
```

## Backtesting

### Running Backtests

```python
from cryptoorchestrator.backtest import BacktestRunner

runner = BacktestRunner()

result = runner.run(
    strategy=MyCustomStrategy,
    config={
        "symbol": "BTC/USD",
        "start_date": "2025-01-01",
        "end_date": "2025-11-15",
        "initial_capital": 10000,
        "timeframe": "1h"
    }
)

print(f"Total Return: {result.total_return:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2f}%")
print(f"Win Rate: {result.win_rate:.2f}%")
```

## Advanced Features

### Custom Indicators

```python
def calculate_custom_indicator(self, prices: list) -> float:
    """Calculate custom indicator"""
    # Your custom calculation
    return value

# Use in strategy
custom_value = self.calculate_custom_indicator(market_data.close_prices)
```

### Multi-Timeframe Analysis

```python
def analyze(self, market_data: MarketData) -> Signal:
    # Get higher timeframe data
    higher_tf = self.get_market_data(
        symbol=market_data.symbol,
        timeframe="4h"
    )
    
    # Analyze both timeframes
    daily_trend = self.analyze_trend(higher_tf)
    hourly_signal = self.analyze_signal(market_data)
    
    # Combine signals
    if daily_trend == "bullish" and hourly_signal.action == "buy":
        return Signal(action="buy", confidence=0.8)
```

### State Management

```python
class MyStrategy(Strategy):
    def __init__(self, config: dict):
        super().__init__(config)
        self.state = {
            "last_signal": None,
            "trade_count": 0,
            "win_count": 0
        }
    
    def on_trade_closed(self, trade: Trade):
        self.state["trade_count"] += 1
        if trade.pnl > 0:
            self.state["win_count"] += 1
    
    def get_win_rate(self) -> float:
        if self.state["trade_count"] == 0:
            return 0.0
        return self.state["win_count"] / self.state["trade_count"]
```

## Publishing Strategies

### Strategy Metadata

```python
STRATEGY_METADATA = {
    "name": "My Custom Strategy",
    "version": "1.0.0",
    "description": "RSI-based mean reversion strategy",
    "author": "Your Name",
    "license": "MIT",
    "tags": ["rsi", "mean-reversion", "scalping"],
    "requirements": {
        "min_timeframe": "5m",
        "recommended_timeframe": "1h",
        "min_capital": 1000
    }
}
```

### Publishing to Marketplace

```python
from cryptoorchestrator.marketplace import StrategyPublisher

publisher = StrategyPublisher()

publisher.publish(
    strategy_class=MyCustomStrategy,
    metadata=STRATEGY_METADATA,
    price=99.99,  # Optional: set price for paid strategy
    is_public=True
)
```

## Best Practices

1. **Test thoroughly** - Always backtest before live trading
2. **Use risk management** - Never exceed risk limits
3. **Log everything** - Comprehensive logging helps debugging
4. **Handle errors** - Graceful error handling prevents crashes
5. **Optimize performance** - Cache calculations when possible
6. **Document your strategy** - Clear comments and docstrings
7. **Version control** - Use Git to track strategy changes
8. **Paper trade first** - Test with paper trading before live
9. **Monitor performance** - Track metrics and adjust accordingly
10. **Follow conventions** - Stick to SDK patterns and conventions

## Examples

See the `/examples` directory for complete strategy examples:

- `rsi_strategy.py` - Simple RSI strategy
- `macd_strategy.py` - MACD crossover strategy
- `ml_strategy.py` - ML-powered strategy
- `multi_timeframe_strategy.py` - Multi-timeframe analysis
- `pairs_trading_strategy.py` - Pairs trading strategy

## Support

- **Documentation**: Full API docs at `/docs`
- **Examples**: See `/examples` directory
- **Community**: Join Discord for strategy discussions
- **Support**: Email sdk-support@cryptoorchestrator.com

