# CryptoOrchestrator API Reference

## Overview

This document provides comprehensive API documentation for the CryptoOrchestrator trading platform. The API is built with FastAPI and follows RESTful principles with automatic OpenAPI/Swagger documentation generation.

## Base URL
```
http://localhost:8000/api
```

## Authentication

All protected endpoints require JWT authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /api/auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Trading Bots API

### GET /api/bots/
Get all trading bots for the authenticated user.

**Response:**
```json
[
  {
    "id": "bot_123",
    "name": "BTC Swing Trader",
    "tradingPair": "BTC/USD",
    "strategy": "ml_adaptive",
    "mode": "paper",
    "status": "stopped",
    "createdAt": "2024-01-15T10:30:00Z"
  }
]
```

### POST /api/bots/
Create a new trading bot.

**Request Body:**
```json
{
  "name": "ETH Momentum Bot",
  "tradingPair": "ETH/USD",
  "strategy": "momentum",
  "mode": "paper",
  "riskPerTrade": 2.0,
  "stopLoss": 3.0,
  "takeProfit": 6.0,
  "indicators": ["RSI", "MACD", "BollingerBands"]
}
```

### POST /api/bots/{bot_id}/start
Start a trading bot.

**Response:**
```json
{
  "success": true,
  "message": "Bot started successfully",
  "botId": "bot_123"
}
```

### POST /api/bots/{bot_id}/stop
Stop a trading bot.

**Response:**
```json
{
  "success": true,
  "message": "Bot stopped successfully",
  "botId": "bot_123"
}
```

## Market Data API

### GET /api/markets/
Get all available trading pairs.

**Query Parameters:**
- `exchange` (optional): Filter by exchange (kraken, binance, etc.)

**Response:**
```json
[
  {
    "symbol": "BTC/USD",
    "baseAsset": "BTC",
    "quoteAsset": "USD",
    "price": 45000.50,
    "change24h": 2.5,
    "volume24h": 1234567.89
  }
]
```

### GET /api/markets/{pair}/ohlcv
Get OHLCV (Open, High, Low, Close, Volume) data for a trading pair.

**Query Parameters:**
- `timeframe`: 1m, 5m, 15m, 1h, 4h, 1d
- `limit`: Number of candles (max 1000)
- `startTime`: ISO 8601 timestamp

**Response:**
```json
[
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "open": 44500.00,
    "high": 45200.00,
    "low": 44400.00,
    "close": 45000.50,
    "volume": 123.45
  }
]
```

### GET /api/markets/{pair}/price
Get current price for a trading pair.

**Response:**
```json
{
  "symbol": "BTC/USD",
  "price": 45000.50,
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "kraken"
}
```

## Trading API

### GET /api/trades/
Get trading history with optional filtering.

**Query Parameters:**
- `botId`: Filter by specific bot
- `mode`: paper or live
- `startDate`: ISO 8601 timestamp
- `endDate`: ISO 8601 timestamp
- `limit`: Number of results (max 1000)

**Response:**
```json
[
  {
    "id": "trade_456",
    "botId": "bot_123",
    "symbol": "BTC/USD",
    "side": "buy",
    "amount": 0.01,
    "price": 45000.50,
    "timestamp": "2024-01-15T10:30:00Z",
    "mode": "paper",
    "pnl": 0.0
  }
]
```

### POST /api/trades/
Execute a new trade (admin/manual override).

**Request Body:**
```json
{
  "botId": "bot_123",
  "symbol": "BTC/USD",
  "side": "buy",
  "amount": 0.01,
  "price": 44500.00,
  "mode": "paper"
}
```

## Analytics API

### GET /api/analytics/summary
Get overall analytics summary.

**Response:**
```json
{
  "totalBots": 5,
  "activeBots": 3,
  "totalTrades": 1247,
  "totalPnL": 1250.75,
  "winRate": 0.62,
  "bestPerformingBot": {
    "id": "bot_123",
    "name": "BTC Swing Trader",
    "pnl": 450.25
  }
}
```

### GET /api/analytics/performance
Get detailed performance metrics.

**Query Parameters:**
- `botId`: Filter by specific bot
- `period`: 1d, 7d, 30d, 90d

