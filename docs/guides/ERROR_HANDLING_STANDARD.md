# Standardized Error Handling for FastAPI Routes

> **Purpose**: Standardize error handling across all routes for consistent logging and error responses  
> **Pattern Source**: `.cursor/extracted-patterns.md` - FastAPI Route Pattern  
> **Status**: Implementation in progress

## Standard Error Handling Pattern

All routes should follow this pattern:

```python
from fastapi import HTTPException
from ..utils.route_helpers import _get_user_id
import logging

logger = logging.getLogger(__name__)

@router.get("/bots")
async def get_bots(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[BotService, Depends(get_bot_service)],
):
    """Get all bots for the current user"""
    try:
        user_id = _get_user_id(current_user)
        bots = await service.get_bots(user_id)
        return bots
    except HTTPException:
        # Let HTTPExceptions propagate (they're already properly formatted)
        raise
    except Exception as e:
        # Log error with full context
        logger.error(
            f"Failed to get bots: {e}",
            exc_info=True,
            extra={"user_id": user_id, "operation": "get_bots"}
        )
        # Raise standardized HTTPException
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve bots"
        )
```

## Key Principles

1. **Always use try/except blocks** for route handlers
2. **Let HTTPExceptions propagate** - Don't catch and re-raise them
3. **Log all other exceptions** with:
   - `exc_info=True` for full traceback
   - `extra` context (user_id, operation name, relevant IDs)
4. **Raise standardized HTTPException** with appropriate status code and message
5. **Include user_id in logs** when available (use `_get_user_id()` helper)

## Error Status Codes

- **400 Bad Request**: Validation errors, invalid input
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate)
- **422 Unprocessable Entity**: Validation errors (Pydantic)
- **500 Internal Server Error**: Unexpected errors (default)

## Logging Context

Always include relevant context in error logs:

```python
logger.error(
    f"Failed to {operation_name}: {e}",
    exc_info=True,
    extra={
        "user_id": user_id,
        "operation": operation_name,
        "bot_id": bot_id,  # If relevant
        "error_type": type(e).__name__,
    }
)
```

## Alternative: Using Helper Function

For routes that prefer a helper function, use `handle_route_error`:

```python
from ..utils.route_helpers import handle_route_error

try:
    bot = await service.get_bot(bot_id, user_id)
    return bot
except HTTPException:
    raise
except Exception as e:
    raise handle_route_error(
        e,
        operation_name="get bot",
        user_id=user_id,
        error_message="Failed to retrieve bot",
        extra_context={"bot_id": bot_id}
    )
```

## Common Patterns

### Pattern 1: Simple Route
```python
@router.get("/resource")
async def get_resource(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    try:
        user_id = _get_user_id(current_user)
        return await service.get_resource(user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource: {e}", exc_info=True, extra={"user_id": user_id})
        raise HTTPException(status_code=500, detail="Failed to retrieve resource")
```

### Pattern 2: Route with ID Parameter
```python
@router.get("/resource/{resource_id}")
async def get_resource_by_id(
    resource_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    try:
        user_id = _get_user_id(current_user)
        resource = await service.get_resource_by_id(resource_id, user_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        return resource
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get resource {resource_id}: {e}",
            exc_info=True,
            extra={"user_id": user_id, "resource_id": resource_id}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve resource")
```

### Pattern 3: Route with Validation Errors
```python
@router.post("/resource")
async def create_resource(
    request: CreateResourceRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    try:
        user_id = _get_user_id(current_user)
        # Validation errors are automatically handled by FastAPI/Pydantic
        resource = await service.create_resource(request, user_id)
        return resource
    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to create resource: {e}",
            exc_info=True,
            extra={"user_id": user_id, "request": request.dict()}
        )
        raise HTTPException(status_code=500, detail="Failed to create resource")
```

## Migration Checklist

When fixing routes, ensure:

- [ ] Route has try/except block
- [ ] HTTPException is re-raised (not caught)
- [ ] Other exceptions are logged with `exc_info=True`
- [ ] Log includes `user_id` when available
- [ ] Log includes operation name
- [ ] Log includes relevant IDs (bot_id, trade_id, etc.)
- [ ] HTTPException has appropriate status code
- [ ] HTTPException has clear error message
- [ ] No sensitive data in error messages (production)

## Examples from Codebase

### Good Example (from `routes/bots.py`)
```python
@router.get("/bots/{bot_id}/risk-metrics")
async def get_bot_risk_metrics(...):
    try:
        user_id = _get_user_id(current_user)
        # ... logic ...
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot risk metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")
```

### Needs Fixing
```python
@router.get("/resource")
async def get_resource(...):
    # Missing error handling
    return await service.get_resource(user_id)
```

## Related Files

- `server_fastapi/utils/route_helpers.py` - Helper functions including `handle_route_error`
- `server_fastapi/middleware/error_handler.py` - Global error handlers
- `.cursor/extracted-patterns.md` - FastAPI Route Pattern documentation
