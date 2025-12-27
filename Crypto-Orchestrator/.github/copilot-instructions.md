---
title: "CryptoOrchestrator – AI Agent Working Rules"
description: "Concise, project-specific guidance for productive AI development"
---

# CryptoOrchestrator – AI Agent Working Rules

Concise guidance focused on discoverable patterns in the code. Reference actual files when describing conventions.

---

## 🏗️ Architecture at a Glance

**Monorepo** – 4-tier SaaS platform for crypto trading automation:
- **Backend**: FastAPI (Python 3.12) in `server_fastapi/` – source of truth
- **Frontend**: React 18 + TypeScript + Vite in `client/src/`
- **Desktop**: Electron wrapper in `electron/` – launches FastAPI + frontend bundle
- **Mobile**: React Native in `mobile/` – shares backend API layer

**Key principle**: Python/FastAPI is authoritative. Legacy Node code (`server/`) is deprecated; ignore it. TypeScript types in `client/src/types/` should mirror Pydantic models.

**Development flow**:
- Terminal 1: `npm run dev:fastapi` → FastAPI auto-reload on http://localhost:8000
- Terminal 2: `npm run dev` → Vite on http://localhost:5173
- API Docs: http://localhost:8000/docs (Swagger)

---

## 📁 Key Directories

| Path | Purpose |
|------|---------|
| `server_fastapi/main.py` | FastAPI app: middleware (CORS, auth, rate limit, Redis), router registration |
| `server_fastapi/routes/` | ~30 thin route files (e.g., `bots.py`, `trades.py`, `risk.py`); Pydantic validation only |
| `server_fastapi/services/` | Stateless business logic; each service handles one domain (e.g., `BotService`, `RiskService`) |
| `server_fastapi/models/` | SQLAlchemy ORM (Bot, Trade, User, Portfolio, etc.) |
| `server_fastapi/repositories/` | Data access layer; abstract queries/filters |
| `server_fastapi/dependencies/` | FastAPI `Depends()` factories: auth, service injection, DB sessions |
| `server_fastapi/tests/` | pytest suites (~80+); run `npm test` enforces ≥90% coverage |
| `client/src/lib/api.ts` | Single source of API client functions |
| `client/src/hooks/` | React Query hooks wrapping API calls; cache invalidation |
| `client/src/components/` | ~80 UI components; use React.memo for expensive renders |
| `client/src/types/` | TypeScript interfaces (keep aligned with backend Pydantic models) |

---

## 🎯 Backend Patterns

### Route Structure
- **Always use `/api/<domain>` prefix** (e.g., `/api/bots`, `/api/trades`)
- **Register in `main.py`**: `app.include_router(router, prefix='/api/bots', tags=['Bots'])`
- **Use `Annotated[Type, Depends(...)]` for all dependencies** (primary pattern)

**Example route** (from [server_fastapi/routes/bots.py](../server_fastapi/routes/bots.py)):
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from pydantic import BaseModel

router = APIRouter()

class CreateBotRequest(BaseModel):
    name: str
    strategy: str

@router.post('/bots', response_model=dict)
async def create_bot(
    req: CreateBotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[BotService, Depends(get_bot_service)],
):
    return await service.create_bot(req, user_id=current_user['id'])
```

### Error Handling
- Use `HTTPException(status_code=..., detail='...')` for known errors
- Log unexpected errors with `logger.error(..., exc_info=True, extra={'user_id': user_id})`
- Production: sanitize responses (no stack traces)

### Testing Backend
```bash
npm test                           # pytest with coverage report
npm run test:watch               # Reload on file change
```

Tests follow pytest structure with fixtures in `conftest.py`. Use `TestClient` for route testing:
```python
def test_create_bot(client: TestClient):
    response = client.post('/api/bots', json={'name': 'Bot1', 'strategy': 'MA'})
    assert response.status_code == 201
