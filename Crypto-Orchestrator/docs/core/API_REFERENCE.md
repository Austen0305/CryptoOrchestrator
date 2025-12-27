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

### Authentication Examples

#### Python (using `requests`)
```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api"

# Login to get token
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "user@example.com",
        "password": "securepassword123"
    }
)
token = login_response.json()["token"]

# Use token for authenticated requests
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Make authenticated API call
response = requests.get(
    f"{BASE_URL}/bots/",
    headers=headers
)
bots = response.json()
```

#### JavaScript/TypeScript (using `fetch`)
```typescript
const BASE_URL = "http://localhost:8000/api";

// Login to get token
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "securepassword123"
  })
});

const { token } = await loginResponse.json();

// Use token for authenticated requests
const headers = {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
};

// Make authenticated API call
const response = await fetch(`${BASE_URL}/bots/`, { headers });
const bots = await response.json();
```

#### cURL
```bash
# Login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }' | jq -r '.token')

# Use token for authenticated requests
curl -X GET http://localhost:8000/api/bots/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

#### React Query Hook Example
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

// Login mutation
const useLogin = () => {
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) throw new Error('Login failed');
      const data = await response.json();
      localStorage.setItem('token', data.token);
      return data;
    },
  });
};

// Authenticated query
const useBots = () => {
  const token = localStorage.getItem('token');
  return useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await fetch('/api/bots/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) throw new Error('Failed to fetch bots');
      return response.json();
    },
  });
};
```

### Token Management

**Token Expiration:**
- Access tokens expire after 24 hours
- Refresh tokens expire after 30 days
- Use the refresh token endpoint to obtain a new access token

**Token Refresh Example:**
```python
# Python
refresh_response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": refresh_token}
)
new_token = refresh_response.json()["token"]
```

```typescript
// TypeScript
const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ refresh_token: refreshToken })
});
const { token } = await refreshResponse.json();
```

### Authorization

**Role-Based Access:**
- **User**: Standard access to own resources
- **Admin**: Full access to all resources and system management

**Checking User Permissions:**
```python
# Python - Check if user is admin
response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
user_data = response.json()
is_admin = user_data.get("role") == "admin"
```

```typescript
// TypeScript - Check if user is admin
const response = await fetch(`${BASE_URL}/auth/me`, {
  headers: { "Authorization": `Bearer ${token}` }
});
const userData = await response.json();
const isAdmin = userData.role === "admin";
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

**Rate Limit:** 1000 requests/hour (authenticated)

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

**Code Examples:**

**Python:**
```python
import requests

response = requests.get(
    f"{BASE_URL}/bots/",
    headers={"Authorization": f"Bearer {token}"}
)
response.raise_for_status()
bots = response.json()
for bot in bots:
    print(f"Bot: {bot['name']} - Status: {bot['status']}")
```

**JavaScript/TypeScript:**
```typescript
const response = await fetch(`${BASE_URL}/bots/`, {
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
});
const bots = await response.json();
bots.forEach(bot => {
  console.log(`Bot: ${bot.name} - Status: ${bot.status}`);
});
```

**cURL:**
```bash
curl -X GET http://localhost:8000/api/bots/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### POST /api/bots/
Create a new trading bot.

**Rate Limit:** 1000 requests/hour (authenticated)

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

**Response:**
```json
{
  "id": "bot_456",
  "name": "ETH Momentum Bot",
  "tradingPair": "ETH/USD",
  "strategy": "momentum",
  "mode": "paper",
  "status": "stopped",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Code Examples:**

**Python:**
```python
import requests

bot_data = {
    "name": "ETH Momentum Bot",
    "tradingPair": "ETH/USD",
    "strategy": "momentum",
    "mode": "paper",
    "riskPerTrade": 2.0,
    "stopLoss": 3.0,
    "takeProfit": 6.0,
    "indicators": ["RSI", "MACD", "BollingerBands"]
}

response = requests.post(
    f"{BASE_URL}/bots/",
    headers={"Authorization": f"Bearer {token}"},
    json=bot_data
)
response.raise_for_status()
bot = response.json()
print(f"Created bot: {bot['id']}")
```

**JavaScript/TypeScript:**
```typescript
const botData = {
  name: "ETH Momentum Bot",
  tradingPair: "ETH/USD",
  strategy: "momentum",
  mode: "paper",
  riskPerTrade: 2.0,
  stopLoss: 3.0,
  takeProfit: 6.0,
  indicators: ["RSI", "MACD", "BollingerBands"]
};

const response = await fetch(`${BASE_URL}/bots/`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(botData)
});

const bot = await response.json();
console.log(`Created bot: ${bot.id}`);
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/bots/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ETH Momentum Bot",
    "tradingPair": "ETH/USD",
    "strategy": "momentum",
    "mode": "paper",
    "riskPerTrade": 2.0,
    "stopLoss": 3.0,
    "takeProfit": 6.0,
    "indicators": ["RSI", "MACD", "BollingerBands"]
  }'
```

**Error Responses:**
- `400 Bad Request`: Invalid bot configuration
- `401 Unauthorized`: Authentication required
- `422 Unprocessable Entity`: Validation error (missing required fields)

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
- `chain_id` (optional): Filter by blockchain network (1=Ethereum, 8453=Base, etc.)

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

## Logs API

Administrative endpoints for searching, analyzing, and managing application logs. All endpoints require admin role.

### GET /api/logs/search

Search application logs with various filters.

**Query Parameters:**
- `query` (optional): Text search query
- `level` (optional): Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `user_id` (optional): Filter by user ID
- `request_id` (optional): Filter by request ID
- `trace_id` (optional): Filter by trace ID
- `start_time` (optional): Start time for time range filter (ISO 8601)
- `end_time` (optional): End time for time range filter (ISO 8601)
- `log_file` (default: "app"): Log file to search (app, errors, audit)
- `limit` (default: 100, max: 1000): Maximum number of results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "results": [
    {
      "timestamp": "2025-12-06T10:30:00Z",
      "level": "ERROR",
      "message": "Failed to execute trade",
      "user_id": "user_123",
      "request_id": "req_456",
      "trace_id": "trace_789",
      "module": "server_fastapi.routes.trades",
      "line": 234
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

**Example:**
```python
# Search for errors in the last hour
from datetime import datetime, timedelta

end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

