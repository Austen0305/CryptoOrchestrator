# CryptoOrchestrator - Developer Guide

**Complete guide for developers working on the CryptoOrchestrator project**

## 🚀 Quick Start

### Setup Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd Crypto-Orchestrator

# 2. Quick setup
npm run quick-start

# 3. Start development
npm run start:all
```

### Verify Setup

```bash
# Run comprehensive checks
npm run check:all

# Or individual checks
npm run verify:startup
npm run verify:features
npm run analyze:performance
npm run check:dependencies
npm run check:quality
```

## 📁 Project Structure

```
Crypto-Orchestrator/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utilities and configs
│   │   └── types/         # TypeScript types
│   └── vite.config.ts     # Vite configuration
│
├── server_fastapi/        # FastAPI backend
│   ├── routes/            # API route handlers (660 routes)
│   ├── services/          # Business logic services
│   ├── models/            # Database models
│   ├── repositories/      # Data access layer
│   ├── middleware/        # Request/response middleware
│   ├── dependencies/      # Dependency injection
│   └── utils/             # Utility functions
│
├── scripts/               # Utility scripts
│   ├── setup/            # Setup scripts
│   ├── verification/     # Verification scripts
│   ├── utilities/        # Development utilities
│   └── monitoring/       # Performance monitoring
│
└── docs/                  # Documentation
```

## 🛠️ Development Workflow

### 1. Making Changes

```bash
# Start development servers
npm run start:all

# Or individually:
npm run dev:fastapi  # Backend (Terminal 1)
npm run dev          # Frontend (Terminal 2)
```

### 2. Code Quality

```bash
# Check code quality
npm run check:quality

# Format code
npm run format        # Frontend
npm run format:py    # Backend (black)

# Lint code
npm run lint         # Frontend
npm run lint:py      # Backend (flake8)
```

### 3. Testing

```bash
# Run tests
npm test             # Backend tests
npm run test:frontend # Frontend tests
npm run test:e2e     # E2E tests
```

### 4. Verification

```bash
# Verify everything works
npm run check:all

# Individual verifications
npm run verify:startup      # Startup verification
npm run verify:features     # Feature verification
npm run analyze:performance # Performance analysis
npm run check:dependencies  # Dependency check
```

## 📝 Code Standards

### Python (Backend)

- **Style**: Follow PEP 8, use Black for formatting
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Include docstrings for all public functions/classes
- **Error Handling**: Use try/except with proper logging
- **Async**: Use async/await for I/O operations

### TypeScript (Frontend)

- **Style**: Follow ESLint rules, use Prettier for formatting
- **Types**: Use TypeScript strict mode
- **Components**: Functional components with hooks
- **Error Handling**: Use ErrorBoundary components

## 🔍 Common Tasks

### Adding a New Route

1. Create route file in `server_fastapi/routes/`
2. Define router with `router = APIRouter()`
3. Add route handlers with proper error handling
4. Register in `server_fastapi/main.py` using `_safe_include()`

Example:
```python
from fastapi import APIRouter, Depends
from ..dependencies.auth import get_current_user
from ..database import get_db_session

router = APIRouter()

@router.get("/example")
async def get_example(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        # Your logic here
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
```

### Adding a New Service

1. Create service file in `server_fastapi/services/`
2. Implement service class with async methods
3. Add proper error handling and logging
4. Use dependency injection in routes

### Adding Caching

```python
from ..middleware.cache_manager import cached

@router.get("/data")
@cached(ttl=60, prefix="data")  # Cache for 60 seconds
async def get_data():
    # Your logic
    return data
```

### Adding Pagination

```python
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

@router.get("/items")
async def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = select(Item)
    query = QueryOptimizer.paginate_query(query, page, page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ResponseOptimizer.paginate_response(items, page, page_size)
```

## 🐛 Debugging

### Backend Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
npm run dev:fastapi

# Check logs
tail -f logs/fastapi.log

# Database query logging
export SQLALCHEMY_ECHO=true
npm run dev:fastapi
```

### Frontend Debugging

```bash
# Start with dev tools
npm run dev

# Check browser console
# Use React DevTools extension
```

### Performance Debugging

```bash
# Analyze performance
npm run analyze:performance

# Monitor performance
npm run monitor:performance
```

## 📚 Useful Commands

### Development
- `npm run dev` - Start frontend dev server
- `npm run dev:fastapi` - Start backend dev server
- `npm run start:all` - Start all services

### Verification
- `npm run verify:startup` - Verify startup
- `npm run verify:features` - Verify features
- `npm run check:all` - Run all checks

### Utilities
- `npm run health:check` - Check service health
- `npm run cache:clear` - Clear all caches
- `npm run analyze:performance` - Analyze performance
- `npm run check:dependencies` - Check dependencies
- `npm run check:quality` - Check code quality
- `npm run optimize:responses` - Analyze response optimization

### Database
- `npm run migrate` - Run migrations
- `npm run migrate:create` - Create new migration
- `npm run migrate:rollback` - Rollback last migration

## 🎯 Best Practices

### Error Handling

Always use try/except with proper logging:

```python
try:
    result = await service.do_something()
    return result
except HTTPException:
    raise  # Let HTTPExceptions propagate
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True, extra={"user_id": user_id})
    raise HTTPException(status_code=500, detail="Internal error")
```

### Logging

Use structured logging with context:

```python
logger.info(
    "Operation completed",
    extra={
        "user_id": user_id,
        "operation": "operation_name",
        "duration_ms": duration,
    }
)
```

### Database Queries

Always use eager loading to prevent N+1 queries:

```python
from sqlalchemy.orm import selectinload

query = select(Model).options(selectinload(Model.relationship))
```

### Caching

Add caching to frequently accessed data:

```python
@cached(ttl=60, prefix="data")
async def get_data():
    # Expensive operation
    return data
```

## 🔐 Security

- Always validate user input
- Use dependency injection for authentication
- Never log sensitive data (passwords, tokens, keys)
- Use parameterized queries (SQLAlchemy handles this)
- Follow security best practices in `docs/security/`

## 📊 Performance

- Use eager loading for relationships
- Add caching to expensive operations
- Use pagination for list endpoints
- Monitor performance with `npm run analyze:performance`

## 🧪 Testing

- Write unit tests for services
- Write integration tests for routes
- Use E2E tests for critical flows
- Maintain test coverage > 80%

## 📖 Documentation

- Update README.md for major changes
- Add docstrings to all public functions
- Update API docs (auto-generated from FastAPI)
- Document breaking changes in CHANGELOG.md

## 🆘 Getting Help

- Check `docs/TROUBLESHOOTING_RUNTIME.md` for common issues
- Run `npm run check:all` for diagnostics
- Review logs in `logs/` directory
- Check API docs at http://localhost:8000/docs

## 🎓 Learning Resources

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/
- TypeScript: https://www.typescriptlang.org/

---

**Happy coding!** 🚀