**Response:**
```json
{
  "sharpeRatio": 1.85,
  "sortinoRatio": 2.12,
  "maxDrawdown": -8.5,
  "winRate": 0.62,
  "profitFactor": 1.45,
  "totalReturn": 12.5,
  "volatility": 0.15
}
```

### GET /api/analytics/risk
Get portfolio risk metrics.

**Response:**
```json
{
  "valueAtRisk": 1250.00,
  "expectedShortfall": 1800.00,
  "beta": 1.2,
  "correlationMatrix": {...},
  "stressTestResults": {...}
}
```

## Portfolio API

### GET /api/portfolio/{mode}
Get portfolio information for paper or live trading.

**Path Parameters:**
- `mode`: paper or live

**Response:**
```json
{
  "totalValue": 15000.00,
  "availableBalance": 5000.00,
  "positions": [
    {
      "symbol": "BTC/USD",
      "amount": 0.25,
      "avgPrice": 44000.00,
      "currentPrice": 45000.00,
      "pnl": 250.00,
      "pnlPercent": 2.27
    }
  ],
  "performance": {
    "daily": 1.2,
    "weekly": 3.5,
    "monthly": 8.7
  }
}
```

## Backtesting API

### POST /api/backtesting/run
Run a backtest for a bot configuration.

**Request Body:**
```json
{
  "botConfig": {
    "name": "Backtest Bot",
    "tradingPair": "BTC/USD",
    "strategy": "ml_adaptive",
    "riskPerTrade": 2.0
  },
  "startDate": "2024-01-01T00:00:00Z",
  "endDate": "2024-01-31T23:59:59Z",
  "initialBalance": 10000.00
}
```

**Response:**
```json
{
  "id": "backtest_789",
  "status": "completed",
  "summary": {
    "totalReturn": 15.5,
    "sharpeRatio": 1.8,
    "maxDrawdown": -12.3,
    "winRate": 0.58,
    "totalTrades": 156
  },
  "trades": [...],
  "performance": {...}
}
```

### GET /api/backtesting/results
Get saved backtest results.

**Query Parameters:**
- `limit`: Number of results
- `strategy`: Filter by strategy

## Preferences API

### GET /api/preferences/
Get user preferences.

**Response:**
```json
{
  "theme": "dark",
  "language": "en",
  "notifications": {
    "email": true,
    "push": true,
    "tradeAlerts": true
  },
  "riskSettings": {
    "maxPositionSize": 10,
    "maxDrawdown": 20
  }
}
```

### PUT /api/preferences/
Update user preferences.

**Request Body:**
```json
{
  "theme": "light",
  "notifications": {
    "tradeAlerts": false
  }
}
```

## Notifications API

### GET /api/notifications/
Get user notifications with filtering.

**Query Parameters:**
- `category`: trade, system, alert
- `read`: true/false
- `limit`: Number of results

**Response:**
```json
[
  {
    "id": "notif_123",
    "type": "trade",
    "title": "Trade Executed",
    "message": "BTC/USD buy order filled at $45,000",
    "timestamp": "2024-01-15T10:30:00Z",
    "read": false
  }
]
```

### PATCH /api/notifications/{notification_id}/read
Mark notification as read.

## Integrations API

### GET /api/integrations/
List all available integrations.

**Response:**
```json
[
  {
    "name": "freqtrade",
    "status": "active",
    "description": "FreqTrade strategy integration"
  },
  {
    "name": "jesse",
    "status": "inactive",
    "description": "Jesse framework integration"
  }
]
```

### POST /api/integrations/{name}/start
Start an integration adapter.

### GET /api/integrations/{name}/status
Get status of specific integration.

## Recommendations API

### GET /api/recommendations/
Get AI-powered trading recommendations.

**Response:**
```json
{
  "pairAnalysis": [
    {
      "symbol": "BTC/USD",
      "confidence": 0.85,
      "signal": "BUY",
      "reasoning": "Strong upward momentum with RSI divergence"
    }
  ],
  "optimalRiskSettings": {
    "positionSize": 2.5,
    "stopLoss": 3.0,
    "takeProfit": 6.0
  }
}
```

## Health Check API

### GET /api/health/
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": 3600.0,
  "version": "1.0.0"
}
```

### GET /api/health/detailed
Detailed health check with system metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": 3600.0,
  "version": "1.0.0",
  "system_metrics": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_usage": {...}
  },
  "services": [
    {
      "service": "ml_engine",
      "status": "healthy",
      "response_time": 12.5
    }
  ]
}
```