response = requests.get(
    f"{BASE_URL}/logs/search",
    headers=headers,
    params={
        "level": "ERROR",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "limit": 50
    }
)
```

### GET /api/logs/statistics

Get log statistics for a time range.

**Query Parameters:**
- `start_time` (optional): Start time for statistics (ISO 8601)
- `end_time` (optional): End time for statistics (ISO 8601)
- `log_file` (default: "app"): Log file to analyze (app, errors, audit)

**Response:**
```json
{
  "total_logs": 12500,
  "by_level": {
    "DEBUG": 8000,
    "INFO": 3500,
    "WARNING": 800,
    "ERROR": 180,
    "CRITICAL": 20
  },
  "error_rate": 0.016,
  "time_range": {
    "start": "2025-12-06T09:00:00Z",
    "end": "2025-12-06T10:00:00Z"
  }
}
```

### GET /api/logs/tail

Get the last N lines from a log file (similar to `tail -n`).

**Query Parameters:**
- `log_file` (default: "app"): Log file to tail (app, errors, audit)
- `lines` (default: 50, max: 1000): Number of lines to return

**Response:**
```json
[
  {
    "timestamp": "2025-12-06T10:35:00Z",
    "level": "INFO",
    "message": "Bot started successfully",
    "user_id": "user_123"
  }
]
```

## Alerting & Incident Management API

Administrative endpoints for managing alerts, alert rules, and incidents. All endpoints require admin role.

### GET /api/alerting/alerts

Get active alerts.

**Query Parameters:**
- `severity` (optional): Filter by severity (low, medium, high, critical)

**Response:**
```json
[
  {
    "id": "alert_123",
    "rule_name": "high_error_rate",
    "metric": "error_rate",
    "current_value": 0.05,
    "threshold": 0.02,
    "severity": "high",
    "message": "Error rate exceeded threshold",
    "timestamp": "2025-12-06T10:30:00Z",
    "acknowledged": false,
    "resolved": false,
    "metadata": {}
  }
]
```

### GET /api/alerting/alerts/history

Get alert history.

**Query Parameters:**
- `limit` (default: 100, max: 1000): Maximum number of alerts
- `severity` (optional): Filter by severity

**Response:**
```json
[
  {
    "id": "alert_456",
    "rule_name": "slow_query_detected",
    "metric": "query_duration",
    "current_value": 250.5,
    "threshold": 200.0,
    "severity": "medium",
    "timestamp": "2025-12-06T09:15:00Z",
    "acknowledged": true,
    "resolved": true
  }
]
```

### POST /api/alerting/alerts/{alert_id}/acknowledge

Acknowledge an alert.

**Response:**
```json
{
  "success": true,
  "message": "Alert acknowledged"
}
```

### POST /api/alerting/alerts/{rule_name}/resolve

Resolve an active alert by rule name.

**Response:**
```json
{
  "success": true,
  "message": "Alert for rule 'high_error_rate' resolved"
}
```

### GET /api/alerting/rules

Get all alert rules.

**Response:**
```json
[
  {
    "name": "high_error_rate",
    "metric": "error_rate",
    "threshold": 0.02,
    "operator": "gt",
    "severity": "high",
    "channels": ["email", "slack"],
    "duration": 60,
    "cooldown": 300,
    "last_triggered": "2025-12-06T10:30:00Z",
    "trigger_count": 5
  }
]
```

### POST /api/alerting/rules

Create a new alert rule.

**Request Body:**
```json
{
  "name": "slow_endpoint",
  "metric": "endpoint_duration",
  "threshold": 1000.0,
  "operator": "gt",
  "severity": "medium",
  "channels": ["email"],
  "duration": 120,
  "cooldown": 600
}
```

**Response:**
```json
{
  "success": true,
  "rule": "slow_endpoint"
}
```

### GET /api/alerting/fatigue-stats

Get alert fatigue statistics.

**Response:**
```json
{
  "total_alerts_24h": 150,
  "alerts_by_severity": {
    "critical": 5,
    "high": 20,
    "medium": 50,
    "low": 75
  },
  "fatigue_score": 0.65,
  "most_frequent_rules": [
    {
      "rule_name": "high_error_rate",
      "count": 25
    }
  ]
}
```

### GET /api/alerting/incidents

Get active incidents.

**Query Parameters:**
- `severity` (optional): Filter by severity

**Response:**
```json
[
  {
    "id": "incident_789",
    "title": "Database Connection Pool Exhausted",
    "severity": "critical",
    "status": "open",
    "created_at": "2025-12-06T10:00:00Z",
    "updated_at": "2025-12-06T10:15:00Z",
    "resolved_at": null,
    "assigned_to": "admin@example.com",
    "related_alerts": ["alert_123", "alert_456"],
    "metadata": {
      "pool_size": 0,
      "max_pool_size": 20
    }
  }
]
```

### GET /api/alerting/incidents/{incident_id}

Get incident details.

**Response:**
```json
{
  "id": "incident_789",
  "title": "Database Connection Pool Exhausted",
  "severity": "critical",
  "status": "open",
  "created_at": "2025-12-06T10:00:00Z",
  "updated_at": "2025-12-06T10:15:00Z",
  "resolved_at": null,
  "assigned_to": "admin@example.com",
  "related_alerts": ["alert_123", "alert_456"],
  "metadata": {},
  "timeline": [
    {
      "timestamp": "2025-12-06T10:00:00Z",
      "event": "incident_created",
      "user": "system"
    }
  ]
}
```

### POST /api/alerting/incidents

Create a new incident.

**Request Body:**
```json
{
  "title": "Service Degradation Detected",
  "severity": "high",
  "description": "API response times increased by 200%",
  "related_alerts": ["alert_123"]
}
```

**Response:**
```json
{
  "id": "incident_790",
  "title": "Service Degradation Detected",
  "status": "open",
  "created_at": "2025-12-06T10:30:00Z"
}
```

### POST /api/alerting/incidents/{incident_id}/resolve

Resolve an incident.

**Response:**
```json
{
  "success": true,
  "message": "Incident resolved",
  "resolved_at": "2025-12-06T10:45:00Z"
}
```

## Database Performance API

Administrative endpoints for monitoring database performance, connection pools, and query optimization. All endpoints require admin role.

### GET /api/database/pool/metrics

Get connection pool metrics.

**Response:**
```json
{
  "pool_size": 10,
  "active_connections": 7,
  "idle_connections": 3,
  "max_pool_size": 20,
  "utilization_percent": 35.0,
  "wait_time_avg_ms": 2.5,
  "connection_errors": 0
}
```

### GET /api/database/pool/health

Get connection pool health status.

**Response:**
```json
{
  "status": "healthy",
  "warnings": [],
  "recommendations": [
    "Pool utilization is optimal"
  ],
  "metrics": {
    "utilization_percent": 35.0,
    "wait_time_avg_ms": 2.5
  }
}
```

### GET /api/database/pool/history

Get connection pool metrics history.

**Query Parameters:**
- `limit` (default: 100, max: 1000): Number of historical entries

**Response:**
```json
{
  "history": [
    {
      "timestamp": "2025-12-06T10:00:00Z",
      "pool_size": 10,
      "active_connections": 7,
      "utilization_percent": 35.0
    }
  ],
  "summary": {
    "avg_utilization": 32.5,
    "max_utilization": 45.0,
    "min_utilization": 20.0
  }
}
```

### GET /api/database/read-replicas/health

Get read replica health status.

**Response:**
```json
{
  "read_replicas_enabled": true,
  "read_replica_count": 2,
  "health": {
    "replica_1": {
      "status": "healthy",
      "lag_seconds": 0.5
    },
    "replica_2": {
      "status": "healthy",
      "lag_seconds": 1.2
    }
  }
}
```

### GET /api/database/indexes/usage

Analyze index usage for a table (PostgreSQL only).

**Query Parameters:**
- `table_name` (required): Table name to analyze

**Response:**
```json
{
  "table_name": "trades",
  "indexes": [
    {
      "index_name": "idx_trades_user_id",
      "scans": 12500,
      "tuples_read": 250000,
      "tuples_fetched": 250000,
      "size_bytes": 1048576
    }
  ]
}
```

### GET /api/database/indexes/unused

Find unused or rarely used indexes (PostgreSQL only).

**Query Parameters:**
- `min_scans` (default: 10): Minimum scans to consider index as used

**Response:**
```json
[
  {
    "index_name": "idx_old_table_column",
    "table_name": "old_table",
    "scans": 2,
    "size_bytes": 524288,
    "recommendation": "Consider dropping this index"
  }
]
```

### GET /api/database/indexes/missing

Find potential missing indexes (PostgreSQL only).

**Response:**
```json
[
  {
    "table_name": "trades",
    "column_name": "executed_at",
    "query_count": 5000,
    "avg_query_time_ms": 150.0,
    "recommendation": "Consider adding index on executed_at"
  }
]
```

## Cache Management API

Administrative endpoints for managing cache, viewing analytics, and controlling versioning. All endpoints require admin role.

### GET /api/cache/analytics

Get cache analytics and performance metrics.

**Query Parameters:**
- `time_window_minutes` (optional): Time window for statistics

**Response:**
```json
{
  "hit_rate": 0.85,
  "miss_rate": 0.15,
  "total_operations": 10000,
  "avg_response_time_ms": 2.5,
  "memory_hits": 7000,
  "redis_hits": 1500,
  "misses": 1500,
  "evictions": 50,
  "total_size_bytes": 104857600
}
```

### GET /api/cache/analytics/pattern/{pattern}

Get analytics for a specific cache pattern.

**Path Parameters:**
- `pattern`: Cache key pattern (e.g., "bots:*", "portfolio:*")

**Response:**
```json
{
  "pattern": "bots:*",
  "hit_rate": 0.92,
  "operations": 5000,
  "avg_response_time_ms": 1.8,
  "size_bytes": 52428800
}
```

### GET /api/cache/versions

Get all cache versions.

**Response:**
```json
{
  "versions": {
    "bots": 5,
    "portfolio": 3,
    "trades": 2
  }
}
```

### POST /api/cache/versions/{prefix}/increment

Increment cache version for a prefix (invalidates all cached data).

**Path Parameters:**
- `prefix`: Cache prefix (e.g., "bots", "portfolio")

**Query Parameters:**
- `reason` (optional): Reason for version increment

**Response:**
```json
{
  "success": true,
  "prefix": "bots",
  "new_version": 6,
  "message": "Cache version incremented to v6"
}
```

### POST /api/cache/versions/invalidate-all

Invalidate all cache versions (full cache clear).

**Query Parameters:**
- `reason` (optional): Reason for invalidation

**Response:**
```json
{
  "success": true,
  "message": "All cache versions invalidated"
}
```

### GET /api/cache/preloader/stats

Get predictive preloader statistics.

**Response:**
```json
{
  "total_accesses": 50000,
  "unique_keys": 1000,
  "frequently_accessed": [
    {
      "key": "bots:user_123",
      "access_count": 500,
      "last_accessed": "2025-12-06T10:30:00Z"
    }
  ],
  "preload_success_rate": 0.85
}
```

### POST /api/cache/preloader/preload-frequent

Manually trigger preloading of frequently accessed keys.

**Query Parameters:**
- `min_access_count` (default: 10): Minimum access count
- `time_window_minutes` (default: 60): Time window in minutes

**Response:**
```json
{
  "success": true,
  "message": "Preload triggered",
  "stats": {
    "keys_preloaded": 25,
    "total_accesses": 50000
  }
}
```

### GET /api/cache/metrics

Get cache metrics from MultiLevelCache.

**Response:**
```json
{
  "hits": 8500,
  "misses": 1500,
  "memory_hits": 7000,
  "redis_hits": 1500,
  "evictions": 50,
  "total_size_bytes": 104857600,
  "hit_rate": 0.85
}
```

### POST /api/cache/analytics/reset

Reset cache analytics statistics.

**Response:**
```json
{
  "success": true,
  "message": "Cache analytics reset"
}
```

## Background Jobs API

Administrative endpoints for monitoring and managing Celery background jobs. All endpoints require admin role.

### GET /api/background-jobs/status

Get overall background jobs status.

**Response:**
```json
{
  "celery_available": true,
  "active_workers": 3,
  "pending_tasks": 15,
  "completed_tasks_24h": 5000,
  "failed_tasks_24h": 25
}
```

### GET /api/background-jobs/tasks

Get active tasks.

**Response:**
```json
[
  {
    "job_id": "task_123",
    "status": "started",
    "task_name": "tasks.update_market_data",
    "created_at": "2025-12-06T10:30:00Z",
    "started_at": "2025-12-06T10:30:05Z",
    "progress": 0.65
  }
]
```

### GET /api/background-jobs/stats

Get job statistics.

**Response:**
```json
{
  "task_statistics": {
    "total_tasks": 10000,
    "successful_tasks": 9950,
    "failed_tasks": 50,
    "avg_execution_time_ms": 125.5
  },
  "queue_metrics": {
    "high_priority": 5,
    "normal_priority": 10,
    "low_priority": 0
  },
  "timestamp": "2025-12-06T10:35:00Z"
}
```

### GET /api/background-jobs/queue-depth

Get queue depth for each priority queue.

**Response:**
```json
{
  "high_priority": 5,
  "normal_priority": 10,
  "low_priority": 0
}
```

### GET /api/background-jobs/batching/stats

Get task batching statistics.

**Response:**
```json
{
  "batches": {
    "batch_1": {
      "task_count": 10,
      "created_at": "2025-12-06T10:30:00Z",
      "status": "pending"
    }
  },
  "timestamp": "2025-12-06T10:35:00Z"
}
```

### POST /api/background-jobs/batching/flush

Flush all pending batches.

**Response:**
```json
{
  "success": true,
  "results": {
    "batch_1": {
      "tasks_executed": 10,
      "status": "completed"
    }
  },
  "timestamp": "2025-12-06T10:35:00Z"
}
```

### GET /api/background-jobs/rate-limits

Get rate limit status for tasks.

**Query Parameters:**
- `task_name` (optional): Filter by task name

**Response:**
```json
{
  "rate_limits": [
    {
      "task_name": "tasks.update_market_data",
      "rate_limited": true,
      "max_calls": 100,
      "time_window_seconds": 60,
      "current_calls": 45,
      "remaining_calls": 55,
      "reset_after_seconds": 15
    }
  ]
}
```

### POST /api/background-jobs/rate-limits/{task_name}/reset

Reset rate limit history for a task.

**Path Parameters:**
- `task_name`: Task name to reset

**Response:**
```json
{
  "success": true,
  "message": "Rate limit reset for tasks.update_market_data"
}
```

## Push Notifications API

Endpoints for managing push notification subscriptions.

### POST /api/notifications/subscribe

Subscribe user to push notifications.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "base64_encoded_key",
    "auth": "base64_encoded_auth"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Push notifications subscribed successfully"
}
```

