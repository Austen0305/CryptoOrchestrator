# 🛠️ CryptoOrchestrator Developer Guide

Complete guide for developers working on the CryptoOrchestrator project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [API Development](#api-development)
- [Frontend Development](#frontend-development)
- [Database Management](#database-management)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **PostgreSQL** (optional, SQLite works for development)
- **Redis** (optional, for caching and rate limiting)
- **Git**

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd Crypto-Orchestrator

# Run automated setup
python scripts/dev_setup.py

# Or manual setup:
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node.js dependencies
npm install

# 3. Copy environment file
cp .env.example .env
# Edit .env with your configuration

# 4. Run database migrations
alembic upgrade head

# 5. Start development server
npm run dev:fastapi
```

---

## 📁 Project Structure

```
Crypto-Orchestrator/
├── server_fastapi/          # FastAPI backend
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── models/              # Database models
│   ├── middleware/          # Request/response middleware
│   ├── repositories/        # Data access layer
│   └── main.py              # Application entry point
├── client/                  # React frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── hooks/           # React hooks
│   │   ├── lib/             # Utilities
│   │   └── pages/           # Page components
├── shared/                  # Shared TypeScript types
├── electron/                # Electron desktop app
├── tests/                   # Test files
├── scripts/                 # Utility scripts
└── docs/                    # Documentation
```

---

## 🔄 Development Workflow

### Starting Development

```bash
# Terminal 1: Backend
npm run dev:fastapi

# Terminal 2: Frontend
cd client && npm run dev

# Terminal 3: Celery Worker (if needed)
npm run celery:worker

# Terminal 4: Celery Beat (if needed)
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
   # Run tests
   npm run test
   
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

---

## 📝 Code Standards

### Python Code Style

- **Formatter**: Black (88 char line length)
- **Linter**: Flake8
- **Type Checking**: MyPy (strict mode)

```bash
# Format code
npm run format:py

# Lint code
npm run lint:py

# Type check
python -m mypy server_fastapi/
```

### TypeScript Code Style

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checking**: TypeScript strict mode

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run check
```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation updated
- [ ] No console.log/debug statements
- [ ] Error handling implemented
- [ ] Type hints/types added

---

## 🧪 Testing

### Running Tests

```bash
# All tests
npm run test

# Backend tests only
pytest server_fastapi/tests/ -v

# Frontend tests
npm run test:frontend

# E2E tests
npm run test:e2e

# Watch mode
npm run test:watch
```

### Writing Tests

**Backend (pytest)**:
```python
import pytest
from fastapi.testclient import TestClient

def test_example(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
```

**Frontend (Vitest)**:
```typescript
import { describe, it, expect } from 'vitest'

describe('Component', () => {
  it('should render', () => {
    // Test code
  })
})
```

---

## 🔌 API Development

### Creating a New API Endpoint

1. **Create the service** (`server_fastapi/services/your_service.py`):
```python
class YourService:
    async def do_something(self, param: str) -> dict:
        # Business logic
        return {"result": "success"}
```

2. **Create the route** (`server_fastapi/routes/your_route.py`):
```python
from fastapi import APIRouter, Depends
from ..services.your_service import YourService
from ..dependencies.auth import get_current_user

router = APIRouter(prefix="/api/your-route", tags=["Your Route"])

@router.get("/endpoint")
async def your_endpoint(
    current_user: dict = Depends(get_current_user)
):
    service = YourService()
    result = await service.do_something("param")
    return result
```

3. **Register the route** (`server_fastapi/main.py`):
```python
from .routes.your_route import router
app.include_router(router)
```

4. **Add tests** (`server_fastapi/tests/test_your_route.py`)

---

## 🎨 Frontend Development

### Creating a New Component

1. **Create component** (`client/src/components/YourComponent.tsx`):
```typescript
import { useState } from 'react'

export function YourComponent() {
  const [state, setState] = useState('')
  
  return <div>{state}</div>
}
```

2. **Create hook** (if needed) (`client/src/hooks/useYourHook.ts`):
```typescript
import { useQuery } from '@tanstack/react-query'
import { yourApi } from '@/lib/api'

export function useYourHook() {
  return useQuery({
    queryKey: ['your-key'],
    queryFn: () => yourApi.getData()
  })
}
```

3. **Add to page** (`client/src/pages/YourPage.tsx`)

---

## 🗄️ Database Management

### Creating Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Review generated migration
# Edit if needed

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Models

```python
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class YourModel(Base):
    __tablename__ = "your_table"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

---

## 🚀 Deployment

### Pre-Deployment Checklist

- [ ] All tests pass
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Security scan passed
- [ ] Performance tested
- [ ] Documentation updated

### Deployment Steps

```bash
# Build application
npm run build

# Run tests
npm run test

# Deploy (see deployment guide)
./scripts/deploy.sh
```

---

## 🐛 Troubleshooting

### Common Issues

**Port already in use**:
```bash
# Find process
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill process
taskkill /PID <PID> /F         # Windows
kill <PID>                     # macOS/Linux
```

**Database connection error**:
- Check DATABASE_URL in .env
- Ensure database is running
- Verify credentials

**Import errors**:
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Frontend build errors**:
- Clear cache: `rm -rf node_modules .next`
- Reinstall: `npm install`

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Project README](../README.md)
- [API Documentation](http://localhost:8000/docs)

---

## 💡 Tips

1. **Use TypeScript** - Always type your code
2. **Write Tests** - Test as you develop
3. **Follow Patterns** - Use existing patterns as examples
4. **Document Code** - Add docstrings and comments
5. **Review Code** - Get code reviews before merging
6. **Keep It Simple** - Prefer simple solutions
7. **Error Handling** - Always handle errors gracefully

---

*Last updated: January 2025*

