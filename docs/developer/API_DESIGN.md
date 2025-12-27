# API Design Guidelines

Comprehensive guidelines for designing and developing APIs in CryptoOrchestrator.

## Table of Contents

1. [API Principles](#api-principles)
2. [RESTful Design](#restful-design)
3. [Request/Response Format](#requestresponse-format)
4. [Error Handling](#error-handling)
5. [Authentication & Authorization](#authentication--authorization)
6. [Pagination](#pagination)
7. [Versioning](#versioning)
8. [Documentation](#documentation)

## API Principles

### 1. Consistency
- Use consistent naming conventions
- Follow RESTful patterns
- Maintain uniform response formats

### 2. Simplicity
- Keep endpoints focused and simple
- Avoid over-engineering
- Prefer clarity over cleverness

### 3. Security
- Always authenticate requests
- Validate all inputs
- Use HTTPS only
- Implement rate limiting

### 4. Performance
- Use pagination for large datasets
- Implement caching where appropriate
- Optimize database queries
- Minimize response payloads

## RESTful Design

### Resource Naming

Use nouns, not verbs:
- ✅ `/api/trades`
- ✅ `/api/users`
- ❌ `/api/getTrades`
- ❌ `/api/createUser`

### HTTP Methods

- `GET`: Retrieve resources
- `POST`: Create resources
- `PUT`: Update entire resource
- `PATCH`: Partial update
- `DELETE`: Delete resource

### Status Codes

- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

## Request/Response Format

### Request Headers

```http
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <uuid>
```

### Request Body

```json
{
  "symbol": "BTC/USD",
  "amount": 0.1,
  "order_type": "market"
}
```

### Response Format

```json
{
  "data": {
    "id": 123,
    "symbol": "BTC/USD",
    "amount": 0.1,
    "status": "completed"
  },
  "meta": {
    "timestamp": "2025-12-12T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "amount",
        "message": "Amount must be positive"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-12-12T10:30:00Z",
    "request_id": "uuid"
  }
}
```

## Error Handling

### Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

### Error Handling Best Practices

1. **Always return consistent error format**
2. **Include helpful error messages**
3. **Log errors server-side**
4. **Don't expose sensitive information**
5. **Use appropriate HTTP status codes**

## Authentication & Authorization

### Authentication

Use JWT tokens:
```http
Authorization: Bearer <jwt_token>
```

### Authorization

Use role-based access control:
- `user`: Regular user
- `admin`: Administrator
- `moderator`: Content moderator

### Example

```python
from fastapi import Depends
from ..dependencies.auth import require_permission

@router.get("/admin/users")
async def get_users(
    current_user: dict = Depends(require_permission("admin:users:read")),
):
    # Admin-only endpoint
    pass
```

## Pagination

### Query Parameters

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `sort`: Sort field
- `order`: Sort order (asc/desc)

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Versioning

### URL Versioning

```
/api/v1/trades
/api/v2/trades
```

### Header Versioning

```http
Accept: application/vnd.cryptoorchestrator.v1+json
```

## Documentation

### OpenAPI/Swagger

- Auto-generate from code
- Keep descriptions up-to-date
- Include examples
- Document all parameters

### Example

```python
@router.post(
    "/api/trades",
    response_model=TradeResponse,
    summary="Create a new trade",
    description="Execute a cryptocurrency trade",
)
async def create_trade(
    request: CreateTradeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new trade.
    
    - **symbol**: Trading pair (e.g., BTC/USD)
    - **amount**: Trade amount
    - **order_type**: Market or limit order
    """
    pass
```

## Best Practices

1. **Use async/await** for all database operations
2. **Validate inputs** with Pydantic models
3. **Handle errors gracefully** with try/except
4. **Log important events** for debugging
5. **Test thoroughly** with unit and integration tests
6. **Document endpoints** with OpenAPI
7. **Use type hints** for better IDE support
8. **Follow RESTful conventions** consistently

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [REST API Design Best Practices](https://restfulapi.net/)
- [OpenAPI Specification](https://swagger.io/specification/)
