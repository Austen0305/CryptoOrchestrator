# API Enhancements & Documentation

## Overview

This document describes the enhancements made to the CryptoOrchestrator API for improved reliability, performance, and developer experience.

## New Features

### 1. Structured Error Responses

All API errors now return a consistent structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "status_code": 400,
    "details": {
      "validation_errors": [
        {
          "field": "email",
          "message": "Invalid email format",
          "type": "value_error"
        }
      ]
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Error Codes:**
- `VALIDATION_ERROR` - Input validation failed (400)
- `AUTHENTICATION_ERROR` - Authentication required (401)
- `AUTHORIZATION_ERROR` - Insufficient permissions (403)
- `NOT_FOUND` - Resource not found (404)
- `CONFLICT` - Resource conflict (409)
- `RATE_LIMIT_EXCEEDED` - Too many requests (429)
- `INTERNAL_ERROR` - Server error (500)

### 2. Request ID Tracking

Every API request now includes a unique request ID in headers:

**Request:**
```http
GET /api/bots/
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```http
HTTP/1.1 200 OK
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Response-Time: 45.23ms
```

Use request IDs for:
- Log correlation
- Debugging
- Support requests
- Performance tracking

### 3. Performance Monitoring

New endpoints for performance metrics:

**Get Performance Stats:**
```http
GET /api/performance/stats
```

**Response:**
```json
{
  "total_requests": 1234,
  "average_response_time": 45.23,
  "endpoints": {
    "GET /api/bots/": {
      "count": 100,
      "average_time": 35.5,
      "min_time": 10.2,
      "max_time": 150.8,
      "error_rate": 0.02,
      "errors": 2
    }
  }
}
```

**Get Slow Requests:**
```http
GET /api/performance/slow-requests?threshold_ms=1000&limit=10
```

**Response:**
```json
{
  "threshold_ms": 1000.0,
  "count": 3,
  "requests": [
    {
      "endpoint": "POST /api/backtesting/run",
      "duration": 2.45,
      "status_code": 200,
      "timestamp": 1702569600.0
    }
  ]
}
```

### 4. Enhanced Health Checks

Comprehensive health check endpoint:

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "CryptoOrchestrator API",
  "database": "healthy",
  "redis": "available",
  "timestamp": "2025-11-13T12:00:00Z"
}
```

Advanced health checks:
```http
GET /api/health/comprehensive
```

## Best Practices

### Error Handling

Always check for error responses:

```javascript
const response = await fetch('/api/bots/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const data = await response.json();

if (!response.ok) {
  // Handle error
  console.error('Error:', data.error.code, data.error.message);
  if (data.error.request_id) {
    console.error('Request ID:', data.error.request_id);
  }
  throw new Error(data.error.message);
}

// Use data
console.log('Bots:', data);
```

### Request ID Usage

Include request ID in error reports:

```javascript
try {
  await apiCall();
} catch (error) {
  const requestId = error.response?.headers?.get('X-Request-ID');
  logError({
    message: error.message,
    request_id: requestId,
    // ... other context
  });
}
```

### Performance Monitoring

Monitor response times:

```javascript
const startTime = performance.now();
const response = await fetch('/api/bots/');
const duration = performance.now() - startTime;

// Log slow requests
if (duration > 1000) {
  console.warn('Slow request:', duration, 'ms');
}

// Use response time header if available
const responseTime = response.headers.get('X-Response-Time');
console.log('Server response time:', responseTime);
```

## Migration Guide

### Error Response Format

**Old Format:**
```json
{
  "message": "Error message",
  "error": "Error details"
}
```

**New Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "status_code": 400,
    "details": {},
    "request_id": "..."
  }
}
```

**Migration:**
```javascript
// Old
const message = response.json().message;

// New
const error = response.json().error;
const message = error.message;
const code = error.code;
```

## Rate Limiting

Rate limits are enforced per endpoint. Check headers for limit information:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1702569600
Retry-After: 60
```

## Security

### Authentication

All API endpoints require authentication except:
- `/health`
- `/api/auth/register`
- `/api/auth/login`

### Security Headers

All responses include security headers:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: ...`

## Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

