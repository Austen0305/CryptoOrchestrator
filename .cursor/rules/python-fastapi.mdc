---
description: Python and FastAPI backend development guidelines for CryptoOrchestrator
globs: ["**/*.py", "server_fastapi/**/*", "alembic/**/*"]
alwaysApply: true
---

# Python & FastAPI Development Rules

You are an expert in Python 3.12 and FastAPI development for the CryptoOrchestrator platform.

## Core Principles

- **Type Safety**: Use type hints for ALL functions, parameters, and return values
- **Async First**: Prefer `async def` for I/O operations (database, API calls, file operations)
- **Pydantic v2**: Use Pydantic models for all request/response validation
- **Dependency Injection**: Use FastAPI's `Annotated` with `Depends` for dependencies
- **Error Handling**: Handle errors early, use specific exceptions, never bare `except`

## Code Style

### Formatting
- **Black**: 88 character line length (as configured in `pyproject.toml`)
- **Import Order**: Standard library → Third-party → Local imports
- **Line Length**: Maximum 88 characters (Black default)

### Naming Conventions
- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Members**: Prefix with `_` (single underscore)
- **Protected Members**: Prefix with `__` (double underscore, rarely used)

### Type Hints
```python
from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Optional[dict]:
    """Get user by ID."""
    # Implementation
```

## FastAPI Patterns

### Route Definitions
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
from pydantic import BaseModel

router = APIRouter(prefix="/api/bots", tags=["Bots"])

class BotResponse(BaseModel):
    id: int
    name: str
    strategy: str

@router.post("/", response_model=BotResponse, status_code=201)
async def create_bot(
    request: CreateBotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BotResponse:
    """Create a new trading bot."""
    # Implementation
```

### Dependency Injection Pattern
```python
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    """Database session dependency with proper cleanup."""
    async with AsyncSession(engine) as session:
        try:
            yield session
        except HTTPException:
            await session.rollback()
            raise
        finally:
            await session.close()

@router.get("/")
async def list_bots(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[BotResponse]:
    # Use db here
```

### Error Handling
```python
from fastapi import HTTPException, status

# ✅ Good: Specific error with appropriate status code
if not bot:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Bot not found",
    )

# ✅ Good: Early returns for error conditions
async def execute_trade(trade_id: int) -> dict:
    if not trade_id:
        raise ValueError("Trade ID is required")
    
    trade = await get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Happy path here
    return await process_trade(trade)
```

## SQLAlchemy Patterns

### Async Session Usage
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# ✅ Good: Use selectinload for eager loading
query = (
    select(Bot)
    .options(selectinload(Bot.user))
    .where(Bot.user_id == user_id)
)
result = await db.execute(query)
bots = result.scalars().all()

# ✅ Good: Boolean comparisons with .is_()
query = select(Bot).where(Bot.is_active.is_(True))

# ✅ Good: Transactions
async with db.begin():
    db.add(new_bot)
    await db.commit()
```

### Model Definitions
```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class TradingBot(Base, TimestampMixin):
    __tablename__ = "trading_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    strategy = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    
    user = relationship("User", back_populates="bots")
```

## Performance Optimization

### Caching
```python
from server_fastapi.services.cache import cache_service

# ✅ Good: Cache expensive operations
@cache_service.cached(ttl=300, key_prefix="bot")
async def get_bot_cached(bot_id: int) -> dict:
    return await get_bot(bot_id)
```

### Async Best Practices
- Use `async def` for all database operations
- Use `asyncio.gather()` for parallel operations when possible
- Avoid blocking I/O in async functions
- Use `await` for all async operations

## Testing

### Test Structure
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_bot(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/bots",
        json={"name": "Test Bot", "strategy": "grid"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Bot"
```

## Security

### Never Log Sensitive Data
```python
# ❌ Bad
logger.info(f"API key: {api_key}")

# ✅ Good
logger.info("API key accessed", extra={"key_id": key_id})
```

### Input Validation
- Always use Pydantic models for request validation
- Sanitize user inputs before logging
- Use SQLAlchemy ORM to prevent SQL injection
- Validate Ethereum addresses and amounts

## Documentation

### Docstrings
Use Google-style docstrings:
```python
async def execute_trade(
    trade_id: int,
    user_id: int,
    amount: float,
) -> dict:
    """
    Execute a cryptocurrency trade.
    
    Args:
        trade_id: Unique identifier for the trade
        user_id: ID of the user executing the trade
        amount: Trade amount in base currency
    
    Returns:
        Dictionary containing trade execution details
    
    Raises:
        ValueError: If amount is invalid
        HTTPException: If trade execution fails
    
    Example:
        >>> trade = await execute_trade(123, 456, 100.0)
        >>> print(trade['status'])
        'executed'
    """
```

## Project-Specific Conventions

- **Database Migrations**: Use Alembic for all schema changes
- **Environment Variables**: Use `.env` files, never hardcode secrets
- **Redis**: Check availability before using cache features
- **Request Timeout**: Respect `REQUEST_TIMEOUT` environment variable
- **Response Models**: Always define `response_model` in route decorators
