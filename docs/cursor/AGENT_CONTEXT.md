# Agent Context - Quick Reference

**Last Updated:** 2025-01-19  
**Project Status:** 95% complete, production-ready

---

## 🎯 Current Project State

- **Status:** Production-ready, 95% complete
- **Last Major Update:** 2025-01-19
- **Critical Issues:** None
- **Next Priorities:** 
  - Mobile native initialization (88% complete)
  - Component test coverage gaps
  - E2E test coverage improvements

---

## 📁 Key Files to Know

### Backend
- **Main Entry:** `server_fastapi/main.py`
- **Routes:** `server_fastapi/routes/`
- **Services:** `server_fastapi/services/`
- **Models:** `server_fastapi/models/`
- **Schemas:** `server_fastapi/schemas/`

### Frontend
- **Main App:** `client/src/App.tsx`
- **Pages:** `client/src/pages/`
- **Components:** `client/src/components/`
- **Hooks:** `client/src/hooks/`
- **Services:** `client/src/services/`

### Configuration
- **API Spec:** `docs/openapi.json`
- **Environment:** `.env.example`
- **Package Config:** `package.json`, `requirements.txt`
- **TypeScript Config:** `tsconfig.json`
- **Tailwind Config:** `tailwind.config.ts`

### Documentation
- **Todo List:** `Todo.md` (comprehensive task list)
- **Changelog:** `CHANGELOG.md`
- **README:** `README.md`
- **Rules:** `.cursor/rules/*.mdc`

---

## 🔧 Common Patterns

### Backend Routes
```python
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/endpoint")
async def get_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseModel:
    # Use repository pattern
    result = await repository.get_data(user_id=current_user["id"], db=db)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return ResponseModel.from_orm(result)
```

### Frontend Hooks
```typescript
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';

export function useData() {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['data', user?.id],
    queryFn: () => api.getData(user.id),
    enabled: !!user,
    staleTime: 30000,
  });
}
```

### Services
- **Pattern:** Stateless services with repository delegation
- **Location:** `server_fastapi/services/`
- **Example:** `server_fastapi/services/trading/dex_trading_service.py`

### Repositories
- **Pattern:** Async operations, eager loading with `selectinload`
- **Location:** `server_fastapi/repositories/`
- **Example:** `server_fastapi/repositories/trading_bot_repository.py`

---

## 🧪 Testing Patterns

### Backend (pytest)
- **Location:** `server_fastapi/tests/`
- **Command:** `pytest server_fastapi/tests/`
- **Fixtures:** `conftest.py` provides `client`, `auth_headers`, `db_session`

### Frontend (Vitest)
- **Location:** `client/src/**/*.test.tsx`
- **Command:** `npm run test:frontend`
- **Setup:** `client/vitest.config.ts`

### E2E (Playwright)
- **Location:** `tests/e2e/`
- **Command:** `npm run test:e2e:complete`
- **Config:** `playwright.config.ts`

---

## 🚀 Quick Commands

### Development
```bash
# Start all services
npm run start:all

# Start backend only
npm run dev:fastapi

# Start frontend only
npm run dev
```

### Testing
```bash
# All tests
npm run test:e2e:complete

# Backend only
pytest server_fastapi/tests/

# Frontend only
npm run test:frontend

# E2E only
npm run test:e2e
```

### Code Quality
```bash
# Format Python
npm run format:py

# Format TypeScript/React
npm run format

# Lint Python
npm run lint:py

# Type check
npm run check
```

### Database
```bash
# Run migrations
npm run migrate

# Create migration
npm run migrate:create -- "description"

# Rollback
npm run migrate:rollback
```

---

## 📋 Project Structure

```
CryptoOrchestrator/
├── client/              # React frontend
│   └── src/
│       ├── components/  # Reusable UI components
│       ├── pages/       # Page components
│       ├── hooks/       # Custom React hooks
│       ├── services/    # API service functions
│       ├── types/       # TypeScript types
│       └── utils/       # Utility functions
├── server_fastapi/      # FastAPI backend
│   ├── routes/         # API route handlers
│   ├── models/         # SQLAlchemy models
│   ├── services/       # Business logic
│   ├── schemas/        # Pydantic schemas
│   ├── repositories/   # Data access layer
│   └── middleware/     # Custom middleware
├── mobile/             # React Native app
├── tests/              # E2E tests (Playwright)
├── alembic/            # Database migrations
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

---

## 🔑 Key Technologies

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL (asyncpg)
- **ORM:** SQLAlchemy (async)
- **Cache:** Redis
- **Migrations:** Alembic

### Frontend
- **Framework:** React 18
- **Language:** TypeScript 5.9+
- **State:** TanStack Query (React Query)
- **Styling:** TailwindCSS + shadcn/ui
- **Build:** Vite

### Testing
- **Backend:** pytest
- **Frontend:** Vitest
- **E2E:** Playwright

---

## ⚠️ Important Notes

### Security
- **Never** store private keys in code
- **Always** validate user input (Pydantic/Zod)
- **Never** log sensitive data
- **Always** use parameterized queries (SQLAlchemy handles this)

### Performance
- Use async/await for all I/O operations
- Implement caching with Redis
- Use eager loading to prevent N+1 queries
- Optimize database queries with indexes

### Code Quality
- Follow project conventions (`.cursor/rules/`)
- Write tests for new features
- Use type hints/types everywhere
- Handle errors explicitly

---

## 📚 Documentation Locations

- **Project Rules:** `.cursor/rules/*.mdc`
- **API Documentation:** `docs/openapi.json`
- **Setup Guides:** `docs/guides/`
- **Development:** `docs/development/`
- **Deployment:** `docs/deployment/`

---

## 🎯 Current Priorities

1. **Mobile Native Initialization** (88% complete)
   - Need to run `react-native init` or use Expo
   - All TypeScript code is ready

2. **Component Test Coverage**
   - Priority: `DEXTradingPanel.tsx`, `Wallet.tsx`, `TradingHeader.tsx`
   - Use existing test files as templates

3. **E2E Test Coverage**
   - Missing flows: Portfolio, Settings, Withdrawal with 2FA
   - Use existing E2E tests as templates

---

## 💡 Tips for Agent

1. **Always check existing patterns** before creating new code
2. **Use existing tests as templates** for new tests
3. **Follow the repository pattern** for data access
4. **Use React Query hooks** for all server state
5. **Check `.cursor/rules/`** for project-specific patterns
6. **Read `Todo.md`** to understand current priorities
7. **Use MCPs** for documentation lookup (context7) and API testing (api-tester)

---

**For detailed patterns, see:** `.cursor/rules/*.mdc`  
**For task list, see:** `Todo.md`  
**For quick reference, see:** `docs/cursor/PRIORITY_TASKS.md`
