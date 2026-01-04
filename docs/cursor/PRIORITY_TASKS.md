# Priority Tasks for Cursor Agent

**Last Updated:** 2025-01-19  
**Project Status:** 95% complete

---

## 🔥 High Priority (Complete First)

### 1. Mobile Native Initialization
- **Status:** 88% complete
- **Location:** `mobile/` directory
- **Issue:** Native projects not initialized (iOS/Android folders missing)
- **Action:** 
  - Option A: Run `react-native init` and copy native folders
  - Option B: Use Expo (`npx expo init`)
- **Time:** 10-30 minutes
- **Files:** 
  - `mobile/package.json` (already configured)
  - `mobile/src/` (TypeScript code complete)
  - Need: `mobile/ios/` and `mobile/android/` folders
- **Reference:** `docs/progress/STATUS.md` (Mobile section)

### 2. Missing Component Tests
- **Status:** Some components lack tests
- **Priority Components:**
  - `client/src/components/DEXTradingPanel.tsx` - Critical trading functionality
  - `client/src/components/Wallet.tsx` - Wallet management
  - `client/src/components/WalletCard.tsx` - Wallet display
  - `client/src/components/TradingHeader.tsx` - Trading interface
  - `client/src/components/StrategyEditor.tsx` - Strategy creation
  - `client/src/components/BotCreator.tsx` - Bot creation
- **Pattern:** Use existing test files as templates
  - Example: `client/src/components/__tests__/TradingHeader.test.tsx`
- **Time:** 2-4 hours
- **Command:** `npm run test:frontend`

### 3. E2E Test Coverage Gaps
- **Status:** Core flows tested, some missing
- **Missing Flows:**
  - Portfolio management flow
  - Settings updates flow
  - Withdrawal with 2FA flow
  - Bot learning/training flow
  - Strategy marketplace flow
  - Copy trading flow
  - Price alerts flow
- **Pattern:** Use existing E2E tests as templates
  - Example: `tests/e2e/critical-flows.spec.ts`
- **Time:** 3-5 hours
- **Command:** `npm run test:e2e`

---

## ⭐ Medium Priority

### 4. Documentation Improvements
- **Status:** Good coverage, some gaps
- **Needed:**
  - API examples for some endpoints
  - Mobile app setup clarity (native init steps)
  - Deployment guide verification
  - Service usage examples
- **Time:** 2-3 hours
- **Location:** `docs/`

### 5. Mock Implementation Replacements
- **Status:** Some mocks exist, verify fallback works
- **Items:**
  - `MockAuthService` in `server_fastapi/routes/auth.py` - Should use real AuthService
  - Mock ML models - Check ML services for placeholders
  - `MockExchange` in integration adapters - Verify fallback logic
- **Action:** Test that fallback logic works correctly
- **Time:** 1-2 hours

### 6. Integration Adapters Status
- **Status:** Placeholder implementations exist
- **Files:**
  - `server/integrations/freqtrade_adapter.py` - Has mock/placeholder logic
  - `server/integrations/jesse_adapter.py` - Has mock implementation
- **Action:** Verify adapters work correctly even without full frameworks
- **Time:** 1 hour

---

## 📝 Low Priority

### 7. Performance Profiling
- **Status:** Optimizations verified, profiling needed
- **Items:**
  - Mobile app performance profiling (needs native projects)
  - Bundle size optimization review
  - Database query optimization review
- **Time:** 2-3 hours

### 8. Additional Features
- **Status:** Core features complete
- **Future Enhancements:**
  - Push notifications (mobile)
  - Background data fetching (mobile)
  - More chart types
  - Custom indicators
  - Watchlists
  - News feed
- **Time:** Variable

---

## ✅ Completed (Reference)

### Already Complete
- ✅ All critical phases (100%)
- ✅ Security features (100%)
- ✅ CI/CD workflows (100%)
- ✅ Performance optimizations (100%)
- ✅ Code quality tools (100%)
- ✅ E2E test infrastructure (5 suites, 36 tests)
- ✅ TypeScript errors fixed (0 remaining)
- ✅ Core component tests
- ✅ Core E2E flows

---

## 🎯 Recommended Order

1. **Mobile Native Init** (10-30 min) - Unblocks mobile testing
2. **Component Tests** (2-4 hours) - Improves code quality
3. **E2E Coverage** (3-5 hours) - Improves test coverage
4. **Documentation** (2-3 hours) - Improves developer experience
5. **Mock Verification** (1-2 hours) - Ensures reliability

**Total Estimated Time:** 8-14 hours

---

## 📋 Task Templates

### Component Test Template
```typescript
import { render, screen } from '@testing-library/react';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  it('renders correctly', () => {
    render(<ComponentName />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

### E2E Test Template
```typescript
import { test, expect } from '@playwright/test';

test('user flow description', async ({ page }) => {
  await page.goto('/');
  // Test steps
  await expect(page.locator('.result')).toBeVisible();
});
```

---

**See Also:**
- `Todo.md` - Complete task list
- `docs/cursor/AGENT_CONTEXT.md` - Project context
- `docs/CURSOR_AGENT_OPTIMIZATION.md` - Optimization guide
