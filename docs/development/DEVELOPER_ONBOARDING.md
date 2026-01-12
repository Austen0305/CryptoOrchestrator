# Developer Onboarding Guide

Complete guide for new developers joining the CryptoOrchestrator project.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Common Tasks](#common-tasks)
- [Getting Help](#getting-help)

---

## 🔧 Prerequisites

### Required Software

- **Python 3.12+** ([Download](https://www.python.org/downloads/))

  - Verify: `python --version` (should be 3.12+)
  - Python 3.12.3 recommended for best compatibility
- **Node.js 18+** ([Download](https://nodejs.org/))

  - Verify: `node --version` (should be 18+)
  - npm comes bundled with Node.js
- **Git** ([Download](https://git-scm.com/downloads))

  - Verify: `git --version`

### Optional Software

- **PostgreSQL 15+** (optional - SQLite works for development)

  - Download: https://www.postgresql.org/download/
  - Or use Docker: `docker run -d -p 5432:5432 postgres:15`
- **Redis** (optional - for caching and rate limiting)

  - Download: https://redis.io/download
  - Or use Docker: `docker run -d -p 6379:6379 redis:7`
- **Docker & Docker Compose** (optional - for containerized development)

  - Download: https://www.docker.com/products/docker-desktop
- **VS Code** (recommended IDE)

  - Download: https://code.visualstudio.com/
  - Recommended extensions:
    - Python
    - Pylance
    - ESLint
    - Prettier
    - GitLens

---

## 🚀 Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Crypto-Orchestrator
```

### 2. Create Environment File

**Windows:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/create_env.ps1
```

**Linux/Mac:**

```bash
python scripts/generate_env.py
```

This creates a `.env` file with:

- Secure random secrets (JWT_SECRET, EXCHANGE_KEY_ENCRYPTION_KEY)
- Development-friendly defaults
- SQLite database configuration
- Optional Redis configuration

### 3. Install Dependencies

**Python dependencies:**

```bash
pip install -r requirements.txt
```

**Node.js dependencies:**

```bash
npm install --legacy-peer-deps
```

**Note:** `--legacy-peer-deps` is required due to some peer dependency conflicts. This is safe and expected.

### 4. Initialize Database

```bash
# Run database migrations
alembic upgrade head
```

This creates the SQLite database file: `crypto_orchestrator.db`

### 5. Verify Setup

```bash
# Start backend (Terminal 1)
npm run dev:fastapi

# Start frontend (Terminal 2)
npm run dev
```

**Verify:**

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Health Check: http://localhost:8000/api/health/

---

## 💻 Development Environment

### Recommended IDE Setup

#### VS Code / Cursor

**Extensions (54 verified free extensions organized in 4 phases):**

**Phase 1 - Essential (CRITICAL - 16 extensions):**

- Error Lens, ESLint, Prettier, SonarLint, Snyk
- Python, Pylance, Black Formatter, Python Docstring Generator, Python Type Hint, Python Test Explorer
- GitLens, Git Graph, Git History, GitHub Pull Requests and Issues
- DotEnv

**Phase 2 - Database & Testing (HIGH):**

- PostgreSQL, SQLite Viewer, SQLite3 Editor
- REST Client, RapidAPI Client
- Coverage Gutters, Jest Runner
- YAML Language Support, YAML ❤️ JSON

**Phase 3 - Documentation & Productivity (MEDIUM):**

- Markdown All in One, Markdown Preview Enhanced, markdownlint, Draw.io, Paste Image, PlantUML
- Better Comments, Path Intellisense, Import Cost, Todo Tree, Code Spell Checker, Project Manager

**Phase 4 - Specialized Tools (MEDIUM-LOW):**

- Docker, Kubernetes Tools, Dev Containers
- Live Server, Live Preview
- Auto Rename Tag, ES7+ React snippets, Indent Rainbow
- Dotenv Official, CodeMetrics, VS Code Lizard
- WakaTime, Pomodoro for Dev, Bookmarks
- React Native Tools, Expo Tools
- Electron Snippets

**Complete Setup Guide:** See [`.cursor/EXTENSIONS_SETUP_GUIDE.md`](../../.cursor/EXTENSIONS_SETUP_GUIDE.md) for:

- Phase-by-phase installation instructions
- Extension descriptions and benefits
- Configuration details
- Troubleshooting tips

**Extension Verification:**

```bash
node scripts/utilities/verify-extensions.js
```

**Settings (`.vscode/settings.json`):**
All extension configurations are pre-configured in `.vscode/settings.json`. Key settings include:

```json
{
  "python.defaultInterpreterPath": "python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.analysis.typeCheckingMode": "strict",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "errorLens.enabled": true,
  "gitlens.codeLens.enabled": true,
  "coverage-gutters.showGutterCoverage": true,
  "todo-tree.general.tags": ["TODO", "FIXME", "NOTE", "HACK", "XXX"]
}
```

See `.vscode/settings.json` for complete configuration.

**MCP Servers (Optional):**
10+ free MCP servers available for enhanced capabilities:

- Infrastructure: Sentry, Docker, New Relic, OneUptime, Prisma, Puppeteer, GitHub
- Crypto: CoinCap, CoinLore, Web3, DeFi Trading, Crypto Fear & Greed, CryptoPanic, and more

See [`.cursor/MCP_ENV_VARS_ADDED.md`](../../.cursor/MCP_ENV_VARS_ADDED.md) for MCP server setup instructions.

### Environment Variables

**Required Variables:**

```env
NODE_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./crypto_orchestrator.db
JWT_SECRET=<generated-secret-64-chars>
EXCHANGE_KEY_ENCRYPTION_KEY=<generated-secret-32-chars>
```

**Optional Variables:**

```env
# Redis (optional - app works without it)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Trading Configuration
DEFAULT_TRADING_MODE=paper
ENABLE_MOCK_DATA=true
PRODUCTION_MODE=false

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
```

See [docs/ENV_VARIABLES.md](./ENV_VARIABLES.md) for complete environment variable reference.

---

## 📁 Project Structure

```
Crypto-Orchestrator/
├── server_fastapi/          # FastAPI backend
│   ├── routes/              # API endpoints (thin controllers)
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── bots.py         # Bot management endpoints
│   │   ├── trades.py       # Trade execution endpoints
│   │   ├── logs.py         # Log search endpoints (admin)
│   │   ├── alerting.py     # Alerting & incident management (admin)
│   │   ├── database_performance.py  # DB performance monitoring (admin)
│   │   ├── cache_management.py     # Cache management (admin)
│   │   └── background_jobs.py       # Background jobs monitoring (admin)
│   ├── services/            # Business logic
│   │   ├── trading/        # Trading services
│   │   │   ├── bot_trading_service.py
│   │   │   ├── real_money_service.py
│   │   │   ├── dex_trading_service.py
│   │   │   └── safe_trading_system.py
│   │   ├── risk_management_engine.py
│   │   ├── risk_persistence.py     # Risk data persistence
│   │   ├── alerting/        # Alerting services
│   │   ├── logging/         # Logging services
│   │   └── cache/           # Cache services
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── bot.py
│   │   ├── trade.py
│   │   ├── risk_limit.py
│   │   └── risk_alert.py
│   ├── repositories/        # Data access layer
│   ├── middleware/          # Request/response middleware
│   │   ├── enhanced_error_handler.py
│   │   ├── rate_limit_middleware.py
│   │   └── query_cache.py
│   ├── dependencies/        # FastAPI dependencies
│   │   ├── auth.py         # Authentication dependencies
│   │   ├── trading.py      # Trading service dependencies
│   │   └── risk.py         # Risk service dependencies
│   ├── utils/               # Utilities
│   │   ├── query_optimizer.py
│   │   ├── cache_utils.py
│   │   └── response_optimizer.py
│   ├── database/            # Database configuration
│   │   ├── connection_pool.py
│   │   └── pool_monitoring.py
│   ├── tests/               # Backend tests
│   └── main.py              # Application entry point
├── client/                  # React frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── ui/         # shadcn/ui base components
│   │   │   ├── BotCreator.tsx
│   │   │   ├── TradingHeader.tsx
│   │   │   └── ...
│   │   ├── hooks/           # Custom React hooks
│   │   │   ├── useApi.ts
│   │   │   ├── useBots.ts
│   │   │   └── ...
│   │   ├── lib/             # Utilities & API clients
│   │   │   ├── api.ts      # API function definitions
│   │   │   ├── queryClient.ts  # React Query setup
│   │   │   └── utils.ts
│   │   ├── pages/           # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Bots.tsx
│   │   │   └── ...
│   │   ├── contexts/        # React contexts
│   │   └── utils/           # Performance utilities
│   └── public/              # Static assets
├── shared/                  # Shared TypeScript types/schemas
│   ├── schema.ts
│   └── types.ts
├── electron/                # Electron desktop app
├── mobile/                  # React Native mobile app
├── tests/                   # Integration & E2E tests
│   └── e2e/                 # Playwright E2E tests
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
│   ├── API_REFERENCE.md
│   ├── DEVELOPER_ONBOARDING.md  # This file
│   ├── CONTRIBUTING.md
│   └── troubleshooting/
├── alembic/                 # Database migrations
├── .env                     # Environment variables (DO NOT COMMIT)
├── .env.example             # Environment template
└── README.md
```

---

## 🔄 Development Workflow

### Starting Development

**Terminal 1: Backend**

```bash
npm run dev:fastapi
```

**Terminal 2: Frontend**

```bash
npm run dev
```

**Terminal 3: Celery Worker (if needed)**

```bash
npm run celery:worker
```

**Terminal 4: Celery Beat (if needed)**

```bash
npm run celery:beat
```

### Making Changes

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**

   - Follow code standards (see below)
   - Write tests for new features
   - Update documentation
3. **Test your changes**

   ```bash
   # Run all tests
   npm run test

   # Backend tests only
   pytest server_fastapi/tests/ -v

   # Frontend tests
   npm run test:frontend

   # E2E tests
   npm run test:e2e

   # Check code quality
   npm run lint:py
   npm run check
   ```
4. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```
5. **Create Pull Request**

   - Follow [CONTRIBUTING.md](./CONTRIBUTING.md) guidelines
   - Ensure all CI checks pass
   - Request code review

---

## 📝 Code Standards

### Python Code Style

**Formatter:** Black (88 char line length)

```bash
npm run format:py
# or
python -m black server_fastapi/ tests/
```

**Linter:** Flake8

```bash
npm run lint:py
# or
python -m flake8 server_fastapi/ tests/
```

**Type Checking:** MyPy (strict mode)

```bash
python -m mypy server_fastapi/
```

**Key Python Standards:**

- Use `async def` for I/O operations
- Use `Annotated` for FastAPI dependencies (primary pattern)
- Use type hints on all functions
- Use SQLAlchemy `.is_(True)` / `.is_(False)` for boolean comparisons
- Use `yield` in dependencies for resources requiring cleanup
- Never log sensitive data (API keys, passwords, private keys)
- Check Redis availability before using cache features

**Example:**

```python
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    """Database session dependency with cleanup."""
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
    service: Annotated[BotService, Depends(get_bot_service)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await service.create_bot(request, user_id=current_user['id'], db=db)
```

### TypeScript Code Style

**Formatter:** Prettier

```bash
npm run format
```

**Linter:** ESLint

```bash
npm run lint
```

**Type Checking:** TypeScript strict mode

```bash
npm run check
```

**Key TypeScript Standards:**

- No `any` types (use `unknown` if needed)
- Use React Query for server state (not component state)
- Handle loading/error states with LoadingSkeleton and ErrorBoundary
- Normalize trading modes ("live" → "real") before API calls
- Use hierarchical query keys: `['domain', subKey?]`
- Invalidate queries strategically (exact match, prefix match, predicates)

**Example:**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { botApi } from '@/lib/api';

export const useBots = () => {
  return useQuery({
    queryKey: ['bots'],
    queryFn: () => botApi.getBots(),
    staleTime: 30000,
    refetchInterval: false, // Disable when WebSocket available
  });
};

export const useCreateBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (bot: InsertBotConfig) => botApi.createBot(bot),
    onSuccess: () => {
      // Prefix match - invalidates all ['bots', ...] queries
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};
```

### Code Review Checklist

Before submitting code, verify:

- [ ] Code follows style guidelines (Black, Prettier)
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation updated
- [ ] No console.log/debug statements
- [ ] Error handling implemented
- [ ] Type hints/types added (Python/TypeScript)
- [ ] No sensitive data in logs
- [ ] SQLAlchemy boolean comparisons use `.is_(True)` / `.is_(False)`
- [ ] FastAPI dependencies use `Annotated` pattern
- [ ] Trading modes normalized ("live" → "real")
- [ ] Redis availability checked before cache operations

---

## 🧪 Testing

### Running Tests

**All Tests:**

```bash
npm run test:all
```

**Backend Tests:**

```bash
# All backend tests
pytest server_fastapi/tests/ -v

# With coverage
pytest server_fastapi/tests/ -v --cov=server_fastapi --cov-report=html

# Watch mode
npm run test:watch
```

**Frontend Tests:**

```bash
# Unit tests
npm run test:frontend

# UI mode
npm run test:frontend:ui

# With coverage
npm run test:frontend:coverage
```

**E2E Tests:**

```bash
# Run all E2E tests
npm run test:e2e

# UI mode (interactive)
npm run test:e2e:ui
```

**Prerequisites for E2E:**

- Backend running on port 8000
- Frontend running on port 5173
- Test database initialized

### Writing Tests

**Backend (pytest):**

```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_bot_success(client: AsyncClient, test_user: dict):
    response = await client.post(
        "/api/bots",
        json={"name": "Test Bot", "strategy": "momentum", "initial_balance": 1000.0},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Bot"
    assert data["strategy"] == "momentum"
```

**Frontend (Vitest):**

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BotList } from '@/components/BotList';

describe('BotList', () => {
  it('should render bot list', () => {
    render(<BotList />);
    expect(screen.getByText('My Bot')).toBeInTheDocument();
  });
});
```

**E2E (Playwright):**

```typescript
import { test, expect } from '@playwright/test';

test('should create bot successfully', async ({ page }) => {
  await page.goto('/bots');
  await page.getByTestId('create-bot-btn').click();
  await page.fill('input[name="name"]', 'Test Bot');
  await page.selectOption('select[name="strategy"]', 'momentum');
  await page.click('button[type="submit"]');
  
  await expect(page.locator('text=Test Bot')).toBeVisible();
});
```

### Test Coverage Goals

- **Backend:** ≥85% coverage
- **Frontend:** ≥85% coverage
- **E2E:** Critical user flows covered
- **Security:** All security checklist items verified
- **E2E:** Critical user flows covered

---

## 🛠️ Common Tasks

### Creating a New API Endpoint

1. **Create the service** (`server_fastapi/services/your_service.py`):

```python
class YourService:
    async def do_something(self, param: str, db: AsyncSession) -> dict:
        # Business logic
        return {"result": "success"}
```

2. **Create the route** (`server_fastapi/routes/your_route.py`):

```python
from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from ..services.your_service import YourService
from ..dependencies.auth import get_current_user
from ..database import get_db_session

router = APIRouter(prefix="/api/your-route", tags=["Your Route"])

@router.get("/endpoint")
async def your_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[YourService, Depends(get_your_service)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    result = await service.do_something("param", db=db)
    return result
```

3. **Create dependency provider** (`server_fastapi/dependencies/your_service.py`):

```python
from typing import Annotated
from fastapi import Depends
from ..services.your_service import YourService

async def get_your_service() -> YourService:
    """Provide your service instance."""
    return YourService()
```

4. **Register the route** (`server_fastapi/main.py`):

```python
from .routes.your_route import router
app.include_router(router)
```

5. **Add tests** (`server_fastapi/tests/test_your_route.py`)

### Creating a New Frontend Component

1. **Create component** (`client/src/components/YourComponent.tsx`):

```typescript
import { useState } from 'react';
import { Button } from '@/components/ui/button';

interface YourComponentProps {
  title: string;
}

export function YourComponent({ title }: YourComponentProps) {
  const [state, setState] = useState('');
  
  return (
    <div>
      <h1>{title}</h1>
      <Button onClick={() => setState('clicked')}>Click me</Button>
    </div>
  );
}
```

2. **Create hook** (if needed) (`client/src/hooks/useYourHook.ts`):

```typescript
import { useQuery } from '@tanstack/react-query';
import { yourApi } from '@/lib/api';

export function useYourHook() {
  return useQuery({
    queryKey: ['your-key'],
    queryFn: () => yourApi.getData(),
    staleTime: 30000,
  });
}
```

3. **Add API function** (`client/src/lib/api.ts`):

```typescript
export const yourApi = {
  getData: () => apiRequest("/api/your-route/endpoint", { method: "GET" }),
};
```

4. **Add to page** (`client/src/pages/YourPage.tsx`)

### Creating a Database Migration

```bash
# Create migration
alembic revision --autogenerate -m "add your_table"

# Review generated migration file
# Edit if needed (alembic/versions/xxx_add_your_table.py)

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Migration Best Practices:**

- Always review auto-generated migrations
- Test migrations on development database first
- Keep migrations backward compatible when possible
- Never edit existing migrations (create new ones)

### Adding a New Dependency

**Python:**

1. Add to `requirements.txt`
2. Install: `pip install -r requirements.txt`
3. Update `requirements-dev.txt` if it's a dev dependency

**Node.js:**

1. Install: `npm install <package> --legacy-peer-deps`
2. Package will be added to `package.json` automatically

---

## 🐛 Getting Help

### Documentation

- **API Reference:** [docs/API_REFERENCE.md](./API_REFERENCE.md)
- **Architecture:** [docs/architecture.md](./architecture.md)
- **Local Development:** [docs/LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md)
- **Troubleshooting:** [docs/troubleshooting/common_issues.md](./troubleshooting/common_issues.md)

### Support Channels

- **GitHub Issues:** Report bugs and request features
- **Discord:** Join developer community
- **Email:** dev-support@cryptoorchestrator.com

### Common Issues

**Port already in use:**

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill <PID>
```

**Database connection error:**

- Check `DATABASE_URL` in `.env`
- Ensure database is running
- Verify credentials

**Import errors:**

- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Frontend build errors:**

- Clear cache: `rm -rf node_modules .next`
- Reinstall: `npm install --legacy-peer-deps`

See [docs/troubleshooting/common_issues.md](./troubleshooting/common_issues.md) for more solutions.

---

## 📚 Next Steps

1. **Read the Architecture:** [docs/architecture.md](./architecture.md)
2. **Review API Documentation:** [docs/API_REFERENCE.md](./API_REFERENCE.md)
3. **Check Contribution Guidelines:** [docs/CONTRIBUTING.md](./CONTRIBUTING.md)
4. **Explore the Codebase:** Start with `server_fastapi/main.py` and `client/src/App.tsx`
5. **Run Tests:** Ensure all tests pass locally
6. **Pick a First Issue:** Look for "good first issue" labels on GitHub

---

**Welcome to the CryptoOrchestrator team!** 🚀

*Last updated: 2025-12-06*
