---
description: Testing standards and patterns for CryptoOrchestrator (pytest, Vitest, Playwright)
globs: ["**/*test*.py", "**/*test*.ts", "**/*test*.tsx", "**/*.spec.ts", "tests/**/*"]
alwaysApply: false
---

# Testing Rules

## Testing Philosophy

- Write tests for new features and bug fixes
- Ensure tests are meaningful and cover edge cases
- Prefer integration tests for critical business logic
- Use mocking/spying appropriately for external dependencies
- Maintain test coverage above 85% for new code
- Tests should be fast, isolated, and repeatable
- Use descriptive test names that explain what is being tested

## Backend Testing (pytest)

### Test Structure
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# ✅ Good: Clear test structure
@pytest.mark.asyncio
async def test_create_bot_requires_authentication(client: TestClient):
    """Test that creating a bot requires authentication."""
    # Arrange
    bot_data = {"name": "Test Bot", "strategy": "grid"}
    
    # Act
    response = client.post("/api/bots", json=bot_data)
    
    # Assert
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_create_bot_success(client: TestClient, auth_headers: dict, test_user: dict):
    """Test successful bot creation."""
    bot_data = {"name": "Test Bot", "strategy": "grid", "amount": 100.0}
    
    response = client.post(
        "/api/bots",
        json=bot_data,
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Bot"
    assert data["strategy"] == "grid"
    assert data["user_id"] == test_user["id"]
```

### Test Fixtures
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()

@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
    }
```

### Mocking External Dependencies
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_execute_trade_with_mock_blockchain():
    """Test trade execution with mocked blockchain service."""
    with patch("server_fastapi.services.blockchain.execute_swap") as mock_swap:
        mock_swap.return_value = AsyncMock(
            status="success",
            tx_hash="0x123...",
            amount_out=100.0,
        )
        
        result = await execute_trade(
            sell_token="USDC",
            buy_token="ETH",
            amount=1000.0,
            user_id=1,
        )
        
        assert result["status"] == "success"
        mock_swap.assert_called_once()
```

### Test Coverage
- Aim for 90%+ coverage for new code
- Use `pytest --cov=server_fastapi --cov-report=html` to generate coverage reports
- Focus on testing business logic, not implementation details
- Test error paths and edge cases

## Frontend Testing (Vitest)

### Component Testing
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TradingBotCard } from './TradingBotCard';

// ✅ Good: Test with React Query provider
test('renders bot name and strategy', async () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  const bot = { id: 1, name: 'Test Bot', strategy: 'grid' };
  
  render(
    <QueryClientProvider client={queryClient}>
      <TradingBotCard botId={bot.id} />
    </QueryClientProvider>
  );
  
  await waitFor(() => {
    expect(screen.getByText('Test Bot')).toBeInTheDocument();
    expect(screen.getByText(/grid/i)).toBeInTheDocument();
  });
});
```

### Hook Testing
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTradingBot } from './useTradingBot';

test('fetches bot data', async () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
  
  const { result } = renderHook(() => useTradingBot(1), { wrapper });
  
  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true);
  });
  
  expect(result.current.data?.name).toBe('Test Bot');
});
```

### Mocking API Calls
```typescript
import { vi } from 'vitest';
import * as api from '@/lib/api';

test('handles API errors', async () => {
  vi.spyOn(api, 'getBot').mockRejectedValue(new Error('Network error'));
  
  render(<TradingBotCard botId={1} />);
  
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

## E2E Testing (Playwright)

### Test Structure
```typescript
import { test, expect } from '@playwright/test';

test.describe('Trading Bot Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should create a new trading bot', async ({ page }) => {
    await page.goto('/bots');
    await page.click('button:has-text("Create Bot")');
    
    await page.fill('input[name="name"]', 'My Test Bot');
    await page.selectOption('select[name="strategy"]', 'grid');
    await page.fill('input[name="amount"]', '1000');
    
    await page.click('button:has-text("Create")');
    
    await expect(page.locator('text=My Test Bot')).toBeVisible();
  });

  test('should display error for invalid bot configuration', async ({ page }) => {
    await page.goto('/bots');
    await page.click('button:has-text("Create Bot")');
    
    // Try to submit without required fields
    await page.click('button:has-text("Create")');
    
    await expect(page.locator('text=Name is required')).toBeVisible();
  });
});
```

### Best Practices
- Use page object models for complex flows
- Test critical user journeys end-to-end
- Use data-testid attributes for reliable selectors
- Clean up test data after tests
- Run tests in multiple browsers (Chromium, Firefox, WebKit)

## Test Organization

### Backend Test Structure
```
server_fastapi/tests/
├── conftest.py           # Shared fixtures
├── test_bots.py         # Bot-related tests
├── test_trades.py       # Trade-related tests
├── test_wallets.py      # Wallet-related tests
└── utils/
    ├── test_factories.py  # Test data factories
    └── test_database.py   # Database test utilities
```

### Frontend Test Structure
```
client/src/
├── components/
│   ├── BotCard/
│   │   ├── BotCard.tsx
│   │   └── BotCard.test.tsx
│   └── ...
├── hooks/
│   ├── useBot.ts
│   └── useBot.test.ts
└── ...
```

## Running Tests

### Backend
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=server_fastapi --cov-report=html

# Run specific test file
pytest server_fastapi/tests/test_bots.py

# Run specific test
pytest server_fastapi/tests/test_bots.py::test_create_bot
```

### Frontend
```bash
# Run all tests
npm run test:frontend

# Run with UI
npm run test:frontend:ui

# Run with coverage
npm run test:frontend:coverage
```

### E2E
```bash
# Run all E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run specific test
npx playwright test tests/e2e/bots.spec.ts
```

## When to Write Tests

- All new features require tests
- Bug fixes require regression tests
- Refactored code should maintain or improve test coverage
- Critical paths require integration tests
- Security-sensitive code requires comprehensive tests