```

---

## 🎨 Frontend Patterns

### API Integration (3-step workflow)
1. **Define endpoint** in `client/src/lib/api.ts`:
   ```typescript
   export const botApi = {
     getBots: () => apiClient.get('/bots'),
     createBot: (data) => apiClient.post('/bots', data),
   };
   ```

2. **Create React Query hook** in `client/src/hooks/useApi.ts`:
   ```typescript
   export const useBots = () => {
     const { isAuthenticated } = useAuth();
     return useQuery({
       queryKey: ['bots'],
       queryFn: botApi.getBots,
       enabled: isAuthenticated,
       staleTime: 2 * 60 * 1000,  // Cache 2 min
     });
   };
   ```

3. **Use in component** with cache invalidation:
   ```typescript
   const { data: bots } = useBots();
   const createMutation = useMutation({
     mutationFn: botApi.createBot,
     onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ['bots'] });
     },
   });
   ```

### React Query Conventions
- **Query keys**: Use array format `['resource', id]` (e.g., `['bots', botId]`)
- **Cache invalidation**: Always include exact key match when invalidating
- **Polling vs WebSocket**: Don't poll if WebSocket is connected; set `refetchInterval` for static data only
- **Error handling**: Access `error?.response?.data?.detail` from mutation/query

### Testing Frontend
```bash
npm run test:frontend          # vitest with coverage
npm run test:frontend:ui       # UI mode for debugging
npm run test:e2e               # Playwright cross-browser tests
npm run test:e2e:ui            # Playwright UI debug mode
```

---

## 🔌 Critical Workflows

### Adding a New Backend Route
1. Create Pydantic models (request + response) in route file
2. Use `Depends()` + `Annotated` for all dependencies
3. Validate inputs; delegate logic to service
4. Register router in `main.py` with prefix + tag
5. Add 2–3 pytest cases (happy path + errors)

### Adding a Frontend Feature
1. Endpoint function in `lib/api.ts`
2. React Query hook in `hooks/useApi.ts`
3. Component in `components/` with TypeScript strict mode
4. Vitest or Playwright test

### Database Migration
```bash
npm run migrate:create "add_user_table"  # Create migration
# Edit alembic/versions/XXXX_add_user_table.py
npm run migrate                          # Apply migration
```

---

## ⚙️ Developer Commands

```bash
# Dev
npm run dev:fastapi          # Backend only
npm run dev                  # Frontend only
npm run electron             # Unified (Electron + FastAPI)

# Test
npm test                     # Backend (90%+ coverage required)
npm run test:frontend        # Frontend
npm run test:e2e             # E2E (Playwright)

# Build
npm run build                # Web bundle
npm run build:electron       # Desktop app (all platforms)

# Code quality
npm run lint:py              # Flake8
npm run format:py            # Black formatter
npm run check                # TypeScript check (no build)
npm run format:check         # Prettier check (frontend)
npm run format               # Prettier write (frontend)

# Infrastructure
docker-compose up -d         # Start all services (Postgres, Redis, etc.)
npm run migrate              # Run Alembic migrations
```

---

## 🔒 Key Safety Rules

✅ **DO**:
- Validate inputs before passing to services
- Use `HTTPException` with proper status codes
- Log suspicious activity with context (user_id, timestamp)
- Keep routes thin; put logic in services
- Use `Depends()` for all dependencies

❌ **DON'T**:
- Trust user input for command construction
- Assume Redis/external services available
- Use wildcard CORS origins
- Leak internal errors to client
- Directly manipulate external processes from routes

---

## 🤔 Decision Guide

| Question | Answer |
|----------|--------|
| "Where does business logic go?" | `server_fastapi/services/` – stateless |
| "Where does data access go?" | `server_fastapi/repositories/` – ORM queries |
| "Where does API endpoint go?" | `server_fastapi/routes/` – thin controller |
| "Where does UI state go?" | React Query hook (`client/src/hooks/`) |
| "Should I use old Node code?" | No. Mirror the FastAPI pattern instead. |
| "How long can a route take?" | < 1s for REST; consider Celery for long jobs |
| "When should I add tests?" | Always: happy path + 1 error case minimum |

---

## 📚 Study These Files

- [server_fastapi/main.py](../server_fastapi/main.py) – App initialization, middleware
- [server_fastapi/routes/bots.py](../server_fastapi/routes/bots.py) – Route pattern (~863 lines)
- [server_fastapi/services/](../server_fastapi/services/) – Service layer examples
- [client/src/lib/api.ts](../client/src/lib/api.ts) – API client definition
- [client/src/hooks/](../client/src/hooks/) – React Query patterns
- [docker-compose.yml](../docker-compose.yml) – Dev environment setup
- [pyproject.toml](../pyproject.toml) – Test config, coverage settings

---

## 🆘 Common Issues

| Issue | Fix |
|-------|-----|
| **Import error in route** | Check router registration in `main.py` |
| **React Query stale data** | Call `queryClient.invalidateQueries({ queryKey: ['resource', id] })` |
| **Pytest fails** | Run `npm run migrate` first (DB schema); check `conftest.py` |
| **TypeScript errors** | Run `npm run check`; review `tsconfig.json` paths |
| **Docker won't start** | Verify `.env.prod`, `DATABASE_URL`, `REDIS_URL` format |
| **Port 8000/5173 in use** | Kill process: `lsof -ti:8000 \| xargs kill -9` |

---

**Last Updated**: December 17, 2025 | **Status**: Production-Ready | **Coverage**: ≥90% enforced | **Tech Stack**: FastAPI + React 18 + TypeScript
