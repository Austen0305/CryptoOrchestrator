# User Rules - Split into Multiple Rules

This document provides the comprehensive rules split into **5 focused rules** for optimal organization.

---

## Rule 1: Communication & Core Quality

```markdown
# Communication & Core Quality Standards

## Communication & Response Style

- Be concise and technical in all responses
- Provide working, production-ready code examples
- Explain complex concepts when relevant, but don't over-explain basics
- Prefer practical solutions that work in production over theoretical approaches
- When uncertain about requirements, ask clarifying questions rather than making assumptions
- Include relevant code snippets inline rather than just describing concepts
- Format code examples with proper syntax highlighting and context

## Code Quality Standards

### General Principles
- Write maintainable, readable, and well-documented code
- Follow project-specific conventions and style guides (check `.cursor/rules/` directory)
- Add comments for complex business logic, algorithms, or non-obvious decisions
- Prioritize type safety: TypeScript strict mode for frontend, Python type hints for backend
- Handle errors explicitly - never use silent failures or bare `except` clauses
- Write self-documenting code with clear, descriptive naming
- Prefer composition over inheritance
- Keep functions focused on a single responsibility

### Code Style
- Use consistent formatting (follow project Prettier/Black configs)
- Maintain consistent indentation (spaces, not tabs, unless project uses tabs)
- Use meaningful variable and function names
- Avoid magic numbers - use named constants
- Keep functions/methods reasonably sized (aim for <50 lines, but prioritize clarity)

## Error Handling Patterns

### General Principles
- Handle errors early with guard clauses
- Use specific exception types, never bare `except:`
- Return meaningful error messages to clients
- Log errors with context (use structured logging)
- Use try/except around external API calls

### Backend Error Handling
```python
# ✅ Good: Specific exceptions with context
async def process_trade(trade_id: int) -> dict:
    if not trade_id:
        raise ValueError("Trade ID is required")
    
    trade = await get_trade(trade_id)
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"Trade {trade_id} not found"
        )
    
    try:
        return await execute_trade(trade)
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
```

### Frontend Error Handling
```typescript
// ✅ Good: Proper error boundaries and error states
function TradingBotCard({ botId }: { botId: number }) {
  const { data, error, isLoading } = useQuery({
    queryKey: ['bot', botId],
    queryFn: () => fetchBot(botId),
    retry: 3,
  });

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorDisplay error={error} />;
  if (!data) return null;

  return <BotDetails bot={data} />;
}
```

## Refactoring Guidelines

- Refactor incrementally, one concern at a time
- Maintain backward compatibility when possible
- Update tests when refactoring
- Document breaking changes clearly
- Consider impact on existing codebase
- Use feature flags for large refactors
- Refactor in small, reviewable commits
```

---

## Rule 2: TypeScript & Frontend Development

```markdown
# TypeScript & Frontend Development

## Type Safety

- Always use TypeScript strict mode
- Never use `any` type - use `unknown` if type is truly unknown, then narrow it
- Define explicit types for function parameters and return values
- Use interfaces for object shapes, types for unions/intersections
- Leverage TypeScript's utility types (Pick, Omit, Partial, etc.)
- Prefer `const` assertions for literal types

## React Best Practices

- Use functional components with hooks (never class components)
- Use React Query (TanStack Query) for server state management
- Use local state (`useState`) only for UI state, not server state
- Extract reusable logic into custom hooks
- Use `React.memo`, `useMemo`, and `useCallback` appropriately (don't over-optimize)
- Handle loading and error states explicitly
- Use proper cleanup in `useEffect` hooks
- Prefer composition patterns over prop drilling

## Component Patterns

```typescript
// ✅ Good: Functional component with proper typing
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export function Button({ label, onClick, disabled = false }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}

// ❌ Bad: Using 'any' or missing types
export function Button(props: any) { ... }
```

## State Management

- Use React Query for all server state
- Use Zustand or Context API for global client state (only when needed)
- Use local state for component-specific UI state
- Avoid prop drilling - use context or state management library if more than 2 levels deep

## React Query Patterns

### Data Fetching
```typescript
// ✅ Good: Query with proper error handling
const { data, isLoading, error } = useQuery({
  queryKey: ['trades', userId],
  queryFn: () => api.getTrades(userId),
  retry: 3,
  staleTime: 30000, // 30 seconds
});

