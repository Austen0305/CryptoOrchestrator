# Marketplace API Reference

Complete API reference for Copy Trading Marketplace and Custom Indicator Marketplace.

## Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://api.cryptoorchestrator.com`

## Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Copy Trading Marketplace

### Apply as Signal Provider

Apply to become a signal provider (requires curator approval).

**Endpoint**: `POST /api/marketplace/apply`

**Request**:
```json
{
  "profile_description": "Professional trader with 5 years experience in crypto markets"
}
```

**Response** (200):
```json
{
  "id": 1,
  "user_id": 123,
  "status": "pending",
  "message": "Application submitted for curator review"
}
```

---

### Browse Signal Providers

Get list of approved signal providers with filtering and sorting.

**Endpoint**: `GET /api/marketplace/traders`

**Query Parameters**:
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 20, max: 100): Items per page
- `sort_by` (string): Sort field - `total_return`, `sharpe_ratio`, `win_rate`, `follower_count`, `rating`
- `min_rating` (float, optional): Minimum average rating (0-5)
- `min_win_rate` (float, optional): Minimum win rate (0-1)
- `min_sharpe` (float, optional): Minimum Sharpe ratio

**Response** (200):
```json
{
  "traders": [
    {
      "id": 1,
      "user_id": 123,
      "username": "trader_john",
      "profile_description": "Professional trader...",
      "trading_strategy": "Swing trading",
      "risk_level": "medium",
      "total_return": 45.5,
      "sharpe_ratio": 2.1,
      "win_rate": 0.65,
      "total_trades": 150,
      "follower_count": 250,
      "average_rating": 4.5,
      "total_ratings": 45,
      "subscription_fee": 29.99,
      "performance_fee_percentage": 20.0,
      "curator_status": "approved",
      "last_metrics_update": "2025-12-12T10:00:00Z"
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

---

### Get Trader Profile

Get detailed profile of a specific signal provider.

**Endpoint**: `GET /api/marketplace/traders/{trader_id}`

**Response** (200):
```json
{
  "id": 1,
  "user_id": 123,
  "username": "trader_john",
  "profile_description": "Professional trader...",
  "trading_strategy": "Swing trading",
  "risk_level": "medium",
  "total_return": 45.5,
  "sharpe_ratio": 2.1,
  "win_rate": 0.65,
  "total_trades": 150,
  "winning_trades": 98,
  "total_profit": 12500.50,
  "max_drawdown": 12.5,
  "profit_factor": 1.85,
  "follower_count": 250,
  "average_rating": 4.5,
  "total_ratings": 45,
  "subscription_fee": 29.99,
  "performance_fee_percentage": 20.0,
  "curator_status": "approved",
  "last_metrics_update": "2025-12-12T10:00:00Z"
}
```

---

### Rate a Trader

Rate a signal provider (1-5 stars).

**Endpoint**: `POST /api/marketplace/traders/{trader_id}/rate`

**Request**:
```json
{
  "rating": 5,
  "comment": "Excellent trader, very consistent returns!"
}
```

**Response** (200):
```json
{
  "id": 1,
  "signal_provider_id": 1,
  "user_id": 456,
  "rating": 5,
  "comment": "Excellent trader, very consistent returns!",
  "created_at": "2025-12-12T10:00:00Z"
}
```

---

### Verify Provider Performance (Admin)

Verify historical performance of a signal provider.

**Endpoint**: `POST /api/marketplace/traders/{trader_id}/verify`

**Query Parameters**:
- `period_days` (int, default: 90): Period to verify

**Response** (200):
```json
{
  "provider_id": 1,
  "verified": true,
  "period_days": 90,
  "trades_count": 150,
  "verified_metrics": {
    "total_return": 45.5,
    "sharpe_ratio": 2.1,
    "win_rate": 0.65,
    "total_trades": 150,
    "profit_factor": 1.85,
    "max_drawdown": 12.5
  },
  "stored_metrics": {
    "total_return": 45.5,
    "sharpe_ratio": 2.1,
    "win_rate": 0.65,
    "total_trades": 150
  },
  "discrepancies": [],
  "verification_date": "2025-12-12T10:00:00Z"
}
```

---

### Calculate Payout

Calculate payout for a signal provider.

**Endpoint**: `GET /api/marketplace/payouts/calculate`

**Query Parameters**:
- `signal_provider_id` (int, required): Signal provider ID
- `period_days` (int, default: 30): Period in days

**Response** (200):
```json
{
  "signal_provider_id": 1,
  "period_start": "2025-11-12T00:00:00Z",
  "period_end": "2025-12-12T00:00:00Z",
  "total_revenue": 5000.00,
  "platform_fee": 1000.00,
  "provider_payout": 4000.00,
  "follower_count": 250,
  "active_followers": 200
}
```

---

### Create Payout

Create a payout record for a signal provider.

**Endpoint**: `POST /api/marketplace/payouts/create`

**Query Parameters**:
- `signal_provider_id` (int, required): Signal provider ID
- `period_days` (int, default: 30): Period in days

**Response** (200):
```json
{
  "id": 1,
  "signal_provider_id": 1,
  "period_start": "2025-11-12T00:00:00Z",
  "period_end": "2025-12-12T00:00:00Z",
  "total_revenue": 5000.00,
  "platform_fee": 1000.00,
  "provider_payout": 4000.00,
  "status": "pending",
  "created_at": "2025-12-12T10:00:00Z"
}
```

---

## Custom Indicator Marketplace

### Browse Indicators

Get list of available indicators with filtering.

**Endpoint**: `GET /api/indicators/marketplace`

**Query Parameters**:
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 20, max: 100): Items per page
- `category` (string, optional): Filter by category - `trend`, `momentum`, `volatility`, `volume`
- `min_rating` (float, optional): Minimum average rating (0-5)
- `search` (string, optional): Search by name or tags
- `sort_by` (string, default: "popularity"): Sort field - `popularity`, `rating`, `price`, `created_at`

**Response** (200):
```json
{
  "indicators": [
    {
      "id": 1,
      "name": "RSI",
      "description": "Relative Strength Index",
      "category": "momentum",
      "tags": "rsi, momentum, oscillator",
      "price": 0.0,
      "is_free": true,
      "average_rating": 4.8,
      "total_ratings": 125,
      "purchase_count": 500,
      "developer": {
        "id": 1,
        "username": "admin"
      },
      "status": "approved",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 20
}
```

---

### Get Indicator Details

Get detailed information about a specific indicator.

**Endpoint**: `GET /api/indicators/{indicator_id}`

**Response** (200):
```json
{
  "id": 1,
  "name": "RSI",
  "description": "Relative Strength Index",
  "category": "momentum",
  "tags": "rsi, momentum, oscillator",
  "code": "...",
  "language": "python",
  "parameters": {
    "period": {
      "type": "integer",
      "default": 14,
      "min": 1,
      "max": 200
    }
  },
  "price": 0.0,
  "is_free": true,
  "average_rating": 4.8,
  "total_ratings": 125,
  "purchase_count": 500,
  "developer": {
    "id": 1,
    "username": "admin"
  },
  "status": "approved",
  "version": "1.0.0",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-12-01T00:00:00Z"
}
```

---

### Create Indicator

Create a new custom indicator (developer).

**Endpoint**: `POST /api/indicators`

**Request**:
```json
{
  "name": "My Custom Indicator",
  "description": "Custom momentum indicator",
  "category": "momentum",
  "tags": "custom, momentum",
  "code": "import pandas as pd\n...",
  "language": "python",
  "parameters": {
    "period": {
      "type": "integer",
      "default": 14,
      "min": 1,
      "max": 200
    }
  },
  "price": 19.99,
  "is_free": false
}
```

**Response** (200):
```json
{
  "id": 100,
  "name": "My Custom Indicator",
  "description": "Custom momentum indicator",
  "category": "momentum",
  "status": "pending",
  "created_at": "2025-12-12T10:00:00Z"
}
```

---

### Publish Indicator

Publish an indicator for review/approval.

**Endpoint**: `POST /api/indicators/{indicator_id}/publish`

**Request**:
```json
{
  "version_name": "1.0.0",
  "release_notes": "Initial release"
}
```

**Response** (200):
```json
{
  "id": 100,
  "status": "pending",
  "version": "1.0.0",
  "published_at": "2025-12-12T10:00:00Z"
}
```

---

### Execute Indicator

Execute an indicator with market data.

**Endpoint**: `POST /api/indicators/{indicator_id}/execute`

**Request**:
```json
{
  "market_data": [
    {
      "open": 50000,
      "high": 51000,
      "low": 49000,
      "close": 50500,
      "volume": 1000,
      "timestamp": "2025-12-01T00:00:00Z"
    }
  ],
  "parameters": {
    "period": 14
  }
}
```

**Response** (200):
```json
{
  "values": [75.5],
  "output": {
    "rsi": 75.5,
    "signal": -1
  },
  "execution_time_ms": 45
}
```

---

### Purchase Indicator

Purchase an indicator (if not free).

**Endpoint**: `POST /api/indicators/{indicator_id}/purchase`

**Response** (200):
```json
{
  "id": 1,
  "indicator_id": 100,
  "user_id": 123,
  "purchase_price": 19.99,
  "purchased_at": "2025-12-12T10:00:00Z"
}
```

---

### Rate Indicator

Rate an indicator (1-5 stars).

**Endpoint**: `POST /api/indicators/{indicator_id}/rate`

**Request**:
```json
{
  "rating": 5,
  "comment": "Great indicator, very accurate!"
}
```

**Response** (200):
```json
{
  "id": 1,
  "indicator_id": 100,
  "user_id": 123,
  "rating": 5,
  "comment": "Great indicator, very accurate!",
  "created_at": "2025-12-12T10:00:00Z"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

API endpoints are rate-limited:
- **Default**: 60 requests per minute
- **Burst**: 100 requests

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1639324800
```

---

## Pagination

List endpoints support pagination:

- `skip`: Number of items to skip
- `limit`: Number of items to return (max 100)

Response includes:
- `total`: Total number of items
- `skip`: Current offset
- `limit`: Current limit

---

## Webhooks (Future)

---

## Analytics Endpoints

### Get Marketplace Overview (Admin Only)

Get comprehensive statistics for both marketplaces.

**Endpoint**: `GET /admin/marketplace/overview`

**Headers**: Requires admin authentication

**Response** (200):
```json
{
  "copy_trading": {
    "total_providers": 150,
    "approved_providers": 120,
    "pending_providers": 30,
    "total_ratings": 1250,
    "average_rating": 4.5,
    "total_followers": 5000,
    "total_payouts": 45,
    "total_payout_amount": 125000.00,
    "platform_revenue": 31250.00
  },
  "indicators": {
    "total_indicators": 200,
    "approved_indicators": 180,
    "pending_indicators": 20,
    "free_indicators": 120,
    "paid_indicators": 80,
    "total_purchases": 500,
    "total_revenue": 50000.00,
    "platform_revenue": 15000.00,
    "developer_revenue": 35000.00,
    "total_ratings": 300,
    "average_rating": 4.3,
    "by_category": {
      "trend": 60,
      "momentum": 50,
      "volatility": 40,
      "volume": 30
    }
  },
  "timestamp": "2025-12-12T10:00:00Z"
}
```

**Rate Limit**: 30 requests/minute

---

### Get Top Providers (Admin Only)

Get top performing signal providers.

**Endpoint**: `GET /admin/marketplace/top-providers`

**Query Parameters**:
- `limit` (optional, default: 10): Number of providers to return (1-50)
- `sort_by` (optional, default: "total_return"): Sort by `total_return`, `sharpe_ratio`, `follower_count`, or `rating`

**Response** (200):
```json
{
  "providers": [
    {
      "id": 1,
      "username": "trader_pro",
      "total_return": 45.5,
      "sharpe_ratio": 2.1,
      "win_rate": 0.68,
      "follower_count": 250,
      "average_rating": 4.8
    }
  ],
  "limit": 10,
  "sort_by": "total_return"
}
```

**Rate Limit**: 30 requests/minute

---

### Get Top Indicators (Admin Only)

Get top performing indicators.

**Endpoint**: `GET /admin/marketplace/top-indicators`

**Query Parameters**:
- `limit` (optional, default: 10): Number of indicators to return (1-50)
- `sort_by` (optional, default: "purchase_count"): Sort by `purchase_count`, `rating`, or `price`

**Response** (200):
```json
{
  "indicators": [
    {
      "id": 1,
      "name": "Advanced RSI",
      "category": "momentum",
      "price": 29.99,
      "is_free": false,
      "purchase_count": 150,
      "average_rating": 4.7
    }
  ],
  "limit": 10,
  "sort_by": "purchase_count"
}
```

**Rate Limit**: 30 requests/minute

---

### Get Revenue Trends (Admin Only)

Get revenue trends over time for both marketplaces.

**Endpoint**: `GET /admin/marketplace/revenue-trends`

**Query Parameters**:
- `days` (optional, default: 30): Number of days to analyze (1-365)

**Response** (200):
```json
{
  "copy_trading": [
    {
      "date": "2025-12-01",
      "platform_revenue": 1250.00,
      "provider_payout": 5000.00
    }
  ],
  "indicators": [
    {
      "date": "2025-12-01",
      "total_revenue": 2000.00,
      "platform_revenue": 600.00,
      "developer_revenue": 1400.00,
      "purchase_count": 25
    }
  ],
  "period_days": 30
}
```

**Rate Limit**: 20 requests/minute

---

### Get Developer Analytics

Get analytics for the current developer's indicators.

**Endpoint**: `GET /api/indicators/analytics/developer`

**Response** (200):
```json
{
  "developer_id": 123,
  "total_indicators": 5,
  "total_purchases": 150,
  "total_revenue": 4500.00,
  "developer_earnings": 3150.00,
  "average_rating": 4.5,
  "indicators": [
    {
      "id": 1,
      "name": "My Indicator",
      "purchases": 50,
      "revenue": 1500.00,
      "developer_earnings": 1050.00,
      "average_rating": 4.7
    }
  ]
}
```

**Rate Limit**: 30 requests/minute

---

### Get Indicator Analytics

Get analytics for a specific indicator (owner only).

**Endpoint**: `GET /api/indicators/analytics/indicator/{indicator_id}`

**Response** (200):
```json
{
  "indicator_id": 1,
  "name": "Advanced RSI",
  "purchases": 50,
  "total_revenue": 1500.00,
  "developer_earnings": 1050.00,
  "platform_fee": 450.00,
  "average_rating": 4.7,
  "total_ratings": 35
}
```

**Rate Limit**: 30 requests/minute

---

### Get Provider Analytics

Get analytics for a specific signal provider (owner only).

**Endpoint**: `GET /api/marketplace/analytics/provider/{provider_id}`

**Response** (200):
```json
{
  "provider_id": 1,
  "total_return": 45.5,
  "sharpe_ratio": 2.1,
  "win_rate": 0.68,
  "total_trades": 150,
  "follower_count": 250,
  "average_rating": 4.8,
  "total_ratings": 45,
  "total_payouts": 5,
  "total_earnings": 12500.00,
  "recent_payouts": [
    {
      "id": 1,
      "period_start": "2025-11-01T00:00:00Z",
      "period_end": "2025-11-30T23:59:59Z",
      "provider_payout": 2500.00,
      "status": "completed"
    }
  ],
  "recent_ratings": [
    {
      "id": 1,
      "rating": 5,
      "comment": "Excellent trader!",
      "created_at": "2025-12-10T10:00:00Z"
    }
  ]
}
```

**Rate Limit**: 30 requests/minute

---

## Webhooks (Future)

Webhook endpoints for marketplace events (coming soon):
- Provider approval/rejection
- New follower
- Payout processed
- Indicator purchase

---

**Last Updated**: December 12, 2025  
**API Version**: 1.0.0