## WebSocket Endpoints

### WS /ws/market-data
Real-time market data streaming.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market-data');
```

**Subscribe Message:**
```json
{
  "type": "subscribe",
  "symbols": ["BTC/USD", "ETH/USD"]
}
```

**Data Message:**
```json
{
  "type": "price_update",
  "symbol": "BTC/USD",
  "price": 45000.50,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### WS /ws/bot-status
Real-time bot status updates.

### WS /ws/notifications
Real-time user notifications.

### WS /ws/performance-metrics
Real-time performance metrics streaming.

## Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limits

- **Authenticated endpoints**: 100 requests per minute
- **Public market data**: 500 requests per minute
- **WebSocket connections**: 10 concurrent connections per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642252800
```

## Versioning

API versioning is handled through URL prefixes:
- Current version: `/api/` (v1)
- Future versions: `/api/v2/`

## Risk Management API

### GET /api/risk-management/metrics
Get current risk metrics for the authenticated user's portfolio.

**Response:**
```json
{
  "totalExposure": 15000.50,
  "maxDrawdown": 0.08,
  "sharpeRatio": 1.85,
  "valueAtRisk": 1250.00,
  "portfolioVolatility": 0.12,
  "timestamp": "2025-11-08T21:00:00Z"
}
```

### GET /api/risk-management/alerts
Get active risk alerts for the user.

**Response:**
```json
[
  {
    "id": "alert_001",
    "type": "POSITION_SIZE",
    "severity": "high",
    "message": "Position size exceeds 80% of maximum limit",
    "timestamp": "2025-11-08T20:55:00Z",
    "acknowledged": false
  }
]
```

### GET /api/risk-management/limits
Get current risk limits configuration.

**Response:**
```json
{
  "maxPositionSize": 50.00,
  "maxDailyLoss": 5.00,
  "maxDrawdown": 15.00,
  "maxLeverage": 3.0
}
```

### POST /api/risk-management/limits
Update risk limits configuration.

**Request Body:**
```json
{
  "maxPositionSize": 60.00,
  "maxDailyLoss": 7.50,
  "maxDrawdown": 20.00,
  "maxLeverage": 2.5
}
```

**Validation Rules:**
- `maxPositionSize`: 0-100 (percentage)
- `maxDailyLoss`: 0-100 (percentage)
- `maxDrawdown`: 0-100 (percentage)
- `maxLeverage`: 1.0-10.0 (multiplier)

**Response:**
```json
{
  "status": "success",
  "limits": {
    "maxPositionSize": 60.00,
    "maxDailyLoss": 7.50,
    "maxDrawdown": 20.00,
    "maxLeverage": 2.5
  }
}
```

### POST /api/risk-management/alerts/{alert_id}/acknowledge
Acknowledge a risk alert.

**Response:**
```json
{
  "id": "alert_001",
  "acknowledged": true,
  "acknowledgedAt": "2025-11-08T21:05:00Z"
}
```

**Note:** Risk metrics endpoint uses 10-second in-memory caching to optimize performance.

## Authentication Notes

### Rate Limiting
Authentication endpoints are **not rate-limited** during test/development mode to facilitate integration testing. In production deployments with Redis available, rate limiting is enforced (5 requests/minute for auth endpoints, 100 requests/minute for general API).

### Test Isolation
Integration tests use unique email addresses per test run to avoid user collision. The authentication service maintains in-memory storage during testing.

## Data Formats

- All dates use ISO 8601 format: `YYYY-MM-DDTHH:mm:ssZ`
- All monetary values use decimal format with 2-8 decimal places
- All percentages use decimal format (0.01 = 1%)

## SDKs and Libraries

- **Python SDK**: `pip install cryptoorchestrator-sdk`
- **JavaScript SDK**: `npm install @cryptoorchestrator/sdk`

## Support

For API support and questions:
- Documentation: https://docs.cryptoorchestrator.com
- Issues: https://github.com/cryptoorchestrator/api/issues
- Email: api-support@cryptoorchestrator.com

---

*Last updated: 2025-11-08* | *Version: 1.1.0* | *Risk Management API added*