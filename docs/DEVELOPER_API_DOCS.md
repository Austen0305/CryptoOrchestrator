# Developer API Documentation

## Overview

This document provides comprehensive API documentation for developers integrating with CryptoOrchestrator. The API is built on FastAPI and provides automatic OpenAPI/Swagger documentation.

## API Base URL

```
Production: https://api.cryptoorchestrator.com/api
Development: http://localhost:8000/api
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Authentication

All API endpoints (except `/api/auth/*`) require JWT authentication.

### Getting a Token

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Using the Token

Include the token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

## API Endpoints Reference

### Authentication

#### `POST /api/auth/register`
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "username": "trader123"
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "trader123",
  "created_at": "2025-11-15T12:00:00Z"
}
```

#### `POST /api/auth/login`
Authenticate and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "trader123"
  }
}
```

### Trading Bots

#### `GET /api/bots`
List all trading bots for the authenticated user.

**Response:**
```json
{
  "bots": [
    {
      "id": "bot_uuid",
      "name": "My Trading Bot",
      "strategy": "rsi",
      "symbol": "BTC/USD",
      "status": "active",
      "created_at": "2025-11-15T12:00:00Z"
    }
  ]
}
```

#### `POST /api/bots`
Create a new trading bot.

**Request:**
```json
{
  "name": "My Trading Bot",
  "strategy": "rsi",
  "symbol": "BTC/USD",
  "config": {
    "risk_per_trade": 0.02,
    "stop_loss": 0.02,
    "take_profit": 0.05
  }
}
```

#### `GET /api/bots/{bot_id}`
Get details of a specific bot.

#### `PUT /api/bots/{bot_id}`
Update bot configuration.

#### `DELETE /api/bots/{bot_id}`
Delete a trading bot.

### Strategies

#### `GET /api/strategies`
List all user strategies.

#### `POST /api/strategies`
Create a new strategy.

**Request:**
```json
{
  "name": "My Custom Strategy",
  "type": "technical",
  "config": {
    "indicators": ["rsi", "macd"],
    "entry_conditions": {},
    "exit_conditions": {}
  }
}
```

#### `GET /api/strategies/templates`
Get available strategy templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "rsi",
      "name": "RSI Strategy",
      "description": "Relative Strength Index strategy",
      "type": "technical",
      "default_config": {}
    }
  ]
}
```

#### `POST /api/strategies/{strategy_id}/backtest`
Run backtest on a strategy.

### Market Data

#### `GET /api/markets/tickers`
Get current market tickers.

**Response:**
```json
{
  "tickers": [
    {
      "symbol": "BTC/USD",
      "price": 47500.0,
      "volume": 1000000.0,
      "change_24h": 0.0476
    }
  ]
}
```

#### `GET /api/markets/ohlcv/{symbol}`
Get OHLCV (candlestick) data.

**Query Parameters:**
- `timeframe`: `1m`, `5m`, `15m`, `1h`, `4h`, `1d` (default: `1h`)
- `limit`: Number of candles (default: 168)
- `since`: Start timestamp (optional)

### Portfolio

#### `GET /api/portfolio`
Get portfolio information.

**Response:**
```json
{
  "total_balance": 10000.0,
  "available_balance": 5000.0,
  "positions": {
    "BTC/USD": {
      "amount": 0.1,
      "value": 4750.0,
      "unrealized_pnl": 250.0
    }
  }
}
```

### Risk Management

#### `GET /api/risk/metrics`
Get current risk metrics.

#### `POST /api/risk/var/calculate`
Calculate Value at Risk.

**Request:**
```json
{
  "returns": [0.01, -0.02, 0.015, ...],
  "portfolio_value": 10000.0,
  "confidence_level": 0.95,
  "time_horizon_days": 1,
  "method": "historical"
}
```

#### `POST /api/risk/monte-carlo/simulate`
Run Monte Carlo simulation.

#### `GET /api/risk/kill-switch/state`
Get drawdown kill switch state.

#### `POST /api/risk/kill-switch/activate`
Manually activate kill switch.

### AI Copilot

#### `POST /api/ai-copilot/trade/explain`
Get natural language explanation of a trade.

**Request:**
```json
{
  "trade_id": "trade_uuid",
  "trade_data": {
    "symbol": "BTC/USD",
    "side": "buy",
    "amount": 0.1,
    "price": 47500.0
  },
  "market_data": {
    "indicators": {
      "rsi": 65.0,
      "macd": {"signal": "bullish"}
    }
  }
}
```

#### `POST /api/ai-copilot/strategy/generate`
Generate trading strategy from natural language.

**Request:**
```json
{
  "description": "Create a trend following strategy using moving averages",
  "timeframe": "1h",
  "risk_level": "moderate"
}
```

#### `POST /api/ai-copilot/strategy/optimize`
Get strategy optimization recommendations.

#### `POST /api/ai-copilot/backtest/summarize`
Generate AI summary of backtest results.

### Automation

#### `POST /api/automation/hedging/start`
Start automatic hedging for a portfolio.

#### `POST /api/automation/strategy-switching/start`
Start adaptive strategy switching for a bot.

#### `POST /api/automation/alerts/rules`
Create a smart alert rule.

#### `POST /api/automation/portfolio/optimize`
Get portfolio optimization recommendations.

### Machine Learning

#### `POST /api/ml-v2/optimize`
Run AutoML hyperparameter optimization.

#### `POST /api/ml-v2/rl/train`
Train reinforcement learning agent.

#### `POST /api/ml-v2/sentiment/analyze`
Analyze market sentiment from text.

#### `POST /api/ml-v2/regime/detect`
Detect current market regime.

### Exchange Integration

#### `GET /api/exchanges/tickers`
Get tickers from all connected exchanges.

#### `POST /api/exchanges/smart-routing/route`
Route order using smart routing.

## Error Handling

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Common Error Codes

- `400` - Bad Request: Invalid input parameters
- `401` - Unauthorized: Missing or invalid authentication
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource doesn't exist
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server-side error

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Default**: 1000 requests per hour per user
- **Burst**: Up to 100 requests per minute
- Rate limit headers:
  - `X-RateLimit-Limit`: Maximum requests per hour
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market-data');
```

### Market Data Stream

**Subscribe:**
```json
{
  "action": "subscribe",
  "channels": ["ticker", "trades", "orderbook"],
  "symbols": ["BTC/USD", "ETH/USD"]
}
```

**Message Format:**
```json
{
  "channel": "ticker",
  "symbol": "BTC/USD",
  "data": {
    "price": 47500.0,
    "volume": 1000000.0
  },
  "timestamp": "2025-11-15T12:00:00Z"
}
```

## SDK Examples

### Python SDK

```python
from cryptoorchestrator import CryptoOrchestratorClient

client = CryptoOrchestratorClient(
    api_key="your_api_key",
    base_url="http://localhost:8000/api"
)

# Authenticate
token = client.auth.login("user@example.com", "password")
client.set_token(token)

# List bots
bots = client.bots.list()

# Create bot
bot = client.bots.create({
    "name": "My Bot",
    "strategy": "rsi",
    "symbol": "BTC/USD"
})

# Get market data
ticker = client.markets.get_ticker("BTC/USD")

# Run backtest
result = client.strategies.backtest(strategy_id, {
    "start_date": "2025-01-01",
    "end_date": "2025-11-15",
    "initial_capital": 10000
})
```

### JavaScript SDK

```javascript
import { CryptoOrchestratorClient } from '@cryptoorchestrator/sdk';

const client = new CryptoOrchestratorClient({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8000/api'
});

// Authenticate
const token = await client.auth.login('user@example.com', 'password');
client.setToken(token);

// List bots
const bots = await client.bots.list();

// Create bot
const bot = await client.bots.create({
  name: 'My Bot',
  strategy: 'rsi',
  symbol: 'BTC/USD'
});

// Get market data
const ticker = await client.markets.getTicker('BTC/USD');

// Run backtest
const result = await client.strategies.backtest(strategyId, {
  startDate: '2025-01-01',
  endDate: '2025-11-15',
  initialCapital: 10000
});
```

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)

**Response:**
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

## Filtering and Sorting

List endpoints support filtering and sorting:

**Query Parameters:**
- `filter`: Filter criteria (JSON string)
- `sort`: Sort field and direction (e.g., `created_at:desc`)
- `search`: Search query (searches name, description, etc.)

**Example:**
```
GET /api/bots?filter={"status":"active"}&sort=created_at:desc&search=RSI
```

## Webhooks

Configure webhooks to receive real-time notifications:

**Create Webhook:**
```json
POST /api/webhooks
{
  "url": "https://your-server.com/webhooks",
  "events": ["trade.executed", "bot.stopped", "alert.triggered"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload:**
```json
{
  "event": "trade.executed",
  "timestamp": "2025-11-15T12:00:00Z",
  "data": {
    "trade_id": "uuid",
    "bot_id": "uuid",
    "symbol": "BTC/USD",
    "side": "buy",
    "amount": 0.1,
    "price": 47500.0
  },
  "signature": "hmac_sha256_signature"
}
```

## Best Practices

1. **Always use HTTPS in production**
2. **Store API keys securely** - Never commit to version control
3. **Implement retry logic** - Handle transient failures gracefully
4. **Respect rate limits** - Implement exponential backoff
5. **Use WebSockets for real-time data** - More efficient than polling
6. **Validate inputs** - Client-side validation improves UX
7. **Handle errors gracefully** - Provide meaningful error messages
8. **Monitor API usage** - Track rate limits and errors
9. **Use pagination** - Don't fetch all data at once
10. **Cache when appropriate** - Reduce API calls for static data

## Testing

Use the Swagger UI at `/docs` for interactive API testing, or test endpoints programmatically:

```python
# Python example
import requests

response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={
        'email': 'user@example.com',
        'password': 'password'
    }
)
token = response.json()['access_token']

headers = {'Authorization': f'Bearer {token}'}
bots = requests.get('http://localhost:8000/api/bots', headers=headers)
```

## Support

For API support:
- **Documentation**: See `/docs` for interactive API docs
- **Issues**: Report bugs via GitHub Issues
- **Discord**: Join our developer community
- **Email**: api-support@cryptoorchestrator.com