**Example (JavaScript):**
```typescript
// Get push subscription from browser
const registration = await navigator.serviceWorker.ready;
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
});

// Subscribe to backend
await fetch('/api/notifications/subscribe', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    endpoint: subscription.endpoint,
    keys: {
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth'))
    }
  })
});
```

### POST /api/notifications/unsubscribe

Unsubscribe user from push notifications.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Push notifications unsubscribed successfully"
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

All endpoints return standardized error responses with consistent structure:

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "classification": "user_error",
    "suggestion": "Helpful suggestion for resolving the error",
    "details": {
      "field": "email",
      "message": "Invalid email format",
      "type": "value_error"
    }
  },
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Classifications

- **`user_error`**: Client-side error (4xx) - Invalid input, missing data, etc.
- **`system_error`**: Server-side error (5xx) - Internal failures, database errors, etc.
- **`security_error`**: Authentication/authorization failures (401, 403, 429)

### Complete Error Code Reference

#### 4xx Client Errors

| Status Code | Error Code | Description | Example |
|------------|------------|-------------|---------|
| 400 | `VALIDATION_ERROR` | Request validation failed | Invalid email format |
| 400 | `INSUFFICIENT_BALANCE` | Insufficient balance for operation | Not enough funds for trade |
| 400 | `INVALID_SYMBOL` | Invalid trading symbol | Symbol "XYZ/USD" not found |
| 400 | `BOT_ALREADY_ACTIVE` | Bot is already running | Cannot start bot that's already active |
| 400 | `BOT_NOT_ACTIVE` | Bot is not running | Cannot stop bot that's not active |
| 400 | `MFA_NOT_ENABLED` | Multi-factor authentication not enabled | 2FA required but not set up |
| 400 | `INVALID_MFA_TOKEN` | Invalid or expired MFA token | 2FA code incorrect or expired |
| 400 | `WITHDRAWAL_LIMIT_EXCEEDED` | Daily/weekly withdrawal limit exceeded | Exceeded $10,000 daily limit |
| 400 | `ADDRESS_NOT_WHITELISTED` | Withdrawal address not whitelisted | Address must be whitelisted 24h before use |
| 400 | `PRICE_IMPACT_TOO_HIGH` | DEX swap price impact exceeds threshold | Price impact >5% rejected |
| 401 | `AUTHENTICATION_ERROR` | Authentication required or failed | Invalid or expired token |
| 401 | `INVALID_CREDENTIALS` | Invalid email/password | Login credentials incorrect |
| 401 | `TOKEN_EXPIRED` | JWT token has expired | Token expired, refresh required |
| 401 | `INVALID_TOKEN` | JWT token is invalid | Malformed or invalid token |
| 401 | `INVALID_REFRESH_TOKEN` | Refresh token is invalid | Refresh token expired or invalid |
| 403 | `AUTHORIZATION_ERROR` | Insufficient permissions | User lacks required role |
| 403 | `ADMIN_ACCESS_REQUIRED` | Admin role required | Endpoint requires admin privileges |
| 404 | `NOT_FOUND` | Resource not found | Bot with ID "bot_123" not found |
| 409 | `INTEGRITY_ERROR` | Database integrity constraint violated | User already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Request format valid but semantically incorrect | Invalid date format |

#### 5xx Server Errors

| Status Code | Error Code | Description | Example |
|------------|------------|-------------|---------|
| 500 | `INTERNAL_ERROR` | Unexpected server error | Unhandled exception occurred |
| 500 | `DATABASE_ERROR` | Database operation failed | Connection timeout |
| 500 | `TRADING_ERROR` | Trading operation failed | Order execution error |
| 502 | `ORDER_EXECUTION_FAILED` | Order execution failed on blockchain | Transaction failed or reverted |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable | Blockchain RPC or DEX aggregator API down |
| 503 | `BLOCKCHAIN_RPC_ERROR` | Cannot connect to blockchain RPC | RPC provider unavailable |
| 503 | `DEX_AGGREGATOR_UNAVAILABLE` | All DEX aggregators unavailable | 0x, OKX, Rubic all down |

### Error Handling Examples

#### Python Error Handling
```python
import requests

try:
    response = requests.post(
        f"{BASE_URL}/bots/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "My Bot", "symbol": "BTC/USD"}
    )
    response.raise_for_status()
    bot = response.json()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    error_code = error_data["error"]["code"]
    error_message = error_data["error"]["message"]
    
    if error_code == "VALIDATION_ERROR":
        print(f"Validation failed: {error_message}")
        print(f"Details: {error_data['error'].get('details', {})}")
    elif error_code == "AUTHENTICATION_ERROR":
        print("Token expired, refreshing...")
        # Refresh token logic
    else:
        print(f"Error {error_code}: {error_message}")
```

#### JavaScript/TypeScript Error Handling
```typescript
async function createBot(botData: CreateBotRequest) {
  try {
    const response = await fetch(`${BASE_URL}/bots/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(botData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      const { code, message, suggestion } = errorData.error;
      
      switch (code) {
        case "VALIDATION_ERROR":
          console.error(`Validation failed: ${message}`);
          console.error("Details:", errorData.error.details);
          break;
        case "AUTHENTICATION_ERROR":
          console.error("Token expired, refreshing...");
          await refreshToken();
          break;
        case "NOT_FOUND":
          console.error(`Resource not found: ${message}`);
          break;
        default:
          console.error(`Error ${code}: ${message}`);
          if (suggestion) console.info(`Suggestion: ${suggestion}`);
      }
      throw new Error(message);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to create bot:", error);
    throw error;
  }
}
```

#### React Query Error Handling
```typescript
import { useMutation } from '@tanstack/react-query';

