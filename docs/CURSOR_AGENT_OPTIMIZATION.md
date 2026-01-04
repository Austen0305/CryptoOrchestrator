# Cursor Agent Optimization Guide

**Purpose:** Additional configurations and improvements to help the Cursor agent complete the CryptoOrchestrator project more effectively.

**Last Updated:** 2025-01-19

---

## 🎯 Current Status

### ✅ Excellent Coverage
- **17 MCPs** installed and working
- **14/14 recommended VS Code extensions** installed
- **Comprehensive Cursor rules** (8 rule files)
- **Intelligence system** integrated
- **Testing infrastructure** complete

### 📊 Project Completion Status
- **Overall Progress:** ~95% complete
- **Critical Phases:** 100% complete
- **Remaining Work:**
  - Mobile app native initialization (88% complete)
  - Some component tests missing
  - E2E test coverage gaps
  - Documentation improvements

---

## 🚀 Additional Optimizations

### 1. Workspace Settings for Cursor

Create `.vscode/settings.json` (if not exists) with agent-friendly settings:

```json
{
  "files.exclude": {
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/coverage": true,
    "**/test-results": true,
    "**/dist": true,
    "**/build": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/coverage": true,
    "**/dist": true,
    "**/build": true
  },
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/__pycache__/**": true,
    "**/coverage/**": true,
    "**/dist/**": true
  },
  "python.analysis.extraPaths": [
    "${workspaceFolder}/server_fastapi"
  ],
  "typescript.preferences.importModuleSpecifier": "non-relative",
  "typescript.suggest.autoImports": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  }
}
```

**Why:** Improves indexing performance and provides better autocomplete for the agent.

---

### 2. Agent Helper Files

#### A. Create `.cursor/AGENT_CONTEXT.md`

A quick reference file the agent can read to understand project state:

```markdown
# Agent Context - Quick Reference

## Current Project State
- **Status:** 95% complete, production-ready
- **Last Major Update:** 2025-01-19
- **Critical Issues:** None
- **Next Priorities:** Mobile native init, test coverage gaps

## Key Files to Know
- **Main Backend:** `server_fastapi/main.py`
- **Main Frontend:** `client/src/App.tsx`
- **API Spec:** `docs/openapi.json`
- **Environment:** `.env.example`
- **Todo List:** `Todo.md`

## Common Patterns
- Backend routes: Use `Annotated[Type, Depends()]` pattern
- Frontend hooks: Use React Query with `useAuth()` pattern
- Services: Stateless, repository delegation
- Tests: pytest (backend), Vitest (frontend), Playwright (E2E)

## Quick Commands
- Start all: `npm run start:all`
- Test all: `npm run test:e2e:complete`
- Format: `npm run format:py` and `npm run format`
- Check: `npm run check`
```

#### B. Create `.cursor/PRIORITY_TASKS.md`

A prioritized list of remaining tasks for the agent:

```markdown
# Priority Tasks for Cursor Agent

## 🔥 High Priority (Complete First)

1. **Mobile Native Initialization**
   - Status: 88% complete
   - Files: `mobile/` directory
   - Action: Run `react-native init` or use Expo
   - Time: 10-30 minutes

2. **Missing Component Tests**
   - Priority components:
     - `DEXTradingPanel.tsx`
     - `Wallet.tsx`, `WalletCard.tsx`
     - `TradingHeader.tsx`
     - `StrategyEditor.tsx`
   - Pattern: Use existing test files as templates
   - Time: 2-4 hours

3. **E2E Test Coverage Gaps**
   - Missing flows:
     - Portfolio management
     - Settings updates
     - Withdrawal with 2FA
     - Bot learning/training
   - Pattern: Use existing E2E tests as templates
   - Time: 3-5 hours

## ⭐ Medium Priority

4. **Documentation Improvements**
   - API examples for some endpoints
   - Mobile app setup clarity
   - Deployment guide verification

5. **Mock Implementation Replacements**
   - `MockAuthService` → Real AuthService
   - Mock ML models → Real implementations
   - Verify fallback logic works

## 📝 Low Priority

6. **Performance Profiling**
   - Mobile app performance
   - Bundle size optimization
   - Database query optimization
```

---

### 3. MCP Configuration Enhancements

#### A. Optimize api-tester MCP Usage

Create `docs/mcp-config/api-tester-config.json`:

```json
{
  "defaultSpec": "docs/openapi.json",
  "defaultLanguage": "python",
  "defaultFramework": "pytest",
  "endpoints": {
    "baseUrl": "http://localhost:8000",
    "auth": {
      "type": "bearer",
      "tokenEnvVar": "TEST_JWT_TOKEN"
    }
  },
  "testGeneration": {
    "includeNegativeTests": true,
    "includeEdgeCases": true,
    "coverageTarget": 80
  }
}
```

**Usage:** Agent can reference this when using api-tester MCP.

#### B. Context7 Library Presets

Create `.cursor/context7-presets.md`:

```markdown
# Context7 Library Presets

## Common Libraries Used

### Backend
- FastAPI: `/tiangolo/fastapi`
- SQLAlchemy: `/sqlalchemy/sqlalchemy`
- Pydantic: `/pydantic/pydantic`
- Web3.py: `/ethereum/web3.py`

### Frontend
- React: `/facebook/react`
- TypeScript: `/microsoft/TypeScript`
- TanStack Query: `/tanstack/query`
- wagmi: `/wagmi-dev/wagmi`

## Quick Lookup
Use context7 MCP with these library IDs for faster documentation access.
```

---

### 4. Codebase Indexing Improvements

#### A. Update `.cursorignore` (Already Good)

Your `.cursorignore` is well-configured. Consider adding:

```
# Additional exclusions for agent performance
*.min.js
*.min.css
*.bundle.js
vendor/
```

#### B. Create `.cursor/index-priority.md`

Tell the agent which files are most important:

```markdown
# Codebase Indexing Priority

## 🔥 Critical Files (Always Index)
- `server_fastapi/main.py`
- `client/src/App.tsx`
- `server_fastapi/routes/**/*.py`
- `client/src/pages/**/*.tsx`
- `server_fastapi/services/**/*.py`
- `.cursor/rules/**/*.mdc`

## ⭐ Important Files (Index When Relevant)
- `server_fastapi/models/**/*.py`
- `client/src/components/**/*.tsx`
- `server_fastapi/schemas/**/*.py`
- `tests/**/*`

## 📝 Reference Files (Index on Demand)
- `docs/**/*.md`
- `scripts/**/*`
- `alembic/**/*`
```

---

### 5. Agent Workflow Optimizations

#### A. Create `.cursor/AGENT_WORKFLOW.md`

Standard workflow for the agent:

```markdown
# Agent Workflow Guide

## Before Starting Any Task

1. **Read Context**
   - Read `.cursor/AGENT_CONTEXT.md`
   - Check `Todo.md` for task status
   - Review relevant `.cursor/rules/*.mdc` files

2. **Understand Patterns**
   - Check `.cursor/extracted-patterns.md` (if exists)
   - Review similar files in codebase
   - Use existing code as templates

3. **Plan Approach**
   - Break down complex tasks
   - Identify dependencies
   - Check for existing solutions

## During Development

1. **Follow Patterns**
   - Use established patterns from rules
   - Match existing code style
   - Maintain consistency

2. **Test as You Go**
   - Write tests for new code
   - Run existing tests to verify
   - Check for regressions

3. **Document Changes**
   - Update relevant docs
   - Add comments for complex logic
   - Update CHANGELOG if needed

## After Completion

1. **Verify**
   - Run tests
   - Check linting
   - Verify functionality

2. **Update Status**
   - Update `Todo.md`
   - Update relevant docs
   - Commit with clear message
```

#### B. Create `.cursor/COMMON_PATTERNS.md`

Quick reference for common patterns:

```markdown
# Common Patterns Quick Reference

## Backend Route Pattern
```python
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/endpoint")
async def get_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseModel:
    # Implementation
```

## Frontend Hook Pattern
```typescript
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';

export function useData() {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['data', user?.id],
    queryFn: () => fetchData(user.id),
    enabled: !!user,
    staleTime: 30000,
  });
}
```

## Service Pattern
```python
class MyService:
    def __init__(self, repository: MyRepository):
        self.repository = repository
    
    async def do_something(self, data: dict) -> dict:
        # Business logic
        return await self.repository.save(data)
```
```

---

### 6. Testing Helper Files

#### A. Create `tests/AGENT_TEST_GUIDE.md`

Guide for agent to write tests:

```markdown
# Agent Test Writing Guide

## Backend Tests (pytest)

### Template
```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_endpoint(client: TestClient, auth_headers: dict):
    response = client.get("/api/endpoint", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

### Common Fixtures
- `client`: TestClient instance
- `auth_headers`: Authentication headers
- `db_session`: Database session
- `test_user`: Test user data

## Frontend Tests (Vitest)

### Template
```typescript
import { render, screen } from '@testing-library/react';
import { Component } from './Component';

test('renders component', () => {
  render(<Component />);
  expect(screen.getByText('Text')).toBeInTheDocument();
});
```

## E2E Tests (Playwright)

### Template
```typescript
import { test, expect } from '@playwright/test';

test('user flow', async ({ page }) => {
  await page.goto('/');
  await page.click('button');
  await expect(page.locator('.result')).toBeVisible();
});
```
```

---

### 7. Documentation Structure for Agent

#### A. Create `docs/AGENT_QUICK_START.md`

Quick start guide for agent:

```markdown
# Agent Quick Start Guide

## Project Overview
CryptoOrchestrator is a FastAPI + React trading platform.

## Key Directories
- `server_fastapi/` - Backend (FastAPI)
- `client/src/` - Frontend (React + TypeScript)
- `mobile/` - Mobile app (React Native)
- `tests/` - All tests
- `docs/` - Documentation
- `.cursor/` - Cursor-specific files

## Common Tasks

### Add New API Endpoint
1. Create route in `server_fastapi/routes/`
2. Add schema in `server_fastapi/schemas/`
3. Add service in `server_fastapi/services/`
4. Add repository in `server_fastapi/repositories/`
5. Write tests in `server_fastapi/tests/`

### Add New Frontend Page
1. Create page in `client/src/pages/`
2. Add route in `client/src/App.tsx`
3. Create hooks in `client/src/hooks/`
4. Add types in `client/src/types/`
5. Write tests in `client/src/**/*.test.tsx`

## Testing Commands
- Backend: `pytest server_fastapi/tests/`
- Frontend: `npm run test:frontend`
- E2E: `npm run test:e2e:complete`
```

---

### 8. Performance Monitoring for Agent

#### A. Create `scripts/monitoring/agent-performance.md`

Track agent efficiency:

```markdown
# Agent Performance Tracking

## Metrics to Track
- Time to complete tasks
- Test coverage changes
- Code quality improvements
- Bug fixes per session

## Tools
- Use existing coverage reports
- Use SonarLint results
- Track TODO.md completion
```

---

## 🎯 Implementation Priority

### Immediate (Do Now)
1. ✅ Create `.vscode/settings.json` (if missing)
2. ✅ Create `.cursor/AGENT_CONTEXT.md`
3. ✅ Create `.cursor/PRIORITY_TASKS.md`

### Soon (This Week)
4. Create `.cursor/AGENT_WORKFLOW.md`
5. Create `.cursor/COMMON_PATTERNS.md`
6. Create `docs/AGENT_QUICK_START.md`

### Later (Nice to Have)
7. Create MCP configuration files
8. Create test writing guides
9. Performance monitoring setup

---

## 📊 Expected Benefits

### For Agent
- **Faster Context Understanding:** Quick reference files
- **Better Pattern Matching:** Common patterns documented
- **Clearer Priorities:** Task prioritization
- **Improved Testing:** Test templates and guides

### For Project
- **Faster Development:** Less time understanding context
- **Better Consistency:** Documented patterns
- **Higher Quality:** Better test coverage
- **Easier Onboarding:** Clear documentation

---

## 🔄 Maintenance

### Regular Updates
- Update `AGENT_CONTEXT.md` when project state changes
- Update `PRIORITY_TASKS.md` as tasks complete
- Update `COMMON_PATTERNS.md` when patterns evolve

### Review Schedule
- Weekly: Review priority tasks
- Monthly: Update context and patterns
- Quarterly: Review and optimize workflow

---

## 📝 Summary

These optimizations will help the Cursor agent:
1. **Understand context faster** (AGENT_CONTEXT.md)
2. **Know what to work on** (PRIORITY_TASKS.md)
3. **Follow established patterns** (COMMON_PATTERNS.md)
4. **Write better tests** (Test guides)
5. **Work more efficiently** (Workflow guide)

**Next Step:** Create the immediate priority files listed above.