// ✅ Good: Mutations
const mutation = useMutation({
  mutationFn: (data: CreateBotRequest) => api.createBot(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['bots'] });
    toast.success('Bot created successfully');
  },
  onError: (error) => {
    toast.error(error.message);
  },
});
```

## Performance Optimization

### Memoization
```typescript
// ✅ Good: Memoize expensive computations
const expensiveValue = useMemo(() => {
  return calculatePortfolioValue(holdings);
}, [holdings]);

// ✅ Good: Memoize callbacks
const handleUpdate = useCallback((id: number) => {
  updateBot(id);
}, [updateBot]);

// ✅ Good: Memoize components
export const BotCard = React.memo(({ bot }: { bot: BotConfig }) => {
  return <div>{bot.name}</div>;
});
```

## Form Handling

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const botSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  strategy: z.enum(['grid', 'dca', 'momentum']),
  amount: z.number().positive('Amount must be positive'),
});

type BotFormData = z.infer<typeof botSchema>;

export function BotForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BotFormData>({
    resolver: zodResolver(botSchema),
  });

  const onSubmit = (data: BotFormData) => {
    createBot(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} />
      {errors.name && <span>{errors.name.message}</span>}
    </form>
  );
}
```

## Frontend Performance

- Code split routes and large components
- Lazy load components and routes
- Use React.memo for expensive renders (but don't overuse)
- Optimize images (use WebP, lazy loading)
- Use React Query's caching and stale-while-revalidate patterns
- Debounce/throttle user input handlers when appropriate

## When Working on CryptoOrchestrator Frontend

- Always review project-specific rules in `.cursor/rules/react-typescript.mdc`
- Use React Query for all server state
- Use functional components with hooks
- Handle loading and error states explicitly
- Use TypeScript strict mode

## MCP Tools for Frontend Development

- Use `cursor-browser-extension` MCP for testing React components in browser
- Always call `browser_snapshot` before clicking/typing to get element refs
- Use browser MCP for E2E testing and user flow verification
- Use `context7` MCP to find React/TypeScript library documentation
- Use `stackoverflow` MCP for React/TypeScript common issues

## Extension Usage

- Use **Error Lens** to see TypeScript/React errors inline
- Use **ESLint** for code quality - fix errors immediately
- Use **Prettier** for consistent formatting (format on save enabled)
- Use **Coverage Gutters** to see test coverage
- Use **Path Intellisense** for `@/*` import autocomplete
```

---

## Rule 3: Python & FastAPI Backend

```markdown
# Python & FastAPI Backend Development

## Type Hints

- Use type hints for ALL functions, including parameters and return types
- Use `typing` module for complex types (List, Dict, Optional, Union, etc.)
- Use `Annotated` for FastAPI dependencies
- Prefer Python 3.9+ type syntax (`list[str]` over `List[str]`)

## Async/Await

- Use `async def` for all I/O operations (database, API calls, file operations)
- Use `await` for all async operations
- Use `asyncio.gather()` for parallel async operations when appropriate
- Avoid blocking I/O in async functions
- Properly handle async context managers

## FastAPI Patterns

```python
# ✅ Good: Type hints, async, dependency injection
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    # Implementation

# ❌ Bad: No types, synchronous, no dependency injection
def get_user(user_id, db):
    # Implementation
```

## Dependency Injection

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

@router.post('/bots', response_model=BotResponse)
async def create_bot(
    request: CreateBotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BotResponse:
    return await service.create_bot(request, user_id=current_user['id'], db=db)
```

## Pydantic Validation

```python
from pydantic import BaseModel, validator

class TradeRequest(BaseModel):
    amount: float
    token_address: str
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

## SQLAlchemy Patterns

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
```

## Code Organization

- Group imports: standard library → third-party → local
- Use dependency injection for shared resources
- Keep route handlers thin - move business logic to services
- Use Pydantic models for all request/response validation

## Backend Performance

- Use async/await for all I/O operations
- Implement caching (Redis) for frequently accessed data
- Optimize database queries (avoid N+1 problems, use eager loading)
- Use database indexes appropriately
- Profile before optimizing - measure actual bottlenecks
- Use connection pooling for databases

## When Working on CryptoOrchestrator Backend

- Always review project-specific rules in `.cursor/rules/python-fastapi.mdc`
- Use FastAPI dependency injection patterns
- Use async/await for database operations
- Handle errors with HTTPException
- Never log sensitive data

## MCP Tools for Backend Development

- Use `filesystem` MCP for file operations instead of terminal
- Use `git` MCP for all version control operations
- Use `context7` MCP to find FastAPI/Python library documentation
- Use `stackoverflow` MCP for Python/FastAPI common problems
- Use `brave-search` MCP for current API documentation
- Use `sequential-thinking` MCP for complex architectural decisions

## Extension Usage

- Use **Python** + **Pylance** with strict type checking
- Use **Black Formatter** for Python code (88 char line length)
- Use **Python Docstring Generator** for auto-generating docstrings
- Use **Python Test Explorer** for running pytest tests
- Use **REST Client** for testing API endpoints
- Use **Coverage Gutters** to see test coverage

---

## Rule 4: Security & Blockchain

```markdown
# Security & Blockchain Development

## Critical Security Rules

### Never Do These
- **NEVER** suggest storing secrets, API keys, or private keys in code, environment files, or commit messages
- **NEVER** log sensitive data (passwords, tokens, private keys, credit card numbers)
- **NEVER** use bare `except:` clauses - always catch specific exceptions
- **NEVER** trust user input without validation

### Always Do These
- Always validate and sanitize user inputs (use Pydantic/Zod schemas)
- Use parameterized queries for database operations (SQLAlchemy ORM handles this)
- Implement proper authentication and authorization checks
- Follow principle of least privilege
- Use HTTPS in production (never HTTP for sensitive data)
- Implement rate limiting for public APIs

## Input Validation

### Backend Validation
```python
from pydantic import BaseModel, validator

class TradeRequest(BaseModel):
    amount: float
    token_address: str
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

### Frontend Validation
```typescript
import { z } from 'zod';

const tradeSchema = z.object({
  amount: z.number().positive('Amount must be positive'),
  tokenAddress: z.string()
    .regex(/^0x[a-fA-F0-9]{40}$/, 'Invalid Ethereum address'),
});
```

## Logging Security

```python
# ✅ Good: Structured logging with context (no sensitive data)
logger.info(
    "Bot created successfully",
    extra={
        "bot_id": bot.id,
        "user_id": user.id,
        "strategy": bot.strategy,
    }
)

# ❌ Bad: Logging sensitive data
logger.info(f"User logged in with password: {password}")  # NEVER DO THIS
logger.debug(f"API key: {api_key}")  # NEVER DO THIS
```

## Blockchain Security

### Private Key Management
- **NEVER** store private keys or seed phrases anywhere in code or database
- Use key management services (AWS KMS, HashiCorp Vault, HSM)
- Store only key IDs or references in database
- Retrieve keys at runtime, never cache
- Clear keys from memory after use

### Transaction Security
```python
# ✅ Good: Validate before executing
async def execute_dex_swap(
    sell_token: str,
    buy_token: str,
    amount: float,
    slippage_percentage: float,
    user_id: int,
):
    # Validate inputs
    if slippage_percentage > MAX_SLIPPAGE:
        raise ValueError(f"Slippage exceeds maximum of {MAX_SLIPPAGE}%")
    
    # Verify user balance
    balance = await get_user_balance(user_id, sell_token)
    if balance < amount:
        raise ValueError("Insufficient balance")
    
    # Get and validate quote
    quote = await get_dex_quote(sell_token, buy_token, amount)
    if quote.min_amount_out < expected_amount * (1 - slippage_percentage):
        raise ValueError("Quote does not meet slippage requirements")
    
    # Execute with idempotency
    swap_id = generate_idempotency_key(user_id, sell_token, buy_token, amount)
    return await execute_swap(quote, swap_id)
```

### Ethereum Address Validation
```python
from eth_utils import is_address, to_checksum_address

def validate_ethereum_address(address: str) -> str:
    if not is_address(address):
        raise ValueError("Invalid Ethereum address")
    return to_checksum_address(address)  # EIP-55 checksum
```

## Authentication & Authorization

- Validate JWT tokens on every request
- Require 2FA for sensitive operations (withdrawals, trades)
- Implement proper session management
- Use secure password hashing (bcrypt)
- Implement account lockout after failed attempts

## API Security

- Use CORS properly (never use `["*"]` in production)
- Implement rate limiting per endpoint
- Validate all request bodies with Pydantic
- Use HTTPS enforcement in production
- Implement request signing for sensitive operations

## When Working on CryptoOrchestrator Security

- Always review project-specific rules in `.cursor/rules/security-blockchain.mdc`
- Never suggest storing private keys
- Always validate Ethereum addresses
- Verify balances before transactions
- Use idempotency keys for retries

## MCP Tools for Security & Blockchain

- Use `coingecko` MCP for cryptocurrency price data
- Use `brave-search` MCP to research security best practices
- Use `stackoverflow` MCP for security-related coding questions
- Use `context7` MCP for blockchain library documentation (web3.py, wagmi)
- Use `memory` MCP to store security patterns and decisions

## Extension Usage

- Use **Snyk** extension to scan for security vulnerabilities
- Use **SonarLint** for code quality and security analysis
- Address security warnings immediately
- Review security suggestions before committing

---

## Rule 5: Testing, Documentation & Standards

```markdown
# Testing, Documentation & Standards

## Testing Standards

### General Testing Philosophy
- Write tests for new features and bug fixes
- Ensure tests are meaningful and cover edge cases
- Prefer integration tests for critical business logic
- Use mocking/spying appropriately for external dependencies
- Maintain test coverage above 85% for new code
- Tests should be fast, isolated, and repeatable
- Use descriptive test names that explain what is being tested

### Test Structure
```python
# ✅ Good: Clear test structure
def test_create_bot_requires_authentication(client):
    # Arrange
    bot_data = {"name": "Test Bot", "strategy": "grid"}
    
    # Act
    response = client.post("/api/bots", json=bot_data)
    
    # Assert
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()
```

### When to Write Tests
- All new features require tests
- Bug fixes require regression tests
- Refactored code should maintain or improve test coverage
- Critical paths require integration tests

## Documentation Standards

### Code Comments
- Write clear docstrings for all public functions, classes, and modules
- Document "why" not "what" - code should be self-explanatory
- Use Google-style docstrings for Python
- Use JSDoc comments for complex TypeScript functions
- Keep comments up-to-date with code changes

### Docstring Examples
```python
def calculate_portfolio_value(
    holdings: list[dict],
    prices: dict[str, float],
) -> float:
    """
    Calculate total portfolio value from holdings and current prices.
    
    Args:
        holdings: List of holding dicts with 'symbol' and 'quantity' keys
        prices: Dictionary mapping symbols to current prices
    
    Returns:
        Total portfolio value as a float
    
    Raises:
        ValueError: If holdings list is empty or prices dict is missing symbols
    
    Example:
        >>> holdings = [{"symbol": "BTC", "quantity": 0.5}]
        >>> prices = {"BTC": 50000.0}
        >>> calculate_portfolio_value(holdings, prices)
        25000.0
    """
```

### README Files
- Include purpose and overview
- Provide installation/setup instructions
- Include usage examples
- Document API reference for libraries/modules
- Keep README files current with code changes

## Git & Version Control

### Commit Messages
Follow Conventional Commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks
- `perf:` Performance improvements
- `style:` Code style changes (formatting)

Examples:
- `feat: Add grid trading strategy`
- `fix: Resolve balance sync issue`
- `docs: Update API documentation`

### Branch Strategy
- Use descriptive branch names: `feature/add-dark-mode`, `fix/login-bug`
- Keep branches focused on a single feature/fix
- Rebase before merging to keep history clean
- Delete merged branches

## API Design Principles

### RESTful APIs
- Use HTTP methods correctly (GET, POST, PUT, DELETE)
- Use resource-based URLs (`/api/bots`, not `/api/getBots`)
- Return consistent response formats
- Use appropriate HTTP status codes
- Implement pagination for list endpoints
- Version APIs when making breaking changes

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

### Error Response Format
```json
{
  "error": {
    "code": "BOT_NOT_FOUND",
    "message": "Bot with ID 123 not found",
    "details": { ... }
  }
}
```

## Database Best Practices

### Query Optimization
- Use indexes on frequently queried columns
- Avoid N+1 queries - use eager loading
- Use pagination for large result sets
- Use transactions for multi-step operations
- Use connection pooling
- Monitor slow queries

### Migration Management
- Always review auto-generated migrations
- Test migrations on staging before production
- Never edit existing migration files
- Use descriptive migration messages
- Keep migrations small and focused

## Dependency Management

- Keep dependencies up-to-date with security patches
- Use lock files (package-lock.json, requirements.txt)
- Pin major versions, allow patch updates
- Regularly audit for vulnerabilities
- Remove unused dependencies
- Document why specific versions are required
```

---

## 📋 Summary

**Total**: 5 focused rules, each ~100-250 lines

1. **Communication & Core Quality** (~150 lines)
2. **TypeScript & Frontend** (~200 lines)
3. **Python & FastAPI** (~200 lines)
4. **Security & Blockchain** (~200 lines)
5. **Testing & Documentation** (~150 lines)

**Setup**: Copy each rule into separate User Rules in Cursor Settings!

---

See [USER_RULES_ORGANIZATION.md](USER_RULES_ORGANIZATION.md) for detailed setup instructions.