const useCreateBot = () => {
  return useMutation({
    mutationFn: async (botData: CreateBotRequest) => {
      const response = await fetch('/api/bots/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(botData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        const error = new Error(errorData.error.message);
        (error as any).code = errorData.error.code;
        (error as any).details = errorData.error.details;
        throw error;
      }
      
      return response.json();
    },
    onError: (error: any) => {
      if (error.code === 'AUTHENTICATION_ERROR') {
        // Refresh token and retry
        refreshToken();
      } else if (error.code === 'VALIDATION_ERROR') {
        // Show validation errors to user
        showValidationErrors(error.details);
      }
    }
  });
};
```

### Request ID Tracking

Every API request includes a unique `request_id` in error responses for debugging:

```python
# Python - Include request ID in support requests
error_data = response.json()
request_id = error_data.get("request_id")
print(f"Request ID for support: {request_id}")
```

```typescript
// TypeScript - Include request ID in error logs
const errorData = await response.json();
const requestId = errorData.request_id;
console.error(`Error request ID: ${requestId}`);
// Include in support ticket
```

## Rate Limits

Rate limiting is enforced per endpoint and user tier to prevent abuse and ensure fair usage. Rate limits are applied using distributed rate limiting (Redis-backed) with in-memory fallback.

### Rate Limit Headers

All responses include rate limit information in headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642252800
Retry-After: 60
```

**Header Descriptions:**
- `X-RateLimit-Limit`: Maximum requests allowed in the time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `Retry-After`: Seconds to wait before retrying (only on 429 responses)

### Default Rate Limits

| User Type | Limit | Window | Description |
|-----------|-------|--------|-------------|
| **Authenticated Users** | 1000 | 1 hour | Standard authenticated endpoints |
| **Anonymous Users** | 100 | 1 hour | Public endpoints without authentication |
| **Admin Users** | Unlimited | - | Admin endpoints bypass rate limits |

### Tier-Based Rate Limits

Rate limits are multiplied based on subscription tier:

| Tier | Multiplier | Example (Base: 1000/hour) |
|------|------------|---------------------------|
| Free | 1.0x | 1,000 requests/hour |
| Basic | 1.5x | 1,500 requests/hour |
| Pro | 2.0x | 2,000 requests/hour |
| Enterprise | 3.0x | 3,000 requests/hour |
| Mega | 5.0x | 5,000 requests/hour |

### Endpoint-Specific Rate Limits

Some endpoints have stricter rate limits for security and resource management:

| Endpoint | Limit | Window | Reason |
|----------|-------|--------|--------|
| `/api/auth/login` | 5 | 1 minute | Prevent brute force attacks |
| `/api/auth/register` | 5 | 1 minute | Prevent spam registrations |
| `/api/integrations/predict` | 20 | 1 minute | ML model resource intensive |
| `/api/backtesting/run` | 10 | 1 minute | CPU-intensive operations |
| `/api/analytics/advanced` | 50 | 1 minute | Complex analytics queries |
| `/api/wallets` | 100 | 1 hour | Wallet operations |
| `/api/wallets/refresh-balances` | 20 | 1 hour | Balance refresh operations |
| `/api/wallets/{id}/withdraw` | 10 | 1 hour | Security: prevent rapid withdrawals |
| `/api/dex/quote` | 60 | 1 minute | DEX quote requests |
| `/api/dex/swap` | 20 | 1 hour | Security: prevent rapid swaps |
| `/api/dex/trades/{id}/status` | 100 | 1 minute | Status check polling |

### Rate Limit Response (429)

When rate limit is exceeded, the API returns:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please wait before retrying.",
    "status_code": 429,
    "classification": "security_error",
    "suggestion": "Too many requests. Please wait a moment and try again."
  },
  "status_code": 429,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**HTTP Headers:**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642252800
Retry-After: 60
```

### Rate Limit Handling Examples

#### Python - Handle Rate Limits
```python
import requests
import time

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            # Rate limit exceeded
            retry_after = int(response.headers.get("Retry-After", 60))
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            
            print(f"Rate limit exceeded. Waiting {retry_after} seconds...")
            print(f"Rate limit resets at: {reset_time}")
            
            time.sleep(retry_after)
            continue
        
        response.raise_for_status()
        return response.json()
    
    raise Exception("Max retries exceeded")
```

#### JavaScript/TypeScript - Handle Rate Limits
```typescript
async function makeRequestWithRetry(
  url: string,
  options: RequestInit,
  maxRetries = 3
): Promise<Response> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = await fetch(url, options);
    
    if (response.status === 429) {
      // Rate limit exceeded
      const retryAfter = parseInt(
        response.headers.get("Retry-After") || "60"
      );
      const resetTime = parseInt(
        response.headers.get("X-RateLimit-Reset") || "0"
      );
      
      console.log(`Rate limit exceeded. Waiting ${retryAfter} seconds...`);
      console.log(`Rate limit resets at: ${new Date(resetTime * 1000)}`);
      
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      continue;
    }
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response;
  }
  
  throw new Error("Max retries exceeded");
}
```

#### React Query - Automatic Retry with Rate Limit Handling
```typescript
import { useQuery } from '@tanstack/react-query';

const useBots = () => {
  return useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await fetch('/api/bots/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.status === 429) {
        const retryAfter = parseInt(
          response.headers.get("Retry-After") || "60"
        );
        // Wait before retrying
        await new Promise(resolve => 
          setTimeout(resolve, retryAfter * 1000)
        );
        // Retry the request
        return fetch('/api/bots/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }).then(r => r.json());
      }
      
      if (!response.ok) {
        throw new Error('Failed to fetch bots');
      }
      
      return response.json();
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 429, handle it in queryFn
      if (error?.status === 429) return false;
      return failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  });
};
```

### Monitoring Rate Limits

**Check Rate Limit Status:**
```python
# Python
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
limit = response.headers.get("X-RateLimit-Limit")
remaining = response.headers.get("X-RateLimit-Remaining")
reset = response.headers.get("X-RateLimit-Reset")

print(f"Limit: {limit}, Remaining: {remaining}, Resets: {reset}")
```

```typescript
// TypeScript
const response = await fetch(`${BASE_URL}/bots/`, { headers });
const limit = response.headers.get("X-RateLimit-Limit");
const remaining = response.headers.get("X-RateLimit-Remaining");
const reset = response.headers.get("X-RateLimit-Reset");

