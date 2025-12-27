# Code Style Guide

Coding standards and style guidelines for CryptoOrchestrator.

## Table of Contents

1. [Python Style Guide](#python-style-guide)
2. [TypeScript Style Guide](#typescript-style-guide)
3. [Database Style Guide](#database-style-guide)
4. [API Style Guide](#api-style-guide)
5. [Documentation Standards](#documentation-standards)

---

## Python Style Guide

### General Principles

- **PEP 8**: Follow PEP 8 style guide
- **Type Hints**: Use type hints for all functions
- **Async/Await**: Prefer async/await over callbacks
- **Error Handling**: Use specific exceptions, not bare `except`

### Code Formatting

Use `ruff` for formatting and linting:

```bash
ruff format .
ruff check .
```

### Naming Conventions

- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_` (single underscore)

### Example

```python
from typing import Optional, List
from datetime import datetime

class TradingBot:
    """Trading bot class."""
    
    MAX_POSITION_SIZE: int = 10000
    
    def __init__(self, bot_id: int, strategy: str):
        self.bot_id = bot_id
        self.strategy = strategy
        self._is_active = False
    
    async def execute_trade(
        self,
        symbol: str,
        amount: float,
    ) -> Optional[dict]:
        """Execute a trade."""
        if not self._is_active:
            raise ValueError("Bot is not active")
        
        # Implementation
        return {"status": "success"}
```

### Import Organization

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
from datetime import datetime
from typing import Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select

# Local
from ..models import Bot
from ..services import TradingService
```

---

## TypeScript Style Guide

### General Principles

- **TypeScript Strict Mode**: Always use strict mode
- **Type Safety**: Avoid `any`, use proper types
- **React Hooks**: Follow React hooks rules
- **Functional Components**: Prefer functional components

### Code Formatting

Use ESLint and Prettier:

```bash
npm run lint
npm run format
```

### Naming Conventions

- **Functions/Components**: `PascalCase` (React components), `camelCase` (functions)
- **Variables**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Types/Interfaces**: `PascalCase`

### Example

```typescript
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface BotConfig {
  id: number;
  name: string;
  strategy: string;
}

const MAX_POSITION_SIZE = 10000;

export function TradingBotCard({ botId }: { botId: number }) {
  const [isActive, setIsActive] = useState(false);
  
  const { data: bot } = useQuery<BotConfig>({
    queryKey: ['bot', botId],
    queryFn: async () => {
      const response = await fetch(`/api/bots/${botId}`);
      return response.json();
    },
  });
  
  if (!bot) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>{bot.name}</h2>
      <p>Strategy: {bot.strategy}</p>
    </div>
  );
}
```

### File Organization

```
src/
  components/
    BotCard/
      BotCard.tsx
      BotCard.test.tsx
      index.ts
  hooks/
    useBot.ts
  services/
    botService.ts
  types/
    bot.ts
```

---

## Database Style Guide

### Table Naming

- **Tables**: `snake_case`, plural (e.g., `trading_bots`)
- **Columns**: `snake_case` (e.g., `created_at`)
- **Indexes**: `idx_<table>_<columns>` (e.g., `idx_bots_user_id`)

### Column Types

- **IDs**: `Integer`, primary key
- **Timestamps**: `DateTime`, with timezone
- **Strings**: `String(length)` with appropriate length
- **JSON**: `JSON` for flexible data
- **Booleans**: `Boolean`, not `Integer`

### Example

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from .base import Base, TimestampMixin

class TradingBot(Base, TimestampMixin):
    __tablename__ = "trading_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    strategy = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        Index("idx_bots_user_id", "user_id", "created_at"),
    )
```

---

## API Style Guide

### RESTful Design

- **Resources**: Use nouns, plural (e.g., `/api/bots`)
- **Actions**: Use HTTP methods (GET, POST, PUT, DELETE)
- **Nested Resources**: `/api/bots/{bot_id}/trades`
- **Query Parameters**: For filtering, pagination

### Response Format

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

### Error Format

```json
{
  "error": {
    "code": "BOT_NOT_FOUND",
    "message": "Bot with ID 123 not found",
    "details": { ... }
  }
}
```

### Example

```python
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/bots", tags=["Bots"])

class BotResponse(BaseModel):
    id: int
    name: str
    strategy: str

@router.get("/", response_model=List[BotResponse])
async def list_bots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List trading bots."""
    # Implementation
    return {"data": bots, "meta": {"page": page, "per_page": per_page}}
```

---

## Documentation Standards

### Code Comments

- **Docstrings**: Use Google-style docstrings
- **Inline Comments**: Explain "why", not "what"
- **Type Hints**: Self-documenting code

### Example

```python
def calculate_pnl(
    entry_price: float,
    exit_price: float,
    quantity: float,
) -> float:
    """
    Calculate profit and loss for a trade.
    
    Args:
        entry_price: Price at which position was opened
        exit_price: Price at which position was closed
        quantity: Quantity of asset traded
    
    Returns:
        Profit/loss amount (positive for profit, negative for loss)
    
    Raises:
        ValueError: If quantity is negative
    """
    if quantity < 0:
        raise ValueError("Quantity must be positive")
    
    return (exit_price - entry_price) * quantity
```

### README Files

Every module should have a README with:
- Purpose and overview
- Installation/setup
- Usage examples
- API reference
- Contributing guidelines

---

## Testing Standards

### Test Naming

- **Test Files**: `test_<module>.py` or `<module>.test.ts`
- **Test Functions**: `test_<functionality>`
- **Test Classes**: `Test<ClassName>`

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

def test_calculate_pnl_profit():
    """Test PnL calculation for profitable trade."""
    result = calculate_pnl(entry_price=100, exit_price=110, quantity=10)
    assert result == 100

def test_calculate_pnl_loss():
    """Test PnL calculation for losing trade."""
    result = calculate_pnl(entry_price=100, exit_price=90, quantity=10)
    assert result == -100
```

---

## Git Commit Messages

Follow conventional commits:

```
feat: Add grid trading strategy
fix: Resolve balance sync issue
docs: Update API documentation
refactor: Simplify bot execution logic
test: Add tests for risk manager
chore: Update dependencies
```

---

## Additional Resources

- [Python PEP 8](https://pep8.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Style Guide](https://react.dev/)
