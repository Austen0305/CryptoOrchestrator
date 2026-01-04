# Research, Plan & Build - Remaining Modernization Tasks
**Date:** January 3, 2026  
**Approach:** Research → Plan → Build using all available MCPs and tools

---

## 📋 Remaining Tasks Analysis

### Task 1: TradingHeader Component Test
**Status:** Missing test file  
**Priority:** P1 (High)  
**Component:** `client/src/components/TradingHeader.tsx`  
**Existing Tests:** DEXTradingPanel.test.tsx, Wallet.test.tsx (good patterns to follow)

**Research Findings:**
- Component has good test IDs: `data-testid="badge-connection"`, `data-testid="text-balance"`, `data-testid="button-settings"`, `data-testid="button-login"`, `data-testid="button-logout"`
- Uses `useAuth` hook (needs mocking)
- Uses `useToast` hook (needs mocking)
- Has event listeners for `auth:expired` event
- Conditional rendering based on `isAuthenticated`

**Plan:**
1. Create test file following existing patterns
2. Mock `useAuth` and `useToast` hooks
3. Test rendering with authenticated/unauthenticated states
4. Test connection badge states
5. Test balance display
6. Test button interactions
7. Test auth modal opening/closing

---

### Task 2: E2E Authentication Fixes
**Status:** 4+ tests skipped due to authentication failures  
**Priority:** P1 (High)  
**Files:** `tests/e2e/critical-flows.spec.ts` (4 skipped), others

**Research Findings:**
- Auth helper exists: `tests/e2e/auth-helper.ts`
- Helper has retry logic and multiple verification methods
- Tests are skipping with: `test.skip(true, 'Authentication required but failed after retries')`
- Registration shim middleware might be affecting auth flow

**Plan:**
1. Review auth helper implementation
2. Check if registration shim affects E2E tests
3. Improve auth helper reliability
4. Add better error messages
5. Test auth flow manually in browser
6. Fix any issues found
7. Re-enable skipped tests

---

### Task 3: Registration Shim Investigation
**Status:** Workaround in place, needs root cause fix  
**Priority:** P0 (Critical)  
**File:** `server_fastapi/main.py` lines 709-923

**Research Findings:**
- Shim bypasses middleware stack
- Potential causes: RequestQueue, RequestBatching, RequestDeduplication, DB pool, Redis timeout
- Feature flag: `ENABLE_HEAVY_MIDDLEWARE` controls heavy middleware

**Plan:**
1. Create middleware profiling utility
2. Test with `ENABLE_HEAVY_MIDDLEWARE=false`
3. Profile each middleware layer
4. Identify blocking middleware
5. Fix or disable problematic middleware
6. Remove shim once fixed

---

## 🛠️ Execution Plan

### Phase 1: Component Test (TradingHeader)
**Estimated Time:** 30-45 minutes

1. ✅ Read existing test patterns (DEXTradingPanel, Wallet)
2. ✅ Analyze TradingHeader component structure
3. ⏳ Create test file with comprehensive coverage
4. ⏳ Run tests and fix any issues

### Phase 2: E2E Authentication Fixes
**Estimated Time:** 1-2 hours

1. ✅ Review auth helper implementation
2. ⏳ Test auth flow in browser (using browser MCP)
3. ⏳ Improve auth helper if needed
4. ⏳ Fix any registration/login issues
5. ⏳ Re-enable skipped tests
6. ⏳ Verify all tests pass

### Phase 3: Middleware Profiling
**Estimated Time:** 2-3 hours

1. ⏳ Create middleware profiling utility
2. ⏳ Test registration with profiling enabled
3. ⏳ Analyze profiling results
4. ⏳ Identify blocking middleware
5. ⏳ Fix or disable problematic middleware
6. ⏳ Remove shim once fixed

---

## 🎯 Success Criteria

- ✅ TradingHeader.test.tsx created with ≥80% coverage
- ✅ All E2E tests pass (no skipped tests)
- ✅ Registration works without shim
- ✅ Middleware profiling identifies bottlenecks
- ✅ All tests pass in CI/CD

---

## 📊 Progress Tracking

- [ ] TradingHeader test created
- [ ] E2E auth fixes applied
- [ ] Middleware profiling implemented
- [ ] Registration shim removed
- [ ] All tests passing

---

**Next Steps:** Execute Phase 1 (TradingHeader test)