console.log(`Limit: ${limit}, Remaining: ${remaining}, Resets: ${reset}`);
```

### Exempt Endpoints

The following endpoints are exempt from rate limiting:
- `/health` - Health check endpoint
- `/docs` - API documentation
- `/redoc` - Alternative API documentation
- `/openapi.json` - OpenAPI specification
- `/favicon.ico` - Favicon requests

## API Versioning

API versioning ensures backward compatibility while allowing evolution of the API. Versioning is handled through URL prefixes and request headers.

### Version Strategy

**URL-Based Versioning (Primary):**
- Current version: `/api/` (v1, default)
- Future versions: `/api/v2/`, `/api/v3/`, etc.

**Header-Based Versioning (Alternative):**
- Header: `X-API-Version: 2.0`
- Falls back to URL version if header not provided

### Current Versions

| Version | Status | Base URL | Description |
|---------|--------|----------|-------------|
| **v1** | ✅ Stable | `/api/` | Current production version |
| **v2** | 🚧 Beta | `/api/v2/` | Enhanced features, improved responses |

### Version Detection

The API automatically detects the requested version:

1. **URL Path**: `/api/v2/bots/` → Uses v2
2. **Header**: `X-API-Version: 2.0` → Uses v2
3. **Default**: `/api/bots/` → Uses v1

### Version Differences

#### v1 Response Format
```json
{
  "success": true,
  "data": {
    "id": "bot_123",
    "name": "My Bot"
  }
}
```

#### v2 Response Format
```json
{
  "success": true,
  "data": {
    "id": "bot_123",
    "name": "My Bot"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "2.0",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Version-Specific Examples

#### Python - Using v2 API
```python
import requests

# Option 1: URL-based versioning
response = requests.get(
    "http://localhost:8000/api/v2/bots/",
    headers={"Authorization": f"Bearer {token}"}
)

# Option 2: Header-based versioning
response = requests.get(
    "http://localhost:8000/api/bots/",
    headers={
        "Authorization": f"Bearer {token}",
        "X-API-Version": "2.0"
    }
)
```

#### JavaScript/TypeScript - Using v2 API
```typescript
// Option 1: URL-based versioning
const response = await fetch('http://localhost:8000/api/v2/bots/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Option 2: Header-based versioning
const response = await fetch('http://localhost:8000/api/bots/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'X-API-Version': '2.0'
  }
});
```

#### cURL - Using v2 API
```bash
# URL-based versioning
curl -X GET http://localhost:8000/api/v2/bots/ \
  -H "Authorization: Bearer $TOKEN"

# Header-based versioning
curl -X GET http://localhost:8000/api/bots/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Version: 2.0"
```

### Migration Guide

#### Migrating from v1 to v2

**1. Update Base URL:**
```python
# v1
BASE_URL = "http://localhost:8000/api"

# v2
BASE_URL = "http://localhost:8000/api/v2"
```

**2. Handle Enhanced Response Format:**
```python
# v1 response handling
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
bots = response.json()  # Direct array or object

# v2 response handling
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
data = response.json()
bots = data["data"]  # Extract from "data" field
meta = data.get("meta", {})  # Access metadata
request_id = meta.get("request_id")  # Get request ID
```

**3. Use Request IDs for Debugging:**
```typescript
// v2 includes request_id in responses
const response = await fetch(`${BASE_URL}/bots/`, { headers });
const data = await response.json();
const requestId = data.meta?.request_id;

// Include in error reports
if (!response.ok) {
  console.error(`Request ID: ${requestId}`);
}
```

### Version Deprecation

**Deprecation Policy:**
- Versions are supported for **12 months** after a new version is released
- Deprecation warnings are included in response headers: `X-API-Deprecated: true`
- Deprecated versions receive security updates but no new features

**Checking Deprecation Status:**
```python
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
is_deprecated = response.headers.get("X-API-Deprecated") == "true"
deprecation_date = response.headers.get("X-API-Deprecation-Date")

if is_deprecated:
    print(f"API version deprecated. Migrate by {deprecation_date}")
```

### Version-Specific Features

**v1 Features:**
- Basic CRUD operations
- Standard error responses
- JWT authentication
- Rate limiting

**v2 Features (Beta):**
- Enhanced error responses with suggestions
- Request ID tracking
- Response metadata
- Improved pagination
- Field selection (sparse fieldsets)
- Enhanced filtering and sorting

### Best Practices

1. **Pin to Specific Version**: Always use a specific version in production
2. **Test Before Upgrading**: Test new versions in staging before production
3. **Monitor Deprecation Warnings**: Check response headers for deprecation notices
4. **Use Request IDs**: Leverage request IDs for debugging and support
5. **Handle Version Errors**: Implement fallback logic for version mismatches

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

## Wallet Management API

### GET /api/wallets
Get all wallets for the authenticated user.

**Response:**
```json
[
  {
    "id": "wallet_123",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
    "type": "custodial",
    "chain_id": 1,
    "chain_name": "Ethereum",
    "balance": "1.5",
    "balance_updated_at": "2025-12-06T10:30:00Z",
    "created_at": "2025-12-01T08:00:00Z"
  }
]
```

### POST /api/wallets
Create a new custodial wallet.

**Request Body:**
```json
{
  "chain_id": 1,
  "label": "My Ethereum Wallet"
}
```

**Response:**
```json
{
  "id": "wallet_123",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "type": "custodial",
  "chain_id": 1,
  "chain_name": "Ethereum",
  "created_at": "2025-12-06T10:30:00Z"
}
```

### GET /api/wallets/{wallet_id}/balance
Get balance for a specific wallet.

**Response:**
```json
{
  "wallet_id": "wallet_123",
  "balance": "1.5",
  "balance_updated_at": "2025-12-06T10:30:00Z",
  "chain_id": 1,
  "chain_name": "Ethereum"
}
```

### POST /api/wallets/{wallet_id}/withdraw
Initiate a withdrawal from a custodial wallet.

**Request Body:**
```json
{
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "amount": "0.5",
  "token_address": null,
  "two_factor_token": "123456"
}
```

**Response:**
```json
{
  "transaction_hash": "0xabc123...",
  "status": "pending",
  "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "amount": "0.5",
  "chain_id": 1,
  "created_at": "2025-12-06T10:30:00Z"
}
```

### GET /api/wallets/{wallet_id}/transactions
Get transaction history for a wallet.

**Query Parameters:**
- `limit` (optional): Number of transactions to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "transactions": [
    {
      "id": "tx_123",
      "transaction_hash": "0xabc123...",
      "type": "deposit",
      "amount": "1.0",
      "status": "confirmed",
      "block_number": 12345678,
      "created_at": "2025-12-06T10:30:00Z"
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

### POST /api/wallets/refresh-balances
Refresh balances for all user wallets.

**Response:**
```json
{
  "status": "success",
  "wallets_updated": 3,
  "updated_at": "2025-12-06T10:30:00Z"
}
```

### POST /api/wallets/external/register
Register an external (non-custodial) wallet for trading. Supports multi-chain wallets.

**Request Body:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "chain_id": 1,
  "signature": "0xabc123...",
  "nonce": "123456"
}
```

**Response:**
```json
{
  "id": "wallet_123",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "type": "external",
  "chain_id": 1,
  "chain_name": "Ethereum",
  "registered_at": "2025-12-06T10:30:00Z"
}
```

### POST /api/wallets/{wallet_id}/refresh-balance
Refresh wallet balance for a specific chain. Supports multi-chain wallets.

**Request:**
```
POST /api/wallets/wallet_123/refresh-balance
```

**Response:**
```json
{
  "wallet_id": "wallet_123",
  "chain_id": 1,
  "balance": "1.5",
  "balance_usd": "4500.00",
  "tokens": [
    {
      "address": "0x...",
      "symbol": "ETH",
      "balance": "1.5",
      "balance_usd": "4500.00"
    }
  ],
  "refreshed_at": "2025-12-06T10:30:00Z"
}
```

### GET /api/wallets/{wallet_id}/transactions
Get transaction history for a wallet across all chains.

**Query Parameters:**
- `chain_id` (optional): Filter by specific chain
- `limit` (optional): Number of transactions to return (default: 50, max: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "transactions": [
    {
      "id": "tx_123",
      "hash": "0xabc123...",
      "chain_id": 1,
      "chain_name": "Ethereum",
      "type": "swap",
      "status": "confirmed",
      "from_token": "USDC",
      "to_token": "ETH",
      "amount": "1000.00",
      "fee": "0.001",
      "timestamp": "2025-12-06T10:30:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

## DEX Trading API

The DEX Trading API enables decentralized exchange swaps across multiple chains (Ethereum, Base, Arbitrum, Polygon) using DEX aggregators (0x, OKX, Rubic) with automatic fallback logic.

### Supported Chains
- **Ethereum** (chain_id: 1)
- **Base** (chain_id: 8453)
- **Arbitrum One** (chain_id: 42161)
- **Polygon** (chain_id: 137)
- **Optimism** (chain_id: 10)
- **Avalanche** (chain_id: 43114)
- **BNB Chain** (chain_id: 56)

### POST /api/dex/quote
Get a quote for a DEX swap from multiple aggregators with automatic best price selection.

**Rate Limit:** 60 requests/minute

**Request Body:**
```json
{
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "sell_amount": "1000000000",
  "chain_id": 1,
  "slippage_percentage": 0.5,
  "cross_chain": false
}
```

**Code Examples:**

**Python:**
```python
import requests

quote_request = {
    "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    "sell_amount": "1000000000",  # 1000 USDC (6 decimals)
    "chain_id": 1,  # Ethereum
    "slippage_percentage": 0.5,
    "cross_chain": False
}

response = requests.post(
    f"{BASE_URL}/dex/quote",
    headers={"Authorization": f"Bearer {token}"},
    json=quote_request
)
response.raise_for_status()
quote = response.json()

print(f"Aggregator: {quote['aggregator']}")
print(f"Buy amount: {quote['buy_amount']}")
print(f"Price impact: {quote['price_impact'] * 100:.2f}%")
print(f"Estimated gas: {quote['estimated_gas']}")
```

**JavaScript/TypeScript:**
```typescript
const quoteRequest = {
  sell_token: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
  buy_token: "0xdAC17F958D2ee523a2206206994597C13D831ec7", // USDT
  sell_amount: "1000000000", // 1000 USDC (6 decimals)
  chain_id: 1, // Ethereum
  slippage_percentage: 0.5,
  cross_chain: false
};

const response = await fetch(`${BASE_URL}/dex/quote`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(quoteRequest)
});

const quote = await response.json();
console.log(`Aggregator: ${quote.aggregator}`);
console.log(`Buy amount: ${quote.buy_amount}`);
console.log(`Price impact: ${(quote.price_impact * 100).toFixed(2)}%`);
console.log(`Estimated gas: ${quote.estimated_gas}`);
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/dex/quote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "sell_amount": "1000000000",
    "chain_id": 1,
    "slippage_percentage": 0.5,
    "cross_chain": false
  }'
```

**Response:**
```json
{
  "aggregator": "0x",
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "sell_amount": "1000000000",
  "buy_amount": "999500000",
  "price": 0.9995,
  "estimated_gas": "150000",
  "sources": [
    {
      "dex": "Uniswap V3",
      "percentage": 100
    }
  ],
  "chain_id": 1,
  "price_impact": 0.05
}
```

**Error Responses:**
- `400 Bad Request`: Invalid token addresses or amounts
- `503 Service Unavailable`: All DEX aggregators unavailable
- `400 Bad Request`: Price impact exceeds threshold (>1% warning, >5% rejection)

### POST /api/dex/swap
Execute a DEX swap. Supports both custodial (platform-managed) and non-custodial (user wallet) modes.

**Rate Limit:** 20 requests/hour (security limit)

**Request Body (Custodial):**
```json
{
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "sell_amount": "1000000000",
  "chain_id": 1,
  "slippage_percentage": 0.5,
  "custodial": true
}
```

**Code Examples:**

**Python - Custodial Swap:**
```python
import requests
import time

swap_request = {
    "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "sell_amount": "1000000000",
    "chain_id": 1,
    "slippage_percentage": 0.5,
    "custodial": True
}

# Execute swap
response = requests.post(
    f"{BASE_URL}/dex/swap",
    headers={"Authorization": f"Bearer {token}"},
    json=swap_request
)
response.raise_for_status()
swap_result = response.json()

trade_id = swap_result["trade_id"]
tx_hash = swap_result["transaction_hash"]

print(f"Swap initiated: {trade_id}")
print(f"Transaction hash: {tx_hash}")

# Poll for status
while True:
    status_response = requests.get(
        f"{BASE_URL}/dex/trades/{trade_id}/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    status = status_response.json()
    
    if status["status"] in ["confirmed", "failed", "reverted"]:
        print(f"Swap {status['status']}: {status['transaction_hash']}")
        break
    
    print(f"Status: {status['status']}, waiting...")
    time.sleep(2)
```

**JavaScript/TypeScript - Custodial Swap:**
```typescript
const swapRequest = {
  sell_token: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  buy_token: "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  sell_amount: "1000000000",
  chain_id: 1,
  slippage_percentage: 0.5,
  custodial: true
};

// Execute swap
const response = await fetch(`${BASE_URL}/dex/swap`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(swapRequest)
});

const swapResult = await response.json();
const { trade_id, transaction_hash } = swapResult;

console.log(`Swap initiated: ${trade_id}`);
console.log(`Transaction hash: ${transaction_hash}`);

// Poll for status
const pollStatus = async () => {
  while (true) {
    const statusResponse = await fetch(
      `${BASE_URL}/dex/trades/${trade_id}/status`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      }
    );
    
    const status = await statusResponse.json();
    
    if (["confirmed", "failed", "reverted"].includes(status.status)) {
      console.log(`Swap ${status.status}: ${status.transaction_hash}`);
      break;
    }
    
    console.log(`Status: ${status.status}, waiting...`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
};

await pollStatus();
```

**cURL:**
```bash
# Execute swap
SWAP_RESPONSE=$(curl -X POST http://localhost:8000/api/dex/swap \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "sell_amount": "1000000000",
    "chain_id": 1,
    "slippage_percentage": 0.5,
    "custodial": true
  }')

TRADE_ID=$(echo $SWAP_RESPONSE | jq -r '.trade_id')

# Poll for status
while true; do
  STATUS=$(curl -X GET "http://localhost:8000/api/dex/trades/$TRADE_ID/status" \
    -H "Authorization: Bearer $TOKEN")
  
  STATUS_VALUE=$(echo $STATUS | jq -r '.status')
  echo "Status: $STATUS_VALUE"
  
  if [[ "$STATUS_VALUE" == "confirmed" || "$STATUS_VALUE" == "failed" ]]; then
    break
  fi
  
  sleep 2
done
```

**For Non-Custodial Swaps:**
```json
{
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "sell_amount": "1000000000",
  "chain_id": 1,
  "slippage_percentage": 0.5,
  "custodial": false,
  "user_wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "signature": "0xabc123..."
}
```

**Response:**
```json
{
  "success": true,
  "trade_id": "trade_123",
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "buy_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "sell_amount": "1000000000",
  "buy_amount": "999500000",
  "fee_amount": "5000",
  "transaction_hash": "0xabc123...",
  "status": "pending",
  "chain_id": 1,
  "aggregator": "0x",
  "created_at": "2025-12-06T10:30:00Z"
}
```

**Security Notes:**
- High-value swaps (>$100) require 2FA token
- Price impact warnings shown if >1%
- Swaps rejected if price impact >5%
- Transaction status monitored until confirmed

### GET /api/dex/trades/{trade_id}/status
Get status of a DEX trade. Polls blockchain until transaction is confirmed or fails.

**Response:**
```json
{
  "trade_id": "trade_123",
  "transaction_hash": "0xabc123...",
  "status": "confirmed",
  "block_number": 12345678,
  "confirmations": 12,
  "sell_amount": "1000000000",
  "buy_amount": "999500000",
  "gas_used": "150000",
  "gas_price": "20000000000",
  "chain_id": 1,
  "aggregator": "0x",
  "updated_at": "2025-12-06T10:32:00Z"
}
```

**Status Values:**
- `pending`: Transaction submitted, waiting for confirmation
- `confirmed`: Transaction confirmed on blockchain
- `failed`: Transaction failed on blockchain
- `reverted`: Transaction reverted

### GET /api/dex/aggregators/health
Check health status of all DEX aggregators.

**Response:**
```json
{
  "aggregators": {
    "0x": {
      "status": "healthy",
      "response_time_ms": 245
    },
    "okx": {
      "status": "healthy",
      "response_time_ms": 312
    },
    "rubic": {
      "status": "degraded",
      "response_time_ms": 1200
    }
  },
  "overall_status": "healthy"
}
```

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

### Official SDKs

- **Python SDK**: `pip install cryptoorchestrator-sdk`
- **JavaScript SDK**: `npm install @cryptoorchestrator/sdk`

### Python SDK Example

```python
from cryptoorchestrator import CryptoOrchestratorClient

# Initialize client
client = CryptoOrchestratorClient(
    base_url="http://localhost:8000/api",
    api_key="your_api_key"
)

# Or use token authentication
client = CryptoOrchestratorClient(
    base_url="http://localhost:8000/api"
)
client.authenticate("user@example.com", "password")

# Get all bots
bots = client.bots.list()
for bot in bots:
    print(f"Bot: {bot.name} - Status: {bot.status}")

# Create a bot
new_bot = client.bots.create(
    name="My Trading Bot",
    symbol="BTC/USD",
    strategy="momentum",
    mode="paper"
)

# Start bot
client.bots.start(new_bot.id)

# Get DEX quote
quote = client.dex.get_quote(
    sell_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    buy_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    sell_amount="1000000000",
    chain_id=1
)

# Execute swap
swap = client.dex.swap(
    sell_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    buy_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    sell_amount="1000000000",
    chain_id=1,
    custodial=True
)

# Poll for swap status
status = client.dex.get_swap_status(swap.trade_id)
while status.status == "pending":
    time.sleep(2)
    status = client.dex.get_swap_status(swap.trade_id)
```

### JavaScript/TypeScript SDK Example

```typescript
import { CryptoOrchestratorClient } from '@cryptoorchestrator/sdk';

// Initialize client
const client = new CryptoOrchestratorClient({
  baseUrl: 'http://localhost:8000/api',
  apiKey: 'your_api_key'
});

// Or use token authentication
await client.authenticate('user@example.com', 'password');

// Get all bots
const bots = await client.bots.list();
bots.forEach(bot => {
  console.log(`Bot: ${bot.name} - Status: ${bot.status}`);
});

// Create a bot
const newBot = await client.bots.create({
  name: 'My Trading Bot',
  symbol: 'BTC/USD',
  strategy: 'momentum',
  mode: 'paper'
});

// Start bot
await client.bots.start(newBot.id);

// Get DEX quote
const quote = await client.dex.getQuote({
  sellToken: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
  buyToken: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
  sellAmount: '1000000000',
  chainId: 1
});

// Execute swap
const swap = await client.dex.swap({
  sellToken: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
  buyToken: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
  sellAmount: '1000000000',
  chainId: 1,
  custodial: true
});

// Poll for swap status
let status = await client.dex.getSwapStatus(swap.tradeId);
while (status.status === 'pending') {
  await new Promise(resolve => setTimeout(resolve, 2000));
  status = await client.dex.getSwapStatus(swap.tradeId);
}
```

## Logs API

Administrative endpoints for searching, analyzing, and managing application logs. All endpoints require admin role.

### GET /api/logs/search

Search application logs with various filters.

**Query Parameters:**
- `query` (optional): Text search query
- `level` (optional): Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `user_id` (optional): Filter by user ID
- `request_id` (optional): Filter by request ID
- `trace_id` (optional): Filter by trace ID
- `start_time` (optional): Start time for time range filter (ISO 8601)
- `end_time` (optional): End time for time range filter (ISO 8601)
- `log_file` (default: "app"): Log file to search (app, errors, audit)
- `limit` (default: 100, max: 1000): Maximum number of results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "results": [
    {
      "timestamp": "2025-12-06T10:30:00Z",
      "level": "ERROR",
      "message": "Failed to execute trade",
      "user_id": "user_123",
      "request_id": "req_456",
      "trace_id": "trace_789",
      "module": "server_fastapi.routes.trades",
      "line": 234
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

**Example:**
```python
# Search for errors in the last hour
from datetime import datetime, timedelta

end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

response = requests.get(
    f"{BASE_URL}/logs/search",
    headers=headers,
    params={
        "level": "ERROR",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "limit": 50
    }
)
```

### GET /api/logs/statistics

Get log statistics for a time range.

**Query Parameters:**
- `start_time` (optional): Start time for statistics (ISO 8601)
- `end_time` (optional): End time for statistics (ISO 8601)
- `log_file` (default: "app"): Log file to analyze (app, errors, audit)

**Response:**
```json
{
  "total_logs": 12500,
  "by_level": {
    "DEBUG": 8000,
    "INFO": 3500,
    "WARNING": 800,
    "ERROR": 180,
    "CRITICAL": 20
  },
  "error_rate": 0.016,
  "time_range": {
    "start": "2025-12-06T09:00:00Z",
    "end": "2025-12-06T10:00:00Z"
  }
}
```

### GET /api/logs/tail

Get the last N lines from a log file (similar to `tail -n`).

**Query Parameters:**
- `log_file` (default: "app"): Log file to tail (app, errors, audit)
- `lines` (default: 50, max: 1000): Number of lines to return

**Response:**
```json
[
  {
    "timestamp": "2025-12-06T10:35:00Z",
    "level": "INFO",
    "message": "Bot started successfully",
    "user_id": "user_123"
  }
]
```

## Alerting & Incident Management API

Administrative endpoints for managing alerts, alert rules, and incidents. All endpoints require admin role.

### GET /api/alerting/alerts

Get active alerts.

**Query Parameters:**
- `severity` (optional): Filter by severity (low, medium, high, critical)

**Response:**
```json
[
  {
    "id": "alert_123",
    "rule_name": "high_error_rate",
    "metric": "error_rate",
    "current_value": 0.05,
    "threshold": 0.02,
    "severity": "high",
    "message": "Error rate exceeded threshold",
    "timestamp": "2025-12-06T10:30:00Z",
    "acknowledged": false,
    "resolved": false,
    "metadata": {}
  }
]
```

### GET /api/alerting/alerts/history

Get alert history.

**Query Parameters:**
- `limit` (default: 100, max: 1000): Maximum number of alerts
- `severity` (optional): Filter by severity

**Response:**
```json
[
  {
    "id": "alert_456",
    "rule_name": "slow_query_detected",
    "metric": "query_duration",
    "current_value": 250.5,
    "threshold": 200.0,
    "severity": "medium",
    "timestamp": "2025-12-06T09:15:00Z",
    "acknowledged": true,
    "resolved": true
  }
]
```

### POST /api/alerting/alerts/{alert_id}/acknowledge

Acknowledge an alert.

**Response:**
```json
{
  "success": true,
  "message": "Alert acknowledged"
}
```

### POST /api/alerting/alerts/{rule_name}/resolve

Resolve an active alert by rule name.

**Response:**
```json
{
  "success": true,
  "message": "Alert for rule 'high_error_rate' resolved"
}
```

### GET /api/alerting/rules

Get all alert rules.

**Response:**
```json
[
  {
    "name": "high_error_rate",
    "metric": "error_rate",
    "threshold": 0.02,
    "operator": "gt",
    "severity": "high",
    "channels": ["email", "slack"],
    "duration": 60,
    "cooldown": 300,
    "last_triggered": "2025-12-06T10:30:00Z",
    "trigger_count": 5
  }
]
```

### POST /api/alerting/rules

Create a new alert rule.

**Request Body:**
```json
{
  "name": "slow_endpoint",
  "metric": "endpoint_duration",
  "threshold": 1000.0,
  "operator": "gt",
  "severity": "medium",
  "channels": ["email"],
  "duration": 120,
  "cooldown": 600
}
```

**Response:**
```json
{
  "success": true,
  "rule": "slow_endpoint"
}
```

### GET /api/alerting/fatigue-stats

Get alert fatigue statistics.

**Response:**
```json
{
  "total_alerts_24h": 150,
  "alerts_by_severity": {
    "critical": 5,
    "high": 20,
    "medium": 50,
    "low": 75
  },
  "fatigue_score": 0.65,
  "most_frequent_rules": [
    {
      "rule_name": "high_error_rate",
      "count": 25
    }
  ]
}
```

### GET /api/alerting/incidents

Get active incidents.

**Query Parameters:**
- `severity` (optional): Filter by severity

**Response:**
```json
[
  {
    "id": "incident_789",
    "title": "Database Connection Pool Exhausted",
    "severity": "critical",
    "status": "open",
    "created_at": "2025-12-06T10:00:00Z",
    "updated_at": "2025-12-06T10:15:00Z",
    "resolved_at": null,
    "assigned_to": "admin@example.com",
    "related_alerts": ["alert_123", "alert_456"],
    "metadata": {
      "pool_size": 0,
      "max_pool_size": 20
    }
  }
]
```

### GET /api/alerting/incidents/{incident_id}

Get incident details.

**Response:**
```json
{
  "id": "incident_789",
  "title": "Database Connection Pool Exhausted",
  "severity": "critical",
  "status": "open",
  "created_at": "2025-12-06T10:00:00Z",
  "updated_at": "2025-12-06T10:15:00Z",
  "resolved_at": null,
  "assigned_to": "admin@example.com",
  "related_alerts": ["alert_123", "alert_456"],
  "metadata": {},
  "timeline": [
    {
      "timestamp": "2025-12-06T10:00:00Z",
      "event": "incident_created",
      "user": "system"
    }
  ]
}
```

### POST /api/alerting/incidents

Create a new incident.

**Request Body:**
```json
{
  "title": "Service Degradation Detected",
  "severity": "high",
  "description": "API response times increased by 200%",
  "related_alerts": ["alert_123"]
}
```

**Response:**
```json
{
  "id": "incident_790",
  "title": "Service Degradation Detected",
  "status": "open",
  "created_at": "2025-12-06T10:30:00Z"
}
```

### POST /api/alerting/incidents/{incident_id}/resolve

Resolve an incident.

**Response:**
```json
{
  "success": true,
  "message": "Incident resolved",
  "resolved_at": "2025-12-06T10:45:00Z"
}
```

## Database Performance API

Administrative endpoints for monitoring database performance, connection pools, and query optimization. All endpoints require admin role.

### GET /api/database/pool/metrics

Get connection pool metrics.

**Response:**
```json
{
  "pool_size": 10,
  "active_connections": 7,
  "idle_connections": 3,
  "max_pool_size": 20,
  "utilization_percent": 35.0,
  "wait_time_avg_ms": 2.5,
  "connection_errors": 0
}
```

### GET /api/database/pool/health

Get connection pool health status.

**Response:**
```json
{
  "status": "healthy",
  "warnings": [],
  "recommendations": [
    "Pool utilization is optimal"
  ],
  "metrics": {
    "utilization_percent": 35.0,
    "wait_time_avg_ms": 2.5
  }
}
```

### GET /api/database/pool/history

Get connection pool metrics history.

**Query Parameters:**
- `limit` (default: 100, max: 1000): Number of historical entries

**Response:**
```json
{
  "history": [
    {
      "timestamp": "2025-12-06T10:00:00Z",
      "pool_size": 10,
      "active_connections": 7,
      "utilization_percent": 35.0
    }
  ],
  "summary": {
    "avg_utilization": 32.5,
    "max_utilization": 45.0,
    "min_utilization": 20.0
  }
}
```

### GET /api/database/read-replicas/health

Get read replica health status.

**Response:**
```json
{
  "read_replicas_enabled": true,
  "read_replica_count": 2,
  "health": {
    "replica_1": {
      "status": "healthy",
      "lag_seconds": 0.5
    },
    "replica_2": {
      "status": "healthy",
      "lag_seconds": 1.2
    }
  }
}
```

### GET /api/database/indexes/usage

Analyze index usage for a table (PostgreSQL only).

**Query Parameters:**
- `table_name` (required): Table name to analyze

**Response:**
```json
{
  "table_name": "trades",
  "indexes": [
    {
      "index_name": "idx_trades_user_id",
      "scans": 12500,
      "tuples_read": 250000,
      "tuples_fetched": 250000,
      "size_bytes": 1048576
    }
  ]
}
```

### GET /api/database/indexes/unused

Find unused or rarely used indexes (PostgreSQL only).

**Query Parameters:**
- `min_scans` (default: 10): Minimum scans to consider index as used

**Response:**
```json
[
  {
    "index_name": "idx_old_table_column",
    "table_name": "old_table",
    "scans": 2,
    "size_bytes": 524288,
    "recommendation": "Consider dropping this index"
  }
]
```

### GET /api/database/indexes/missing

Find potential missing indexes (PostgreSQL only).

**Response:**
```json
[
  {
    "table_name": "trades",
    "column_name": "executed_at",
    "query_count": 5000,
    "avg_query_time_ms": 150.0,
    "recommendation": "Consider adding index on executed_at"
  }
]
```

## Cache Management API

Administrative endpoints for managing cache, viewing analytics, and controlling versioning. All endpoints require admin role.

### GET /api/cache/analytics

Get cache analytics and performance metrics.

**Query Parameters:**
- `time_window_minutes` (optional): Time window for statistics

**Response:**
```json
{
  "hit_rate": 0.85,
  "miss_rate": 0.15,
  "total_operations": 10000,
  "avg_response_time_ms": 2.5,
  "memory_hits": 7000,
  "redis_hits": 1500,
  "misses": 1500,
  "evictions": 50,
  "total_size_bytes": 104857600
}
```

### GET /api/cache/analytics/pattern/{pattern}

Get analytics for a specific cache pattern.

**Path Parameters:**
- `pattern`: Cache key pattern (e.g., "bots:*", "portfolio:*")

**Response:**
```json
{
  "pattern": "bots:*",
  "hit_rate": 0.92,
  "operations": 5000,
  "avg_response_time_ms": 1.8,
  "size_bytes": 52428800
}
```

### GET /api/cache/versions

Get all cache versions.

**Response:**
```json
{
  "versions": {
    "bots": 5,
    "portfolio": 3,
    "trades": 2
  }
}
```

### POST /api/cache/versions/{prefix}/increment

Increment cache version for a prefix (invalidates all cached data).

**Path Parameters:**
- `prefix`: Cache prefix (e.g., "bots", "portfolio")

**Query Parameters:**
- `reason` (optional): Reason for version increment

**Response:**
```json
{
  "success": true,
  "prefix": "bots",
  "new_version": 6,
  "message": "Cache version incremented to v6"
}
```

### POST /api/cache/versions/invalidate-all

Invalidate all cache versions (full cache clear).

**Query Parameters:**
- `reason` (optional): Reason for invalidation

**Response:**
```json
{
  "success": true,
  "message": "All cache versions invalidated"
}
```

### GET /api/cache/preloader/stats

Get predictive preloader statistics.

**Response:**
```json
{
  "total_accesses": 50000,
  "unique_keys": 1000,
  "frequently_accessed": [
    {
      "key": "bots:user_123",
      "access_count": 500,
      "last_accessed": "2025-12-06T10:30:00Z"
    }
  ],
  "preload_success_rate": 0.85
}
```

### POST /api/cache/preloader/preload-frequent

Manually trigger preloading of frequently accessed keys.

**Query Parameters:**
- `min_access_count` (default: 10): Minimum access count
- `time_window_minutes` (default: 60): Time window in minutes

**Response:**
```json
{
  "success": true,
  "message": "Preload triggered",
  "stats": {
    "keys_preloaded": 25,
    "total_accesses": 50000
  }
}
```

### GET /api/cache/metrics

Get cache metrics from MultiLevelCache.

**Response:**
```json
{
  "hits": 8500,
  "misses": 1500,
  "memory_hits": 7000,
  "redis_hits": 1500,
  "evictions": 50,
  "total_size_bytes": 104857600,
  "hit_rate": 0.85
}
```

### POST /api/cache/analytics/reset

Reset cache analytics statistics.

**Response:**
```json
{
  "success": true,
  "message": "Cache analytics reset"
}
```

## Background Jobs API

Administrative endpoints for monitoring and managing Celery background jobs. All endpoints require admin role.

### GET /api/background-jobs/status

Get overall background jobs status.

**Response:**
```json
{
  "celery_available": true,
  "active_workers": 3,
  "pending_tasks": 15,
  "completed_tasks_24h": 5000,
  "failed_tasks_24h": 25
}
```

### GET /api/background-jobs/tasks

Get active tasks.

**Response:**
```json
[
  {
    "job_id": "task_123",
    "status": "started",
    "task_name": "tasks.update_market_data",
    "created_at": "2025-12-06T10:30:00Z",
    "started_at": "2025-12-06T10:30:05Z",
    "progress": 0.65
  }
]
```

### GET /api/background-jobs/stats

Get job statistics.

**Response:**
```json
{
  "task_statistics": {
    "total_tasks": 10000,
    "successful_tasks": 9950,
    "failed_tasks": 50,
    "avg_execution_time_ms": 125.5
  },
  "queue_metrics": {
    "high_priority": 5,
    "normal_priority": 10,
    "low_priority": 0
  },
  "timestamp": "2025-12-06T10:35:00Z"
}
```

### GET /api/background-jobs/queue-depth

Get queue depth for each priority queue.

**Response:**
```json
{
  "high_priority": 5,
  "normal_priority": 10,
  "low_priority": 0
}
```

### GET /api/background-jobs/batching/stats

Get task batching statistics.

**Response:**
```json
{
  "batches": {
    "batch_1": {
      "task_count": 10,
      "created_at": "2025-12-06T10:30:00Z",
      "status": "pending"
    }
  },
  "timestamp": "2025-12-06T10:35:00Z"
}
```

### POST /api/background-jobs/batching/flush

Flush all pending batches.

**Response:**
```json
{
  "success": true,
  "results": {
    "batch_1": {
      "tasks_executed": 10,
      "status": "completed"
    }
  },
  "timestamp": "2025-12-06T10:35:00Z"
}
```

### GET /api/background-jobs/rate-limits

Get rate limit status for tasks.

**Query Parameters:**
- `task_name` (optional): Filter by task name

**Response:**
```json
{
  "rate_limits": [
    {
      "task_name": "tasks.update_market_data",
      "rate_limited": true,
      "max_calls": 100,
      "time_window_seconds": 60,
      "current_calls": 45,
      "remaining_calls": 55,
      "reset_after_seconds": 15
    }
  ]
}
```

### POST /api/background-jobs/rate-limits/{task_name}/reset

Reset rate limit history for a task.

**Path Parameters:**
- `task_name`: Task name to reset

**Response:**
```json
{
  "success": true,
  "message": "Rate limit reset for tasks.update_market_data"
}
```

## Push Notifications API

Endpoints for managing push notification subscriptions.

### POST /api/notifications/subscribe

Subscribe user to push notifications.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "base64_encoded_key",
    "auth": "base64_encoded_auth"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Push notifications subscribed successfully"
}
```

**Example (JavaScript):**
```typescript
// Get push subscription from browser
const registration = await navigator.serviceWorker.ready;
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
});

// Subscribe to backend
await fetch('/api/notifications/subscribe', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    endpoint: subscription.endpoint,
    keys: {
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth'))
    }
  })
});
```

### POST /api/notifications/unsubscribe

Unsubscribe user from push notifications.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Push notifications unsubscribed successfully"
}
```

## Support

For API support and questions:
- Documentation: https://docs.cryptoorchestrator.com
- Issues: https://github.com/cryptoorchestrator/api/issues
- Email: api-support@cryptoorchestrator.com

## Business Metrics API

### GET /api/business-metrics/summary

Get comprehensive business metrics summary including users, revenue, and trades.

**Authentication**: Required (admin:metrics permission)

**Response:**
```json
{
  "users": {
    "total_users": 1250,
    "active_users_24h": 342
  },
  "trades_per_day": [
    {
      "date": "2025-12-06",
      "trade_count": 45,
      "mode": "paper"
    }
  ],
  "revenue": {
    "subscription_revenue": 12500.50,
    "trading_fee_revenue": 2340.25,
    "total_revenue": 14840.75
  },
  "timestamp": "2025-12-06T12:00:00Z"
}
```

### GET /api/business-metrics/revenue

Get revenue metrics for a date range.

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)

### GET /api/business-metrics/revenue/daily

Get daily revenue breakdown for the last N days.

**Query Parameters:**
- `days` (optional, default: 30): Number of days

### GET /api/business-metrics/users

Get user growth and activity metrics.

### GET /api/business-metrics/trades

Get trading metrics for the last N days.

**Query Parameters:**
- `days` (optional, default: 30): Number of days

### GET /api/business-metrics/dashboard

Get comprehensive business dashboard with all metrics, KPIs, user acquisition, and trading activity.

### GET /api/business-metrics/kpis

Get key performance indicators with growth rates.

**Query Parameters:**
- `period_days` (optional, default: 30): Period in days

### GET /api/business-metrics/user-acquisition

Get user acquisition metrics including daily registrations.

**Query Parameters:**
- `days` (optional, default: 30): Number of days

### GET /api/business-metrics/trading-activity

Get trading activity breakdown by mode and chain.

**Query Parameters:**
- `days` (optional, default: 30): Number of days

## Performance Profiling API

### GET /api/performance-profiling/slow-queries

Get slow database queries sorted by duration.

**Authentication**: Required (admin:performance permission)

**Query Parameters:**
- `limit` (optional, default: 50): Maximum number of queries to return

**Response:**
```json
{
  "slow_queries": [
    {
      "query": "SELECT * FROM trades WHERE user_id = ?",
      "duration_ms": 245.5,
      "params": "{'user_id': 123}",
      "timestamp": "2025-12-06T12:00:00Z"
    }
  ],
  "count": 1,
  "limit": 50
}
```

### GET /api/performance-profiling/slow-endpoints

Get slow API endpoints sorted by p95 latency.

**Query Parameters:**
- `limit` (optional, default: 50): Maximum number of endpoints to return

**Response:**
```json
{
  "slow_endpoints": [
    {
      "method": "GET",
      "path": "/api/bots",
      "p95_ms": 350.2,
      "avg_ms": 280.5,
      "max_ms": 450.0,
      "count": 150,
      "status_code": 200,
      "timestamp": "2025-12-06T12:00:00Z"
    }
  ],
  "count": 1,
  "limit": 50
}
```

### GET /api/performance-profiling/query-statistics

Get performance statistics for a specific query or all queries.

**Query Parameters:**
- `query` (optional): Specific query to analyze

### GET /api/performance-profiling/endpoint-statistics

Get performance statistics for a specific endpoint or all endpoints.

**Query Parameters:**
- `method` (optional): HTTP method
- `path` (optional): Endpoint path

### GET /api/performance-profiling/summary

Get comprehensive performance profiling summary.

### POST /api/performance-profiling/clear-old-entries

Clear profiling entries older than specified hours.

**Query Parameters:**
- `max_age_hours` (optional, default: 24): Maximum age in hours

---

*Last updated: 2025-12-06* | *Version: 1.4.0* | *Enhanced with business metrics, performance profiling, distributed tracing, and comprehensive monitoring API documentation*