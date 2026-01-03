---
description: CryptoOrchestrator project-specific conventions and patterns
globs: ["**/*"]
alwaysApply: true
---

# CryptoOrchestrator Project Conventions

## Project Overview

CryptoOrchestrator is a professional cryptocurrency trading platform with:
- **Backend**: FastAPI (Python 3.12), PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, shadcn/ui
- **Trading**: Blockchain/DEX trading exclusively (no centralized exchanges)
- **Architecture**: Microservices, event-driven, API-first design

## File Structure

```
CryptoOrchestrator/
├── client/                 # React frontend
│   └── src/
│       ├── components/     # Reusable UI components
│       ├── pages/          # Page components
│       ├── hooks/          # Custom React hooks
│       ├── services/       # API service functions
│       ├── types/          # TypeScript type definitions
│       └── utils/          # Utility functions
├── server_fastapi/         # FastAPI backend
│   ├── routes/             # API route handlers
│   ├── models/             # SQLAlchemy models
│   ├── services/           # Business logic
│   ├── schemas/            # Pydantic schemas
│   └── middleware/         # Custom middleware
├── shared/                 # Shared TypeScript/Python code
├── alembic/                # Database migrations
├── scripts/                # Utility scripts
└── docs/                   # Documentation
```

## Naming Conventions

### Python Files
- **Modules**: `snake_case.py` (e.g., `trading_service.py`)
- **Classes**: `PascalCase` (e.g., `TradingBot`)
- **Functions**: `snake_case` (e.g., `execute_trade`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_POSITION_SIZE`)

### TypeScript Files
- **Components**: `PascalCase.tsx` (e.g., `TradingBotCard.tsx`)
- **Hooks**: `camelCase.ts` with `use` prefix (e.g., `useBot.ts`)
- **Types**: `camelCase.ts` or `PascalCase.ts` (e.g., `bot.ts` or `Bot.ts`)
- **Utilities**: `camelCase.ts` (e.g., `formatCurrency.ts`)

### Database
- **Tables**: `snake_case`, plural (e.g., `trading_bots`)
- **Columns**: `snake_case` (e.g., `created_at`)
- **Indexes**: `idx_<table>_<columns>` (e.g., `idx_bots_user_id`)

## Code Style

### Python
- **Formatter**: Black (88 char line length)
- **Linter**: Flake8
- **Type Checker**: MyPy (strict mode)
- **Line Length**: 88 characters

### TypeScript
- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checker**: TypeScript (strict mode)
- **Line Length**: 120 characters

## API Conventions

### REST Endpoints
- **Base Path**: `/api/`
- **Resources**: Plural nouns (e.g., `/api/bots`, `/api/trades`)
- **Nested Resources**: `/api/bots/{bot_id}/trades`
- **HTTP Methods**: GET (read), POST (create), PUT (update), DELETE (remove)

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

## Environment Variables

### Required Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing secret
- `ENVIRONMENT`: `development`, `staging`, or `production`

### Optional Variables
- `REQUEST_TIMEOUT`: Per-request timeout in seconds (default: 30)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Testing Standards

### Backend Tests
- **Framework**: pytest
- **Coverage Target**: 90%+
- **Location**: `server_fastapi/tests/`
- **Naming**: `test_*.py`

### Frontend Tests
- **Framework**: Vitest
- **Location**: `client/src/**/*.test.tsx`
- **Naming**: `*.test.tsx` or `*.test.ts`

### E2E Tests
- **Framework**: Playwright
- **Location**: `tests/e2e/`
- **Naming**: `*.spec.ts`

## Git Conventions

### Commit Messages
Follow Conventional Commits:
```
feat: Add grid trading strategy
fix: Resolve balance sync issue
docs: Update API documentation
refactor: Simplify bot execution logic
test: Add tests for risk manager
chore: Update dependencies
perf: Optimize database queries
```

### Branch Naming
- **Feature**: `feature/feature-name`
- **Bugfix**: `fix/bug-name`
- **Hotfix**: `hotfix/issue-name`
- **Release**: `release/v1.0.0`

## Database Migrations

### Creating Migrations
```bash
alembic revision --autogenerate -m "description"
```

### Running Migrations
```bash
alembic upgrade head
```

### Best Practices
- Always review auto-generated migrations
- Test migrations on staging before production
- Never edit existing migration files
- Use descriptive migration messages

## Logging

### Python Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Bot created", extra={"bot_id": bot_id, "user_id": user_id})
logger.error("Trade failed", exc_info=True)
```

### Frontend Logging
```typescript
// Use console.log for development
// Use proper error tracking service in production (e.g., Sentry)
console.error('Trade failed', error);
```

## Documentation

### Code Comments
- **Docstrings**: Required for all public functions/classes
- **Inline Comments**: Explain "why", not "what"
- **Type Hints**: Serve as self-documenting code

### README Files
Each major module should have a README with:
- Purpose and overview
- Installation/setup
- Usage examples
- API reference

## Deployment

### Environments
- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

### Docker
- Use `docker-compose.yml` for local development
- Use `docker-compose.prod.yml` for production
- All services should be containerized

## Performance

### Backend
- Use async/await for all I/O operations
- Implement caching with Redis
- Use database indexes appropriately
- Optimize queries with eager loading

### Frontend
- Code splitting with Vite
- Lazy load routes and components
- Use React.memo for expensive renders
- Optimize images and assets

## Security

### Never Commit
- API keys
- Private keys
- Passwords
- Environment files (except `.env.example`)

### Always Validate
- User inputs with Pydantic (backend) and Zod (frontend)
- Ethereum addresses before processing
- Amounts are positive and within limits
- User permissions before sensitive operations

## Blockchain-Specific Patterns

### Wallet Addresses
- Always validate Ethereum address format
- Use checksummed addresses (EIP-55)
- Never store private keys in code or database

### Transaction Handling
- Always check transaction status
- Implement proper error handling for failed transactions
- Use idempotency keys for retries
- Log all blockchain transactions

### DEX Trading
- Use DEX aggregators (0x, OKX, Rubic)
- Always check slippage tolerance
- Verify balances before executing swaps
- Handle transaction failures gracefully

## Best Practices

1. **Write Tests**: Every new feature should have tests
2. **Type Safety**: Always use type hints/types
3. **Error Handling**: Handle errors explicitly, never silent failures
4. **Documentation**: Document complex logic and algorithms
5. **Performance**: Profile before optimizing
6. **Security**: Never log sensitive data
7. **Code Review**: All code should be reviewed before merging
8. **Continuous Integration**: All tests must pass in CI
