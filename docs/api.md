# API Documentation

Complete API reference for CryptoOrchestrator FastAPI backend.

## Overview

The CryptoOrchestrator API is a RESTful API built with FastAPI, providing 267+ endpoints for trading, analytics, machine learning, and platform management.

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://api.cryptoorchestrator.com`

## Authentication

Most endpoints require authentication via JWT tokens:

```http
Authorization: Bearer <your_jwt_token>
```

Get a token by logging in:
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## OpenAPI Schema

The complete OpenAPI 3.0 schema is auto-generated on server startup and saved to:

- **File:** `docs/openapi.json`
- **Endpoint:** `http://localhost:8000/openapi.json`

### Exporting OpenAPI Schema

The schema is automatically exported when the FastAPI server starts. To manually export:

```python
from server_fastapi.main import app
import json

schema = app.openapi()
with open("docs/openapi.json", "w") as f:
    json.dump(schema, f, indent=2)
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout (invalidate token)
- `GET /api/auth/me` - Get current user info

### Bots
- `GET /api/bots` - List all bots
- `POST /api/bots` - Create new bot
- `GET /api/bots/{id}` - Get bot details
- `PUT /api/bots/{id}` - Update bot
- `DELETE /api/bots/{id}` - Delete bot
- `POST /api/bots/{id}/start` - Start bot
- `POST /api/bots/{id}/stop` - Stop bot

### Trading
- `GET /api/trades` - List trades
- `GET /api/trades/{id}` - Get trade details
- `POST /api/trades` - Execute trade
- `GET /api/markets` - List trading pairs
- `GET /api/markets/{symbol}` - Get market data

### Strategies
- `GET /api/strategies` - List strategies
- `POST /api/strategies` - Create strategy
- `GET /api/strategies/{id}` - Get strategy details
- `PUT /api/strategies/{id}` - Update strategy
- `DELETE /api/strategies/{id}` - Delete strategy

### Machine Learning
- `POST /api/ml-v2/predict` - Get ML prediction
- `POST /api/ml-v2/automl/optimize` - Run AutoML optimization
- `POST /api/ml-v2/reinforcement-learning/train` - Train RL agent
- `GET /api/ml-v2/sentiment/analyze` - Analyze market sentiment
- `GET /api/ml-v2/regime/detect` - Detect market regime

### Risk Management
- `GET /api/risk-management/limits` - Get risk limits
- `PUT /api/risk-management/limits` - Update risk limits
- `GET /api/risk-management/portfolio-heat` - Get portfolio heat
- `POST /api/risk-scenarios/analyze` - Analyze risk scenario

### Backtesting
- `POST /api/backtesting/run` - Run backtest
- `GET /api/backtesting/{id}` - Get backtest results
- `POST /api/backtesting/enhanced/optimize` - Optimize strategy

### Portfolio
- `GET /api/portfolio` - Get portfolio overview
- `GET /api/portfolio/performance` - Get performance metrics
- `GET /api/portfolio/positions` - Get open positions
- `POST /api/portfolio/rebalance` - Rebalance portfolio

### Analytics
- `GET /api/analytics/performance` - Get performance analytics
- `GET /api/analytics/risk` - Get risk analytics
- `GET /api/analytics/trades` - Get trade analytics

### Payments & Licensing
- `POST /api/payments/customers` - Create Stripe customer
- `POST /api/payments/subscriptions` - Create subscription
- `POST /api/licensing/generate` - Generate license key
- `POST /api/licensing/activate` - Activate license
- `GET /api/licensing/validate` - Validate license

### AI Copilot
- `POST /api/ai-copilot/explain-trade` - Explain trade decision
- `POST /api/ai-copilot/generate-strategy` - Generate strategy from text
- `POST /api/ai-copilot/optimize-strategy` - Get optimization suggestions

### Exchanges
- `GET /api/exchanges` - List connected exchanges
- `GET /api/exchanges/{name}/status` - Get exchange status
- `POST /api/exchanges/smart-route` - Smart route order

### Health & Status
- `GET /health` - Health check with database status
- `GET /healthz` - Simple health check (returns `{"status": "ok"}`)
- `GET /api/status` - Detailed system status

## Request/Response Examples

### Create Bot

```http
POST /api/bots
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "BTC Swing Trader",
  "trading_pair": "BTC/USD",
  "strategy": "ml_adaptive",
  "mode": "paper",
  "risk_per_trade": 2.0,
  "stop_loss": 3.0,
  "take_profit": 6.0
}
```

**Response:**
```json
{
  "id": "bot_123",
  "name": "BTC Swing Trader",
  "status": "stopped",
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Get ML Prediction

```http
POST /api/ml-v2/predict
Authorization: Bearer <token>
Content-Type: application/json

{
  "symbol": "BTC/USD",
  "timeframe": "1h",
  "model": "lstm"
}
```

**Response:**
```json
{
  "prediction": 45230.50,
  "confidence": 0.75,
  "direction": "up",
  "model": "lstm"
}
```

## WebSocket API

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Supported Channels:**
- Market data updates
- Trade execution updates
- Bot status changes
- Portfolio updates

## Rate Limiting

API requests are rate-limited:
- **Free tier:** 10 requests/hour
- **Basic tier:** 100 requests/hour
- **Pro tier:** 1,000 requests/hour
- **Enterprise:** 10,000 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642680000
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "status_code": 400,
    "details": {}
  }
}
```

**Common Error Codes:**
- `UNAUTHORIZED` (401) - Missing or invalid token
- `FORBIDDEN` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `VALIDATION_ERROR` (422) - Invalid request data
- `RATE_LIMIT_EXCEEDED` (429) - Too many requests
- `INTERNAL_ERROR` (500) - Server error

## SDKs and Client Libraries

### Python

```python
import requests

base_url = "http://localhost:8000"
token = "your_jwt_token"

headers = {"Authorization": f"Bearer {token}"}

# Get bots
response = requests.get(f"{base_url}/api/bots", headers=headers)
bots = response.json()
```

### JavaScript/TypeScript

```typescript
const baseUrl = 'http://localhost:8000';
const token = 'your_jwt_token';

const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Get bots
const response = await fetch(`${baseUrl}/api/bots`, { headers });
const bots = await response.json();
```

## Complete API Reference

For complete API documentation with all endpoints, parameters, and examples:

1. **Interactive Docs:** Visit `http://localhost:8000/docs` when server is running
2. **OpenAPI JSON:** See `docs/openapi.json` (auto-generated)
3. **ReDoc:** Visit `http://localhost:8000/redoc` for alternative docs

## Related Documentation

- [Architecture Guide](architecture.md) - System architecture
- [Installation Guide](installation.md) - Setup instructions
- [Deployment Guide](deployment.md) - Production deployment

