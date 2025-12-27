---
name: ""
overview: ""
todos: []
---

# Complete E2E Testing and Fix Plan

## Overview

This plan systematically tests everything end-to-end, identifies all issues, fixes them, and optimizes performance to ensure the CryptoOrchestrator project works perfectly and runs as fast as possible.

## Current State Analysis

**Project Status:**

- 98% complete (132/135 tasks) according to TODO.md
- 20 E2E test files covering major features
- Zero linter errors detected
- Comprehensive testing infrastructure in place
- Performance optimizations already implemented

## Implementation Progress

### Fixes Applied (2025-12-11)

1. **Fixed test-e2e-complete.js path issues:**

   - Fixed `projectRoot` calculation (was `scripts/`, now `scripts/../..`)
   - Fixed `validate-environment.js` import path (now `scripts/utilities/validate-environment.js`)
   - Fixed `service-manager.js` import path (now `../utilities/service-manager.js`)
   - Fixed `run-puppeteer-tests.js` path (now `scripts/testing/run-puppeteer-tests.js`)

2. **Fixed service-manager.js Python path:**

   - Added `PYTHONPATH: projectRoot` to FastAPI startup environment
   - This fixes `ModuleNotFoundError: No module named 'server_fastapi'`

3. **Installed Playwright browsers:**

   - Installed Chromium, Firefox, and WebKit browsers for E2E testing

### Current Blockers

1. **Docker not running:**

   - PostgreSQL and Redis containers cannot start without Docker
   - Service manager gracefully skips Docker services if Docker unavailable
   - Tests can still run if services are running locally or using SQLite

2. **Services need to be running for E2E tests:**

   - FastAPI backend needs to be running on port 8000
   - React frontend needs to be running on port 5173
   - Database (PostgreSQL or SQLite) needs to be available

**Key Components:**

- Backend: FastAPI (Python 3.12) with async operations
- Frontend: React 18 + TypeScript + TanStack Query
- Desktop: Electron with Python runtime bundling
- Mobile: React Native/Expo
- Testing: Playwright E2E, Puppeteer, Vitest, Pytest

## Phase 1: Environment & Prerequisites Verification

### 1.1 Environment Setup

- **Verify Python 3.12+ installation** - Check version and PATH
- **Verify Node.js 18+ installation** - Check version and npm
- **Verify PostgreSQL/Redis availability** - Check if services are running (optional)
- **Verify environment variables** - Check `.env` file exists and has required variables
- **Install/update dependencies** - Run `npm install --legacy-peer-deps` and `pip install -r requirements.txt`
- **Verify ports availability** - Check ports 8000 (backend) and 5173 (frontend) are free

**Files to check:**

- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies

### 1.2 TypeScript & Build Verification

- **Run TypeScript type check** - `npm run check` (fix PowerShell syntax if needed)
- **Run ESLint** - `npm run lint` to verify no linting errors
- **Run Prettier check** - `npm run format:check` to verify formatting
- **Build frontend** - `npm run build` to verify build succeeds
- **Build backend** - Verify FastAPI imports work correctly

**Files to check:**

- `client/tsconfig.json` - TypeScript configuration
- `.eslintrc.json` - ESLint configuration
- `vite.config.ts` - Build configuration

## Phase 2: Comprehensive E2E Testing

### 2.1 Service Startup & Health Checks

- **Start all services** - Use `npm run start:all` or manual startup
- **Verify backend health** - Check `http://localhost:8000/health` endpoint
- **Verify frontend accessibility** - Check `http://localhost:5173` loads
- **Verify database connection** - Check backend can connect to database
- **Verify Redis connection** - Check backend can connect to Redis (if available)

**Scripts to use:**

- `scripts/utilities/start-all-services.js` - Unified service startup
- `scripts/utilities/check-services.js` - Service health checks
- `scripts/utilities/validate-environment.js` - Environment validation

### 2.2 Run Complete E2E Test Suite

- **Run unified E2E tests** - `npm run test:e2e:complete` (Playwright + Puppeteer)
- **Run Playwright tests individually** - `npm run test:e2e` for detailed results
- **Run Puppeteer tests** - `npm run test:puppeteer` for critical flows
- **Generate test reports** - Review HTML and JSON reports in `test-results/`

**Test suites to verify:**

- `tests/e2e/auth.spec.ts` - Authentication flows
- `tests/e2e/bots.spec.ts` - Bot management
- `tests/e2e/trading.spec.ts` - Trading operations
- `tests/e2e/wallet.spec.ts` - Wallet management
- `tests/e2e/dex-swap.spec.ts` - DEX swap operations
- `tests/e2e/withdrawal-flow.spec.ts` - Withdrawal flows
- All other E2E test files

### 2.3 Backend Unit & Integration Tests

- **Run backend tests** - `pytest server_fastapi/tests/ -v --cov=server_fastapi`
- **Check test coverage** - Verify ≥85% coverage target
- **Run specific test suites** - Test critical services (wallet, DEX, trading)
- **Verify test database isolation** - Ensure tests don't interfere with each other

**Key test files:**

- `server_fastapi/tests/test_bot_service.py` - Bot service tests
- `server_fastapi/tests/test_trading_integration.py` - Trading integration tests
- `server_fastapi/tests/test_wallet_service.py` - Wallet service tests
- All other test files in `server_fastapi/tests/`

### 2.4 Frontend Unit Tests

- **Run frontend tests** - `npm run test:frontend`
- **Check component tests** - Verify all component tests pass
- **Check hook tests** - Verify all hook tests pass
- **Generate coverage report** - `npm run test:frontend:coverage`

**Key test files:**

- `client/src/components/__tests__/` - Component tests
- `client/src/hooks/__tests__/` - Hook tests

## Phase 3: Issue Identification & Analysis

### 3.1 Test Failure Analysis

- **Collect all test failures** - Document failing tests from E2E, unit, and integration tests
- **Categorize failures** - Group by type (authentication, API, UI, database, etc.)
- **Identify root causes** - Analyze error messages and stack traces
- **Prioritize fixes** - Critical issues first, then high-priority, then medium/low

### 3.2 Code Quality Issues

- **TypeScript errors** - Run `npm run check` and fix all type errors
- **Linting issues** - Run `npm run lint` and fix all warnings/errors
- **Python linting** - Run `flake8 server_fastapi/` and fix issues
- **Code formatting** - Run `npm run format` and `black server_fastapi/` to format code

### 3.3 Performance Analysis

- **Run load tests** - `npm run load:test:comprehensive` to identify bottlenecks
- **Check bundle size** - Verify bundle sizes are within limits (<1MB per chunk)
- **Database query analysis** - Check for N+1 queries, missing indexes
- **API response times** - Identify slow endpoints (>2s response time)
- **Memory usage** - Check for memory leaks or excessive memory usage

**Tools to use:**

- `scripts/utilities/load_test.py` - Load testing script
- `scripts/utilities/bundle-analyze.js` - Bundle size analysis
- Browser DevTools - Performance profiling
- Backend monitoring - Performance metrics

### 3.4 Security & Configuration Issues

- **Run security scans** - `npm run audit:security` and fix vulnerabilities
- **Check environment variables** - Verify all required variables are set
- **Verify CORS configuration** - Check CORS settings for production
- **Check authentication** - Verify JWT token validation works correctly
- **Verify rate limiting** - Check rate limiting is working

## Phase 4: Systematic Fixes

### 4.1 Critical Fixes (Blocking Issues)

- **Fix authentication failures** - Resolve any auth-related test failures
- **Fix database connection issues** - Resolve database connectivity problems
- **Fix API endpoint errors** - Fix 500 errors, missing endpoints, incorrect responses
- **Fix build failures** - Resolve any build errors preventing deployment
- **Fix startup failures** - Ensure all services start correctly

**Files likely to need fixes:**

- `server_fastapi/main.py` - Backend startup and configuration
- `server_fastapi/database/` - Database connection and migrations
- `client/src/lib/api.ts` - API client configuration
- `tests/e2e/global-setup.ts` - E2E test setup

### 4.2 High-Priority Fixes (Feature-Breaking)

- **Fix UI component errors** - Resolve React component errors and warnings
- **Fix API integration issues** - Fix frontend-backend integration problems
- **Fix WebSocket connections** - Ensure WebSocket real-time updates work
- **Fix form validation** - Ensure all forms validate correctly
- **Fix error handling** - Improve error messages and error boundaries

**Files likely to need fixes:**

- `client/src/components/` - React components
- `client/src/hooks/useApi.ts` - API hooks
- `client/src/hooks/useWebSocket.ts` - WebSocket hooks
- `server_fastapi/routes/` - API routes

### 4.3 Medium-Priority Fixes (Quality Issues)

- **Fix TypeScript errors** - Resolve all type errors and improve type safety
- **Fix linting warnings** - Resolve ESLint and Flake8 warnings
- **Fix test flakiness** - Improve test reliability and add retries
- **Fix accessibility issues** - Improve ARIA labels and keyboard navigation
- **Fix mobile responsiveness** - Ensure UI works on mobile devices

**Files likely to need fixes:**

- TypeScript files with type errors
- Files with linting warnings
- Test files with flaky tests
- Component files missing accessibility attributes

### 4.4 Performance Optimizations

- **Optimize database queries** - Add indexes, fix N+1 queries, use eager loading
- **Optimize API responses** - Add caching, implement pagination, optimize serialization
- **Optimize frontend bundle** - Code splitting, tree shaking, lazy loading
- **Optimize images** - Use WebP/AVIF, implement lazy loading, responsive images
- **Optimize WebSocket** - Reduce message frequency, implement batching

**Files likely to need optimization:**

- `server_fastapi/repositories/` - Database queries
- `server_fastapi/utils/query_optimizer.py` - Query optimization utilities
- `server_fastapi/utils/cache_utils.py` - Caching utilities
- `vite.config.ts` - Build optimization
- `client/src/utils/performance.ts` - Performance utilities

## Phase 5: Verification & Validation

### 5.1 Re-run All Tests

- **Re-run E2E tests** - Verify all tests pass after fixes
- **Re-run unit tests** - Verify all unit tests pass
- **Re-run integration tests** - Verify all integration tests pass
- **Check test coverage** - Ensure coverage remains ≥85%

### 5.2 Manual Testing

- **Test authentication flow** - Sign up, sign in, sign out
- **Test bot management** - Create, start, stop, delete bots
- **Test trading operations** - Paper trading, real trading (if configured)
- **Test wallet operations** - View balance, deposit, withdraw
- **Test DEX swaps** - Execute swaps, check transaction status
- **Test real-time updates** - Verify WebSocket updates work
- **Test error handling** - Verify error messages are user-friendly

### 5.3 Performance Validation

- **Verify load test improvements** - Compare before/after metrics
- **Verify bundle size** - Ensure bundles are optimized
- **Verify API response times** - Ensure <2s for most endpoints
- **Verify database query performance** - Check query execution times
- **Verify memory usage** - Ensure no memory leaks

### 5.4 Security Validation

- **Verify no vulnerabilities** - Run security scans and verify clean
- **Verify authentication** - Test JWT token validation
- **Verify authorization** - Test user permissions and access control
- **Verify input validation** - Test all input validation
- **Verify rate limiting** - Test rate limiting works correctly

## Phase 6: Documentation & Reporting

### 6.1 Create Test Report

- **Document test results** - Create comprehensive test report with pass/fail status
- **Document fixes applied** - List all fixes made during the process
- **Document performance improvements** - Document performance optimizations and metrics
- **Document remaining issues** - List any issues that couldn't be fixed (if any)

### 6.2 Update Documentation

- **Update README** - Update with latest status and improvements
- **Update CHANGELOG** - Document all changes made
- **Update TODO.md** - Update progress and mark completed tasks
- **Create completion summary** - Create summary document of all work done

## Implementation Strategy

### Execution Order

1. **Phase 1** - Environment setup (30 minutes)
2. **Phase 2** - Run all tests (2-3 hours)
3. **Phase 3** - Analyze results (1 hour)
4. **Phase 4** - Fix issues systematically (4-8 hours, depending on issues found)
5. **Phase 5** - Verify fixes (2-3 hours)
6. **Phase 6** - Documentation (1 hour)

### Tools & Scripts to Use

- **Service Management**: `scripts/utilities/start-all-services.js`
- **E2E Testing**: `scripts/testing/test-e2e-complete.js`
- **Load Testing**: `scripts/utilities/load_test.py`
- **Bundle Analysis**: `scripts/utilities/bundle-analyze.js`
- **Environment Validation**: `scripts/utilities/validate-environment.js`

### MCP Tool Decision Tree

**When to Use Each MCP Tool:**

#### Browser MCP (Primary for Frontend Testing)

- ✅ **ALWAYS use** for manual UI testing
- ✅ **ALWAYS use** to verify fixes work visually
- ✅ **ALWAYS use** to test user flows end-to-end
- ✅ **ALWAYS use** to take screenshots for documentation
- ✅ **ALWAYS use** to check API responses in DevTools
- ✅ **ALWAYS use** to monitor WebSocket connections
- ✅ **ALWAYS use** to test error scenarios
- ✅ **ALWAYS use** to verify accessibility (keyboard nav, ARIA)
- ✅ **ALWAYS use** to test mobile responsiveness

#### CoinGecko MCP (Cryptocurrency Prices)

- ✅ **Use when** testing trading features
- ✅ **Use when** verifying price data accuracy
- ✅ **Use when** testing DEX swaps (verify token prices)
- ✅ **Use when** testing bot creation (verify market data)
- ✅ **Use when** debugging price-related issues

#### Web3 MCP (Blockchain Operations)

- ✅ **Use when** testing wallet features
- ✅ **Use when** verifying wallet balances match blockchain
- ✅ **Use when** testing DEX swaps (verify transaction status)
- ✅ **Use when** testing withdrawals (verify transactions)
- ✅ **Use when** debugging blockchain-related issues

#### DeFi Trading MCP (Trading & Portfolio)

- ✅ **Use when** testing trading operations
- ✅ **Use when** verifying portfolio data
- ✅ **Use when** testing DEX liquidity
- ✅ **Use when** debugging trading-related issues

#### Postgres/SQLite MCP (Database)

- ✅ **Use when** testing database connectivity
- ✅ **Use when** verifying data integrity after operations
- ✅ **Use when** analyzing slow queries
- ✅ **Use when** checking indexes
- ✅ **Use when** debugging database-related issues

#### Context7 MCP (Library Documentation)

- ✅ **Use when** researching FastAPI patterns
- ✅ **Use when** researching React/TypeScript patterns
- ✅ **Use when** researching SQLAlchemy patterns
- ✅ **Use when** researching Vite build issues
- ✅ **Use when** researching error solutions
- ✅ **Use when** need latest library documentation

#### StackOverflow MCP (Community Solutions)

- ✅ **Use when** encountering specific error messages
- ✅ **Use when** need community-tested solutions
- ✅ **Use when** debugging common issues
- ✅ **Use when** Context7 doesn't have the answer

#### Brave Search MCP (Best Practices)

- ✅ **Use when** researching best practices
- ✅ **Use when** researching security best practices
- ✅ **Use when** researching performance optimization
- ✅ **Use when** Context7 and StackOverflow don't cover it

#### Sequential Thinking MCP (Complex Reasoning)

- ✅ **Use when** analyzing complex issues
- ✅ **Use when** prioritizing fixes
- ✅ **Use when** making architectural decisions
- ✅ **Use when** analyzing trade-offs

#### Memory-Bank MCP (Knowledge Storage)

- ✅ **Use BEFORE** starting: Retrieve stored patterns and decisions
- ✅ **Use AFTER** fixes: Store fix patterns for future reference
- ✅ **Use AFTER** decisions: Store architectural decisions
- ✅ **Use AFTER** testing: Store test results and metrics

#### Filesystem MCP (File Operations)

- ✅ **Use when** reading configuration files
- ✅ **Use when** reading test files
- ✅ **Use when** reading documentation
- ✅ **Use when** bulk file operations needed

#### Redis MCP (Cache)

- ✅ **Use when** testing Redis connectivity
- ✅ **Use when** debugging cache issues
- ✅ **Use when** verifying cache operations

#### ArXiv MCP (Research Papers)

- ✅ **Use when** implementing ML features
- ✅ **Use when** researching trading algorithms
- ✅ **Use when** need academic approaches

#### GitHub MCP (Repository)

- ✅ **Use when** need to understand git history
- ✅ **Use when** creating branches for fixes
- ✅ **Use when** reviewing PRs/issues

### Pattern Matching

- **Backend routes**: Match FastAPI Route Pattern from `.cursor/extracted-patterns.md`
- **Frontend hooks**: Match React Query Hook Pattern from `.cursor/extracted-patterns.md`
- **Services**: Match Service Layer Pattern from `.cursor/extracted-patterns.md`
- **Repositories**: Match Repository Pattern from `.cursor/extracted-patterns.md`

### Feature-by-Feature Testing Strategy

For each feature, follow this testing pattern:

1. **Read Intelligence Files** (AUTOMATIC):

- Read `.cursor/extracted-patterns.md` - Find matching patterns
- Read `.cursor/knowledge-base.md` - Check for existing solutions
- Use Memory-Bank MCP to retrieve stored patterns

2. **Research** (if needed):

- Use Context7 MCP for library patterns
- Use StackOverflow MCP for error solutions
- Use Brave Search MCP for best practices

3. **Test with Browser MCP**:

- Navigate to feature page
- Test all user interactions
- Take screenshots
- Verify functionality

4. **Verify with Crypto MCPs** (if applicable):

- CoinGecko MCP for price data
- Web3 MCP for blockchain operations
- DeFi Trading MCP for trading features

5. **Verify with Database MCP**:

- Postgres MCP to verify data operations
- Check data integrity

6. **Fix Issues**:

- Match extracted patterns
- Apply fixes
- Test again with Browser MCP

7. **Store Results**:

- Use Memory-Bank MCP to store fix patterns
- Update documentation

## Success Criteria

### Must Have (Critical)

- ✅ All E2E tests pass
- ✅ All unit tests pass (≥85% coverage)
- ✅ All integration tests pass
- ✅ No TypeScript errors
- ✅ No linting errors
- ✅ All services start successfully
- ✅ All critical features work end-to-end

### Should Have (High Priority)

- ✅ Performance improvements verified (load test metrics)
- ✅ Bundle sizes optimized (<1MB per chunk)
- ✅ API response times <2s for most endpoints
- ✅ No security vulnerabilities
- ✅ All forms validate correctly
- ✅ Error handling works correctly

### Nice to Have (Medium Priority)

- ✅ All accessibility improvements
- ✅ All mobile optimizations
- ✅ Comprehensive documentation updates
- ✅ Performance monitoring in place

## Risk Mitigation

### Potential Issues

- **Service startup failures** - Use retry logic and better error messages
- **Test flakiness** - Add retries and improve test isolation
- **Performance regressions** - Compare before/after metrics
- **Breaking changes** - Test thoroughly before applying fixes
- **Dependency issues** - Verify all dependencies are compatible

### Mitigation Strategies

- **Incremental fixes** - Fix one issue at a time and verify
- **Test after each fix** - Run relevant tests after each fix
- **Backup before changes** - Create backups before major changes
- **Use version control** - Commit changes frequently with clear messages
- **Document decisions** - Document why fixes were made

## Feature-by-Feature Testing Checklist

### Authentication & User Management

- [ ] **Browser MCP**: Test sign up flow (navigate, fill form, submit, verify)
- [ ] **Browser MCP**: Test sign in flow (navigate, fill form, submit, verify)
- [ ] **Browser MCP**: Test sign out flow (click sign out, verify token cleared)
- [ ] **Browser MCP**: Test password reset flow
- [ ] **Postgres MCP**: Verify user data in database after signup
- [ ] **Browser MCP**: Test authentication state persistence (refresh page)
- [ ] **Browser MCP**: Test protected routes (redirect if not authenticated)
- [ ] **CoinGecko MCP**: Not applicable
- **Files**: `client/src/pages/Login.tsx`, `client/src/pages/Register.tsx`, `server_fastapi/routes/auth.py`

### Bot Management

- [ ] **Browser MCP**: Test bot creation (navigate, fill form, submit, verify)
- [ ] **Browser MCP**: Test bot list (verify bots display correctly)
- [ ] **Browser MCP**: Test bot start (click start, verify status updates)
- [ ] **Browser MCP**: Test bot stop (click stop, verify status updates)
- [ ] **Browser MCP**: Test bot delete (click delete, confirm, verify removal)
- [ ] **Browser MCP**: Test bot editing (edit bot config, save, verify)
- [ ] **CoinGecko MCP**: Verify price data used in bot creation
- [ ] **Postgres MCP**: Verify bot data in database
- **Files**: `client/src/pages/Bots.tsx`, `client/src/components/BotCreator.tsx`, `server_fastapi/routes/bots.py`

### Trading Operations

- [ ] **Browser MCP**: Test paper trading mode (switch mode, execute trade, verify)
- [ ] **Browser MCP**: Test real trading mode (switch mode, execute trade, verify)
- [ ] **Browser MCP**: Test trading mode switching (verify mode persists)
- [ ] **Browser MCP**: Test order placement (market, limit, stop-loss orders)
- [ ] **Browser MCP**: Test order cancellation
- [ ] **CoinGecko MCP**: Verify market data accuracy
- [ ] **Postgres MCP**: Verify trade data in database
- **Files**: `client/src/pages/TradingBots.tsx`, `client/src/components/OrderEntryPanel.tsx`, `server_fastapi/routes/trading.py`

### Wallet Management

- [ ] **Browser MCP**: Test wallet creation (create wallet, verify address)
- [ ] **Browser MCP**: Test balance display (verify balance shows correctly)
- [ ] **Browser MCP**: Test deposit flow (generate QR, verify address)
- [ ] **Browser MCP**: Test withdrawal flow (enter amount, address, verify 2FA)
- [ ] **Browser MCP**: Test transaction history (verify transactions display)
- [ ] **Web3 MCP**: Verify wallet balances match blockchain
- [ ] **Web3 MCP**: Verify deposit transactions on blockchain
- [ ] **Web3 MCP**: Verify withdrawal transactions on blockchain
- [ ] **Postgres MCP**: Verify wallet data in database
- **Files**: `client/src/pages/Wallet.tsx`, `client/src/components/Wallet.tsx`, `server_fastapi/routes/wallet.py`

### DEX Trading

- [ ] **Browser MCP**: Test DEX swap UI (navigate, select tokens, enter amount)
- [ ] **Browser MCP**: Test quote retrieval (get quote, verify price impact)
- [ ] **Browser MCP**: Test price impact warning (verify warning shows if >1%)
- [ ] **Browser MCP**: Test swap execution (execute swap, verify transaction)
- [ ] **Browser MCP**: Test transaction status tracking (verify status updates)
- [ ] **CoinGecko MCP**: Verify token prices for swap calculation
- [ ] **Web3 MCP**: Verify swap transaction on blockchain
- [ ] **DeFi Trading MCP**: Verify swap execution and liquidity
- [ ] **Postgres MCP**: Verify swap data in database
- **Files**: `client/src/components/DEXTradingPanel.tsx`, `server_fastapi/routes/dex_trading.py`

### Portfolio & Analytics

- [ ] **Browser MCP**: Test portfolio display (verify balances, positions)
- [ ] **Browser MCP**: Test performance charts (verify charts render)
- [ ] **Browser MCP**: Test analytics dashboard (verify metrics display)
- [ ] **CoinGecko MCP**: Verify portfolio valuation uses accurate prices
- [ ] **DeFi Trading MCP**: Verify portfolio analysis data
- [ ] **Postgres MCP**: Verify portfolio data in database
- **Files**: `client/src/pages/Dashboard.tsx`, `client/src/pages/PerformanceDashboard.tsx`, `server_fastapi/routes/portfolio.py`

### Real-Time Updates (WebSocket)

- [ ] **Browser MCP**: Test WebSocket connection (verify connection established)
- [ ] **Browser MCP**: Test price updates (verify prices update in real-time)
- [ ] **Browser MCP**: Test balance updates (verify balances update in real-time)
- [ ] **Browser MCP**: Test trade updates (verify trades update in real-time)
- [ ] **Browser MCP**: Test WebSocket reconnection (disconnect, verify reconnects)
- [ ] **Browser DevTools**: Monitor WebSocket messages in Network tab
- **Files**: `client/src/hooks/useWebSocket.ts`, `server_fastapi/routes/websocket_*.py`

### Settings & Preferences

- [ ] **Browser MCP**: Test settings page (navigate, verify settings display)
- [ ] **Browser MCP**: Test preference changes (change setting, verify saves)
- [ ] **Browser MCP**: Test theme switching (switch theme, verify persists)
- [ ] **Postgres MCP**: Verify settings data in database
- **Files**: `client/src/pages/Settings.tsx`, `server_fastapi/routes/settings.py`

### Mobile App (if applicable)

- [ ] **Browser MCP**: Test mobile viewport (resize to mobile, verify responsive)
- [ ] **Browser MCP**: Test touch interactions (verify touch targets are 44x44px)
- [ ] **Browser MCP**: Test mobile navigation (verify mobile menu works)
- **Files**: `mobile/src/screens/`, `mobile/src/components/`

## Complete MCP & Tool Usage Guide

### When to Use Browser MCP (Primary Tool for Frontend)

**ALWAYS use Browser MCP for:**

- ✅ Manual testing of ALL UI features
- ✅ Verifying fixes work visually
- ✅ Testing user flows end-to-end
- ✅ Taking screenshots for documentation
- ✅ Checking API responses in DevTools Network tab
- ✅ Monitoring WebSocket connections in DevTools
- ✅ Testing error scenarios and error boundaries
- ✅ Verifying accessibility (keyboard navigation, ARIA labels)
- ✅ Testing mobile responsiveness (resize window, check viewport)
- ✅ Measuring performance (Network tab, Performance tab)
- ✅ Debugging frontend issues interactively

**Browser MCP Commands to Use:**

- `browser_navigate(url)` - Navigate to pages
- `browser_snapshot()` - Get page structure for interactions
- `browser_click(element, ref)` - Click buttons, links
- `browser_type(element, ref, text)` - Fill forms
- `browser_take_screenshot(filename)` - Capture screenshots
- `browser_evaluate(function)` - Run JavaScript on page
- `browser_console_messages()` - Check console errors
- `browser_network_requests()` - Check API calls

### When to Use CoinGecko MCP

**Use CoinGecko MCP when:**

- ✅ Testing trading features (verify price data)
- ✅ Testing bot creation (verify market data used)
- ✅ Testing DEX swaps (verify token prices for calculation)
- ✅ Testing portfolio valuation (verify prices used)
- ✅ Debugging price-related issues
- ✅ Verifying price data accuracy in tests

**CoinGecko MCP Commands:**

- `call-tool(serverName: "coingecko", toolName: "get_price", toolArgs: {symbol: "BTC"})`
- `call-tool(serverName: "coingecko", toolName: "get_historical", toolArgs: {symbol: "ETH", days: 30})`

### When to Use Web3 MCP

**Use Web3 MCP when:**

- ✅ Testing wallet features (verify balances match blockchain)
- ✅ Testing deposits (verify transactions on blockchain)
- ✅ Testing withdrawals (verify transactions on blockchain)
- ✅ Testing DEX swaps (verify transaction status)
- ✅ Debugging blockchain-related issues
- ✅ Verifying multi-chain operations

**Web3 MCP Commands:**

- `call-tool(serverName: "web3", toolName: "get_balance", toolArgs: {address: "...", chain: "ethereum"})`
- `call-tool(serverName: "web3", toolName: "get_transaction", toolArgs: {tx_hash: "...", chain: "ethereum"})`

### When to Use DeFi Trading MCP

**Use DeFi Trading MCP when:**

- ✅ Testing trading operations (verify execution)
- ✅ Testing portfolio analysis (verify data)
- ✅ Testing DEX liquidity (verify liquidity data)
- ✅ Debugging trading-related issues

**DeFi Trading MCP Commands:**

- `call-tool(serverName: "defi-trading", toolName: "get_portfolio", toolArgs: {address: "..."})`
- `call-tool(serverName: "defi-trading", toolName: "get_liquidity", toolArgs: {token_pair: "USDC/ETH"})`

### When to Use Postgres/SQLite MCP

**Use Postgres/SQLite MCP when:**

- ✅ Testing database connectivity
- ✅ Verifying data integrity after operations
- ✅ Analyzing slow queries (EXPLAIN ANALYZE)
- ✅ Checking indexes exist
- ✅ Debugging database-related issues
- ✅ Verifying test database state

**Postgres MCP Commands:**

- `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "SELECT * FROM users"})`
- `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "EXPLAIN ANALYZE SELECT ..."})`

### When to Use Context7 MCP

**Use Context7 MCP when:**

- ✅ Researching FastAPI patterns (async, dependencies, error handling)
- ✅ Researching React/TypeScript patterns (hooks, components, error boundaries)
- ✅ Researching SQLAlchemy patterns (queries, eager loading, transactions)
- ✅ Researching Vite build issues (bundle optimization, code splitting)
- ✅ Researching TanStack Query patterns (caching, invalidation, mutations)
- ✅ Researching WebSocket patterns (FastAPI + React)
- ✅ Researching form validation (react-hook-form + Zod)
- ✅ Need latest library documentation

**Context7 MCP Usage:**

- Search for library-specific patterns and solutions
- Get latest documentation when local docs might be outdated

### When to Use StackOverflow MCP

**Use StackOverflow MCP when:**

- ✅ Encountering specific error messages
- ✅ Need community-tested solutions
- ✅ Debugging common issues
- ✅ Context7 doesn't have the answer

**StackOverflow MCP Commands:**

- `call-tool(serverName: "stackoverflow", toolName: "search", toolArgs: {query: "FastAPI async dependency injection error"})`

### When to Use Brave Search MCP

**Use Brave Search MCP when:**

- ✅ Researching best practices (security, performance, accessibility)
- ✅ Researching when Context7 and StackOverflow don't cover it
- ✅ Need current industry standards (2025)
- ✅ Researching security vulnerabilities and fixes

**Brave Search MCP Commands:**

- `call-tool(serverName: "brave-search", toolName: "search", toolArgs: {query: "FastAPI performance optimization 2025"})`

### When to Use Sequential Thinking MCP

**Use Sequential Thinking MCP when:**

- ✅ Analyzing complex issues (multiple root causes)
- ✅ Prioritizing fixes (impact analysis)
- ✅ Making architectural decisions
- ✅ Analyzing trade-offs between approaches

### When to Use Memory-Bank MCP

**Use Memory-Bank MCP:**

- ✅ **BEFORE starting**: Retrieve stored patterns and decisions
- `read_global_memory_bank({docs: ".cursor", path: "patterns/*.json"})`
- ✅ **AFTER fixes**: Store fix patterns for future reference
- `write_global_memory_bank({docs: ".cursor", path: "fixes/...", content: "..."})`
- ✅ **AFTER decisions**: Store architectural decisions
- `write_global_memory_bank({docs: ".cursor", path: "decisions/...", content: "..."})`
- ✅ **AFTER testing**: Store test results and metrics
- `write_global_memory_bank({docs: ".cursor", path: "test-results/...", content: "..."})`

### When to Use Filesystem MCP

**Use Filesystem MCP when:**

- ✅ Reading configuration files
- ✅ Reading test files
- ✅ Reading documentation
- ✅ Bulk file operations needed
- ✅ Writing documentation files

### When to Use Redis MCP

**Use Redis MCP when:**

- ✅ Testing Redis connectivity
- ✅ Debugging cache issues
- ✅ Verifying cache operations
- ✅ Checking cache keys and values

### When to Use ArXiv MCP

**Use ArXiv MCP when:**

- ✅ Implementing ML features
- ✅ Researching trading algorithms
- ✅ Need academic approaches to problems

### When to Use GitHub MCP

**Use GitHub MCP when:**

- ✅ Need to understand git history
- ✅ Creating branches for fixes
- ✅ Reviewing PRs/issues
- ✅ Committing changes

## Notes

- **Use Intelligence System FIRST** - Always check `.cursor/extracted-patterns.md` and `.cursor/knowledge-base.md` before making changes
- **Match Existing Patterns** - Follow patterns from codebase (103 patterns available)
- **Test Incrementally** - Don't wait until the end to test, test after each fix
- **Document Everything** - Document all fixes and decisions made, store in Memory-Bank
- **Performance First** - Optimize performance as issues are fixed
- **Browser MCP is Primary** - Use Browser MCP for ALL manual testing and verification
- **Crypto MCPs for Verification** - Use CoinGecko, Web3, DeFi Trading MCPs to verify crypto features
- **Database MCPs for Data** - Use Postgres/SQLite MCPs to verify data operations
- **Research MCPs for Solutions** - Use Context7, StackOverflow, Brave Search for research
- **Memory-Bank for Storage** - Store all important patterns, fixes, and decisions

## Complete MCP & Tool Usage Guide

### When to Use Browser MCP (Primary Tool for Frontend)

**ALWAYS use Browser MCP for:**

- ✅ Manual testing of ALL UI features
- ✅ Verifying fixes work visually
- ✅ Testing user flows end-to-end
- ✅ Taking screenshots for documentation
- ✅ Checking API responses in DevTools Network tab
- ✅ Monitoring WebSocket connections in DevTools
- ✅ Testing error scenarios and error boundaries
- ✅ Verifying accessibility (keyboard navigation, ARIA labels)
- ✅ Testing mobile responsiveness (resize window, check viewport)
- ✅ Measuring performance (Network tab, Performance tab)
- ✅ Debugging frontend issues interactively

**Browser MCP Commands to Use:**

- `browser_navigate(url)` - Navigate to pages
- `browser_snapshot()` - Get page structure for interactions
- `browser_click(element, ref)` - Click buttons, links
- `browser_type(element, ref, text)` - Fill forms
- `browser_take_screenshot(filename)` - Capture screenshots
- `browser_evaluate(function)` - Run JavaScript on page
- `browser_console_messages()` - Check console errors
- `browser_network_requests()` - Check API calls

### When to Use CoinGecko MCP

**Use CoinGecko MCP when:**

- ✅ Testing trading features (verify price data)
- ✅ Testing bot creation (verify market data used)
- ✅ Testing DEX swaps (verify token prices for calculation)
- ✅ Testing portfolio valuation (verify prices used)
- ✅ Debugging price-related issues
- ✅ Verifying price data accuracy in tests

**CoinGecko MCP Commands:**

- `call-tool(serverName: "coingecko", toolName: "get_price", toolArgs: {symbol: "BTC"})`
- `call-tool(serverName: "coingecko", toolName: "get_historical", toolArgs: {symbol: "ETH", days: 30})`

### When to Use Web3 MCP

**Use Web3 MCP when:**

- ✅ Testing wallet features (verify balances match blockchain)
- ✅ Testing deposits (verify transactions on blockchain)
- ✅ Testing withdrawals (verify transactions on blockchain)
- ✅ Testing DEX swaps (verify transaction status)
- ✅ Debugging blockchain-related issues
- ✅ Verifying multi-chain operations

**Web3 MCP Commands:**

- `call-tool(serverName: "web3", toolName: "get_balance", toolArgs: {address: "...", chain: "ethereum"})`
- `call-tool(serverName: "web3", toolName: "get_transaction", toolArgs: {tx_hash: "...", chain: "ethereum"})`

### When to Use DeFi Trading MCP

**Use DeFi Trading MCP when:**

- ✅ Testing trading operations (verify execution)
- ✅ Testing portfolio analysis (verify data)
- ✅ Testing DEX liquidity (verify liquidity data)
- ✅ Debugging trading-related issues

**DeFi Trading MCP Commands:**

- `call-tool(serverName: "defi-trading", toolName: "get_portfolio", toolArgs: {address: "..."})`
- `call-tool(serverName: "defi-trading", toolName: "get_liquidity", toolArgs: {token_pair: "USDC/ETH"})`

### When to Use Postgres/SQLite MCP

**Use Postgres/SQLite MCP when:**

- ✅ Testing database connectivity
- ✅ Verifying data integrity after operations
- ✅ Analyzing slow queries (EXPLAIN ANALYZE)
- ✅ Checking indexes exist
- ✅ Debugging database-related issues
- ✅ Verifying test database state

**Postgres MCP Commands:**

- `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "SELECT * FROM users"})`
- `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "EXPLAIN ANALYZE SELECT ..."})`

### When to Use Context7 MCP

**Use Context7 MCP when:**

- ✅ Researching FastAPI patterns (async, dependencies, error handling)
- ✅ Researching React/TypeScript patterns (hooks, components, error boundaries)
- ✅ Researching SQLAlchemy patterns (queries, eager loading, transactions)
- ✅ Researching Vite build issues (bundle optimization, code splitting)
- ✅ Researching TanStack Query patterns (caching, invalidation, mutations)
- ✅ Researching WebSocket patterns (FastAPI + React)
- ✅ Researching form validation (react-hook-form + Zod)
- ✅ Need latest library documentation

**Context7 MCP Usage:**

- Search for library-specific patterns and solutions
- Get latest documentation when local docs might be outdated

### When to Use StackOverflow MCP

**Use StackOverflow MCP when:**

- ✅ Encountering specific error messages
- ✅ Need community-tested solutions
- ✅ Debugging common issues
- ✅ Context7 doesn't have the answer

**StackOverflow MCP Commands:**

- `call-tool(serverName: "stackoverflow", toolName: "search", toolArgs: {query: "FastAPI async dependency injection error"})`

### When to Use Brave Search MCP

**Use Brave Search MCP when:**

- ✅ Researching best practices (security, performance, accessibility)
- ✅ Researching when Context7 and StackOverflow don't cover it
- ✅ Need current industry standards (2025)
- ✅ Researching security vulnerabilities and fixes

**Brave Search MCP Commands:**

- `call-tool(serverName: "brave-search", toolName: "search", toolArgs: {query: "FastAPI performance optimization 2025"})`

### When to Use Sequential Thinking MCP

**Use Sequential Thinking MCP when:**

- ✅ Analyzing complex issues (multiple root causes)
- ✅ Prioritizing fixes (impact analysis)
- ✅ Making architectural decisions
- ✅ Analyzing trade-offs between approaches

### When to Use Memory-Bank MCP

**Use Memory-Bank MCP:**

- ✅ **BEFORE starting**: Retrieve stored patterns and decisions
- `read_global_memory_bank({docs: ".cursor", path: "patterns/*.json"})`
- ✅ **AFTER fixes**: Store fix patterns for future reference
- `write_global_memory_bank({docs: ".cursor", path: "fixes/...", content: "..."})`
- ✅ **AFTER decisions**: Store architectural decisions
- `write_global_memory_bank({docs: ".cursor", path: "decisions/...", content: "..."})`
- ✅ **AFTER testing**: Store test results and metrics
- `write_global_memory_bank({docs: ".cursor", path: "test-results/...", content: "..."})`

### When to Use Filesystem MCP

**Use Filesystem MCP when:**

- ✅ Reading configuration files
- ✅ Reading test files
- ✅ Reading documentation
- ✅ Bulk file operations needed
- ✅ Writing documentation files

### When to Use Redis MCP

**Use Redis MCP when:**

- ✅ Testing Redis connectivity
- ✅ Debugging cache issues
- ✅ Verifying cache operations
- ✅ Checking cache keys and values

### When to Use ArXiv MCP

**Use ArXiv MCP when:**

- ✅ Implementing ML features
- ✅ Researching trading algorithms
- ✅ Need academic approaches to problems

### When to Use GitHub MCP

**Use GitHub MCP when:**

- ✅ Need to understand git history
- ✅ Creating branches for fixes
- ✅ Reviewing PRs/issues
- ✅ Committing changes

## Cursor Extensions Usage Guide

Cursor Extensions are VS Code extensions that enhance the development experience. Use them alongside MCP tools for comprehensive testing and fixing.

### Code Quality Extensions

#### Error Lens Extension

**When to Use:**

- ✅ **ALWAYS** - Shows errors and warnings inline in the editor
- ✅ **ALWAYS** - Highlights TypeScript errors in real-time
- ✅ **ALWAYS** - Highlights Python linting errors (Flake8)
- ✅ **ALWAYS** - Shows ESLint warnings inline
- ✅ **Use when**: Writing code, fixing errors, reviewing code

**How to Use:**

- Errors appear inline in the editor automatically
- Click on error to see details
- Fix errors as you code

#### GitLens Extension

**When to Use:**

- ✅ **ALWAYS** - View git blame information inline
- ✅ **ALWAYS** - See commit history for lines of code
- ✅ **ALWAYS** - View file history and changes
- ✅ **Use when**: Understanding code changes, debugging issues, reviewing commits
- ✅ **Use when**: Finding when a bug was introduced

**How to Use:**

- Hover over code to see git blame
- Click on line numbers to see commit details
- Use GitLens sidebar for file history

#### Code Metrics Extension

**When to Use:**

- ✅ **Use when**: Analyzing code complexity
- ✅ **Use when**: Identifying complex functions that need refactoring
- ✅ **Use when**: Performance optimization (complex code is often slow)
- ✅ **Use when**: Code review (flag complex code)

**How to Use:**

- View complexity metrics in status bar
- Check function complexity scores
- Identify functions exceeding baseline (complexity > 10, length > 50)

### Testing & Coverage Extensions

#### Coverage Gutters Extension

**When to Use:**

- ✅ **ALWAYS** - Visualize test coverage in editor
- ✅ **ALWAYS** - See which lines are covered by tests
- ✅ **ALWAYS** - Identify untested code paths
- ✅ **Use when**: Running tests, verifying coverage ≥85%
- ✅ **Use when**: Finding untested code to add tests

**How to Use:**

- Run tests with coverage: `pytest --cov` or `npm run test:frontend:coverage`
- Coverage appears as colored gutters in editor
- Green = covered, Red = not covered
- Click on gutter to see coverage details

### API Testing Extensions

#### REST Client Extension

**When to Use:**

- ✅ **Use when**: Testing API endpoints manually
- ✅ **Use when**: Debugging API issues
- ✅ **Use when**: Verifying API responses
- ✅ **Use when**: Testing authentication endpoints
- ✅ **Alternative to**: Browser MCP for API testing (use REST Client for quick API tests, Browser MCP for full UI flows)

**How to Use:**

- Create `.http` or `.rest` files with API requests
- Send requests directly from editor
- View responses inline
- Test endpoints: `http://localhost:8000/api/bots`, `http://localhost:8000/api/auth/login`

**Example REST Client File:**

```http
### Login
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "password123"
}

### Get Bots
GET http://localhost:8000/api/bots
Authorization: Bearer {{token}}
```

### Database Extensions

#### PostgreSQL Extension

**When to Use:**

- ✅ **Use when**: Connecting to database directly
- ✅ **Use when**: Running SQL queries for debugging
- ✅ **Use when**: Inspecting database schema
- ✅ **Use when**: Verifying data after operations
- ✅ **Alternative to**: Postgres MCP (use extension for visual SQL editor, MCP for programmatic queries)

**How to Use:**

- Connect to database via extension sidebar
- Run SQL queries in editor
- View query results in table format
- Inspect table schemas visually

### Documentation Extensions

#### Markdown Extension

**When to Use:**

- ✅ **ALWAYS** - Preview markdown files
- ✅ **ALWAYS** - Edit documentation files
- ✅ **Use when**: Updating README, CHANGELOG, documentation
- ✅ **Use when**: Creating test reports

**How to Use:**

- Open markdown file
- Press `Ctrl+Shift+V` (Windows) to preview
- Edit and preview simultaneously

#### Paste Image Extension

**When to Use:**

- ✅ **Use when**: Adding screenshots to documentation
- ✅ **Use when**: Documenting UI issues
- ✅ **Use when**: Creating test reports with images

**How to Use:**

- Copy image to clipboard
- Paste in markdown file (saves to `docs/images/`)
- Image automatically inserted with proper path

#### TODO Tree Extension

**When to Use:**

- ✅ **ALWAYS** - Find all TODO/FIXME comments in codebase
- ✅ **ALWAYS** - Track remaining work
- ✅ **Use when**: Identifying incomplete features
- ✅ **Use when**: Finding code that needs fixing

**How to Use:**

- View TODO Tree in sidebar
- See all TODO/FIXME/NOTE comments
- Click to navigate to code
- Tags: TODO, FIXME, NOTE, HACK, XXX

#### Better Comments Extension

**When to Use:**

- ✅ **ALWAYS** - Highlight important comments
- ✅ **Use when**: Writing code comments
- ✅ **Use when**: Documenting complex logic

**How to Use:**

- Use special comment syntax:
  - `// ! Important`
  - `// ? Question`
  - `// TODO: Fix this`
  - `// * Highlighted`

### Code Formatting Extensions

#### Prettier Extension (TypeScript/React)

**When to Use:**

- ✅ **ALWAYS** - Format TypeScript/React files on save
- ✅ **ALWAYS** - Ensure consistent code style
- ✅ **Use when**: Fixing formatting issues
- ✅ **Use when**: Code review (format before commit)

**How to Use:**

- Format on save (enabled in settings)
- Manual format: `Shift+Alt+F` (Windows)
- Format all files: `npm run format`

#### Black Formatter Extension (Python)

**When to Use:**

- ✅ **ALWAYS** - Format Python files on save
- ✅ **ALWAYS** - Ensure consistent Python style
- ✅ **Use when**: Fixing Python formatting issues

**How to Use:**

- Format on save (enabled in settings)
- Manual format: `Shift+Alt+F` (Windows)
- Format all files: `black server_fastapi/`

### Development Tools Extensions

#### Docker Extension

**When to Use:**

- ✅ **Use when**: Managing Docker containers
- ✅ **Use when**: Building Docker images
- ✅ **Use when**: Debugging container issues
- ✅ **Use when**: Viewing container logs

**How to Use:**

- View containers in Docker sidebar
- Start/stop containers
- View logs
- Build images

#### Live Server Extension

**When to Use:**

- ✅ **Use when**: Quick HTML/static file testing
- ✅ **Use when**: Testing frontend without full dev server
- ✅ **Alternative to**: Full Vite dev server (use Live Server for quick tests)

**How to Use:**

- Right-click HTML file → "Open with Live Server"
- Auto-reloads on file changes

### Productivity Extensions

#### Path Intellisense Extension

**When to Use:**

- ✅ **ALWAYS** - Autocomplete file paths in imports
- ✅ **ALWAYS** - Faster imports with path aliases (`@/*`, `@shared/*`)
- ✅ **Use when**: Writing imports, refactoring file paths

**How to Use:**

- Type import path, extension suggests files
- Supports path aliases configured in `tsconfig.json`

#### WakaTime Extension

**When to Use:**

- ✅ **Optional** - Track coding time
- ✅ **Use when**: Monitoring development time
- ✅ **Note**: Requires WakaTime API key

#### Pomodoro Extension

**When to Use:**

- ✅ **Optional** - Time management during long sessions
- ✅ **Use when**: Long testing/fixing sessions
- ✅ **Use when**: Need breaks during work

### AI Assistant Extensions

#### CodeGPT Extension

**When to Use:**

- ✅ **Optional** - Additional AI assistance
- ✅ **Use when**: Need alternative AI suggestions
- ✅ **Note**: Requires API key

#### CodeGeeX Extension

**When to Use:**

- ✅ **Optional** - AI code completion
- ✅ **Use when**: Writing code, generating boilerplate
- ✅ **Use when**: Code suggestions and completions

**Features:**

- Sidebar chat UI
- Comment generation
- Commit message generation
- Code completion

### Language-Specific Extensions

#### Python Extension

**When to Use:**

- ✅ **ALWAYS** - Python language support
- ✅ **ALWAYS** - Type checking (mypy strict mode)
- ✅ **ALWAYS** - Linting (Flake8)
- ✅ **ALWAYS** - Testing (pytest)
- ✅ **ALWAYS** - Formatting (Black)

**How to Use:**

- Errors shown inline (Error Lens)
- Run tests: Right-click test file → "Run Python Tests"
- Format: `Shift+Alt+F`
- Lint: Errors shown automatically

#### TypeScript/React Extensions (Built-in)

**When to Use:**

- ✅ **ALWAYS** - TypeScript language support
- ✅ **ALWAYS** - React support
- ✅ **ALWAYS** - Auto-imports
- ✅ **ALWAYS** - Type checking

**How to Use:**

- Errors shown inline (Error Lens)
- Auto-imports on typing
- Go to definition: `F12`
- Find references: `Shift+F12`

#### React Native Extension

**When to Use:**

- ✅ **Use when**: Working on mobile app
- ✅ **Use when**: Testing React Native code
- ✅ **Use when**: Mobile development

### Extension Usage Workflow

**For Code Quality:**

1. **Error Lens** - See errors inline while coding
2. **GitLens** - Understand code history
3. **Code Metrics** - Check complexity
4. **Coverage Gutters** - Verify test coverage

**For Testing:**

1. **REST Client** - Test API endpoints quickly
2. **Coverage Gutters** - Visualize coverage
3. **PostgreSQL** - Inspect database
4. **Browser MCP** - Full UI testing (primary)

**For Debugging:**

1. **Error Lens** - Find errors quickly
2. **GitLens** - Find when bug introduced
3. **REST Client** - Test API endpoints
4. **PostgreSQL** - Check database state
5. **Browser MCP** - Reproduce UI issues

**For Documentation:**

1. **Markdown** - Preview documentation
2. **Paste Image** - Add screenshots
3. **TODO Tree** - Track remaining work
4. **Better Comments** - Highlight important comments

**For Code Formatting:**

1. **Prettier** - Format TypeScript/React (auto on save)
2. **Black** - Format Python (auto on save)
3. **Manual format**: `Shift+Alt+F`

### Extension + MCP Tool Combinations

**Best Combinations:**

1. **Error Lens + Context7 MCP**: See error → Research solution
2. **REST Client + Browser MCP**: Quick API test → Full UI test
3. **PostgreSQL Extension + Postgres MCP**: Visual SQL → Programmatic queries
4. **Coverage Gutters + Browser MCP**: See coverage → Test manually
5. **GitLens + GitHub MCP**: View history → Create branches/PRs
6. **TODO Tree + Memory-Bank MCP**: Find TODOs → Store fix patterns
7. **Error Lens + StackOverflow MCP**: See error → Search solution
8. **Code Metrics + Context7 MCP**: Find complex code → Research refactoring

### Extension Configuration

**Key Settings (from `.vscode/settings.json`):**

- **Error Lens**: Enabled for errors and warnings
- **GitLens**: Code lens and current line enabled
- **Python**: Black formatter, Flake8 linting, pytest testing, strict type checking
- **Prettier**: Default formatter for TypeScript/React
- **REST Client**: 10s timeout, JSON default headers
- **Coverage Gutters**: Shows coverage from `coverage/lcov.info` and `coverage/coverage.xml`
- **TODO Tree**: Tracks TODO, FIXME, NOTE, HACK, XXX tags
- **Auto Save**: Enabled with 1s delay
- **Format on Save**: Enabled for all languages

## Feature-by-Feature Complete Testing Workflow

For each feature, follow this complete workflow:

### Step 1: Intelligence System (AUTOMATIC - MANDATORY)

1. ✅ **AUTOMATICALLY** Read `.cursor/extracted-patterns.md` - Find matching patterns
2. ✅ **AUTOMATICALLY** Read `.cursor/knowledge-base.md` - Check for existing solutions
3. ✅ **AUTOMATICALLY** Read `.cursor/quick-reference.md` - Fast lookup
4. ✅ **AUTOMATICALLY** Use Memory-Bank MCP: `read_global_memory_bank({docs: ".cursor"})` - Retrieve stored patterns
5. ✅ **AUTOMATICALLY** Check `.cursor/decisions.md` - Review similar decisions
6. ✅ **AUTOMATICALLY** Check `.cursor/predictive-suggestions.md` - Get proactive suggestions

### Step 2: Research (if needed)

- **Use Context7 MCP** for library patterns
- **Use StackOverflow MCP** for error solutions
- **Use Brave Search MCP** for best practices
- **Use Sequential Thinking MCP** for complex analysis

### Step 3: Test with Browser MCP (PRIMARY)

- Navigate to feature page: `browser_navigate(url: "http://localhost:5173/feature")`
- Take snapshot: `browser_snapshot()` to get page structure
- Test interactions: `browser_click()`, `browser_type()`, `browser_select_option()`
- Take screenshots: `browser_take_screenshot(filename: "feature-test.png")`
- Check console: `browser_console_messages()` for errors
- Check network: `browser_network_requests()` for API calls
- Verify functionality visually

### Step 4: Verify with Crypto MCPs (if applicable)

- **CoinGecko MCP**: Verify price data accuracy
- **Web3 MCP**: Verify blockchain operations (balances, transactions)
- **DeFi Trading MCP**: Verify trading operations and portfolio data

### Step 5: Verify with Database MCP

- **Postgres/SQLite MCP**: Verify data operations, check data integrity
- Run queries to verify data was saved correctly

### Step 6: Fix Issues

- Match extracted patterns from `.cursor/extracted-patterns.md`
- Apply fixes following project patterns
- Test again with Browser MCP to verify fixes work

### Step 7: Store Results

- Use Memory-Bank MCP to store fix patterns
- Update documentation with Filesystem MCP
- Store test results and metrics

## Complete Feature Testing Examples

### Example 1: Testing Bot Creation Feature

**Step 1: Intelligence System (AUTOMATIC)**

- Read `.cursor/extracted-patterns.md` - Find Bot Creation patterns
- Read `.cursor/knowledge-base.md` - Check bot creation solutions
- Use Memory-Bank MCP to retrieve stored bot patterns

**Step 2: Research (if needed)**

- Use Context7 MCP: "React form validation patterns", "FastAPI bot creation endpoints"

**Step 3: Test with Browser MCP**

- Navigate: `browser_navigate(url: "http://localhost:5173/bots")`
- Snapshot: `browser_snapshot()` to get page structure
- Click create button: `browser_click(element: "Create Bot button", ref: "...")`
- Fill form: `browser_type(element: "Bot name input", ref: "...", text: "Test Bot")`
- Submit: `browser_click(element: "Submit button", ref: "...")`
- Screenshot: `browser_take_screenshot(filename: "bot-creation.png")`
- Verify: Check bot appears in list

**Step 4: Verify with Crypto MCPs**

- CoinGecko MCP: Verify price data used in bot creation is accurate
- Not needed: Web3 MCP, DeFi Trading MCP (bot creation doesn't use blockchain)

**Step 5: Verify with Database MCP**

- Postgres MCP: `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "SELECT * FROM bots WHERE name = 'Test Bot'"})`
- Verify bot data saved correctly

**Step 6: Fix Issues (if any)**

- Match FastAPI Route Pattern and React Query Hook Pattern
- Apply fixes
- Test again with Browser MCP

**Step 7: Store Results**

- Memory-Bank MCP: Store bot creation fix patterns

### Example 2: Testing DEX Swap Feature

**Step 1: Intelligence System (AUTOMATIC)**

- Read `.cursor/extracted-patterns.md` - Find DEX trading patterns
- Use Memory-Bank MCP to retrieve stored DEX patterns

**Step 2: Research (if needed)**

- Use Context7 MCP: "DEX aggregator integration", "Price impact calculation"
- Use Brave Search MCP: "DEX swap best practices 2025"

**Step 3: Test with Browser MCP**

- Navigate: `browser_navigate(url: "http://localhost:5173/dex-trading")`
- Snapshot: `browser_snapshot()` to get swap UI structure
- Select tokens: `browser_select_option(element: "Token in", ref: "...", values: ["USDC"])`
- Enter amount: `browser_type(element: "Amount input", ref: "...", text: "100")`
- Get quote: Click "Get Quote" button
- Verify price impact warning (if >1%)
- Execute swap: `browser_click(element: "Swap button", ref: "...")`
- Screenshot: `browser_take_screenshot(filename: "dex-swap.png")`
- Monitor transaction: Check transaction status updates

**Step 4: Verify with Crypto MCPs**

- CoinGecko MCP: Verify token prices for swap calculation
- Web3 MCP: Verify swap transaction on blockchain: `call-tool(serverName: "web3", toolName: "get_transaction", toolArgs: {tx_hash: "...", chain: "ethereum"})`
- DeFi Trading MCP: Verify swap execution and liquidity

**Step 5: Verify with Database MCP**

- Postgres MCP: Verify swap data saved in database

**Step 6: Fix Issues (if any)**

- Match DEX trading patterns
- Apply fixes
- Test again with Browser MCP

**Step 7: Store Results**

- Memory-Bank MCP: Store DEX swap fix patterns

## Complete Testing Checklist with MCP Tools

### Authentication Feature

- [ ] **Browser MCP**: Navigate to login page, test sign in flow
- [ ] **Browser MCP**: Test sign up flow, verify form validation
- [ ] **Browser MCP**: Test sign out, verify token cleared
- [ ] **Browser MCP**: Test protected routes, verify redirect
- [ ] **Postgres MCP**: Verify user data in database after signup
- [ ] **Browser MCP**: Take screenshots of all auth flows
- [ ] **Context7 MCP**: Research JWT authentication patterns if issues found

### Bot Management Feature

- [ ] **Browser MCP**: Test bot creation form, submit, verify
- [ ] **Browser MCP**: Test bot list, verify bots display
- [ ] **Browser MCP**: Test bot start/stop, verify status updates
- [ ] **Browser MCP**: Test bot delete, verify removal
- [ ] **CoinGecko MCP**: Verify price data used in bot creation
- [ ] **Postgres MCP**: Verify bot data in database
- [ ] **Browser MCP**: Take screenshots of bot management flows

### Trading Operations Feature

- [ ] **Browser MCP**: Test paper trading mode, execute trade
- [ ] **Browser MCP**: Test real trading mode, execute trade
- [ ] **Browser MCP**: Test trading mode switching, verify persistence
- [ ] **CoinGecko MCP**: Verify market data accuracy
- [ ] **Postgres MCP**: Verify trade data in database
- [ ] **Browser MCP**: Take screenshots of trading flows

### Wallet Management Feature

- [ ] **Browser MCP**: Test wallet creation, verify address
- [ ] **Browser MCP**: Test balance display, verify shows correctly
- [ ] **Browser MCP**: Test deposit flow, generate QR code
- [ ] **Browser MCP**: Test withdrawal flow, verify 2FA
- [ ] **Web3 MCP**: Verify wallet balances match blockchain
- [ ] **Web3 MCP**: Verify deposit/withdrawal transactions on blockchain
- [ ] **Postgres MCP**: Verify wallet data in database
- [ ] **Browser MCP**: Take screenshots of wallet flows

### DEX Trading Feature

- [ ] **Browser MCP**: Test DEX swap UI, select tokens, enter amount
- [ ] **Browser MCP**: Test quote retrieval, verify price impact
- [ ] **Browser MCP**: Test price impact warning (if >1%)
- [ ] **Browser MCP**: Test swap execution, verify transaction
- [ ] **CoinGecko MCP**: Verify token prices for swap
- [ ] **Web3 MCP**: Verify swap transaction on blockchain
- [ ] **DeFi Trading MCP**: Verify swap execution and liquidity
- [ ] **Postgres MCP**: Verify swap data in database
- [ ] **Browser MCP**: Take screenshots of DEX swap flows

### Portfolio & Analytics Feature

- [ ] **Browser MCP**: Test portfolio display, verify balances
- [ ] **Browser MCP**: Test performance charts, verify render
- [ ] **Browser MCP**: Test analytics dashboard, verify metrics
- [ ] **CoinGecko MCP**: Verify portfolio valuation uses accurate prices
- [ ] **DeFi Trading MCP**: Verify portfolio analysis data
- [ ] **Postgres MCP**: Verify portfolio data in database

### WebSocket Real-Time Updates

- [ ] **Browser MCP**: Test WebSocket connection, verify established
- [ ] **Browser MCP**: Test price updates, verify real-time
- [ ] **Browser MCP**: Test balance updates, verify real-time
- [ ] **Browser MCP**: Test trade updates, verify real-time
- [ ] **Browser DevTools**: Monitor WebSocket messages in Network tab
- [ ] **Context7 MCP**: Research WebSocket patterns if issues found

## Research Workflow for Issues

When encountering an issue, follow this research workflow:

1. **Check Intelligence System FIRST** (AUTOMATIC):

- Read `.cursor/extracted-patterns.md`
- Read `.cursor/knowledge-base.md`
- Use Memory-Bank MCP to retrieve stored solutions

2. **Search Codebase**:

- Use `codebase_search` to find similar implementations
- Use `grep` to find specific patterns

3. **Research with MCPs** (in order):

- **Context7 MCP**: Library-specific patterns and documentation
- **StackOverflow MCP**: Error message solutions
- **Brave Search MCP**: Best practices and current standards
- **Sequential Thinking MCP**: Complex analysis

4. **Test with Browser MCP**:

- Reproduce issue in browser
- Take screenshots
- Check console and network

5. **Verify with Database/Crypto MCPs**:

- Postgres MCP for data issues
- Web3 MCP for blockchain issues
- CoinGecko MCP for price issues

6. **Fix and Verify**:

- Apply fix matching extracted patterns
- Test again with Browser MCP
- Store fix pattern in Memory-Bank MCP
- **Test Every Feature** - Use Browser MCP + Crypto MCPs + Database MCPs for comprehensive testing

## Complete Execution Checklist

This checklist tells you exactly what to do at each step, including which tools to use.

### Phase 1: Environment Setup

**Step 1.1: Verify Python Installation**

- [ ] **Terminal**: Run `python --version` (should be 3.12+)
- [ ] **Filesystem MCP**: Check Python installation paths if needed
- [ ] **If issues**: Use Context7 MCP to research Python installation

**Step 1.2: Verify Node.js Installation**

- [ ] **Terminal**: Run `node --version` (should be 18+)
- [ ] **Terminal**: Run `npm --version`

**Step 1.3: Verify Database/Redis**

- [ ] **Postgres MCP**: Test connection: `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "SELECT 1"})`
- [ ] **Redis MCP**: Test connection: `call-tool(serverName: "redis", toolName: "get", toolArgs: {key: "test"})`
- [ ] **If unavailable**: Continue with SQLite (development mode)

**Step 1.4: Verify Environment Variables**

- [ ] **Filesystem MCP**: Read `.env.example` file
- [ ] **Filesystem MCP**: Check if `.env` file exists
- [ ] **If missing**: Create `.env` from `.env.example`
- [ ] **Context7 MCP**: Research environment variable best practices if needed

**Step 1.5: Install Dependencies**

- [ ] **Terminal**: Run `npm install --legacy-peer-deps`
- [ ] **Terminal**: Run `pip install -r requirements.txt`
- [ ] **If errors**: Use StackOverflow MCP to search for error solutions

**Step 1.6: Verify Ports**

- [ ] **Terminal**: Check port 8000 (backend) - `netstat -ano | findstr :8000` (Windows)
- [ ] **Terminal**: Check port 5173 (frontend) - `netstat -ano | findstr :5173` (Windows)
- [ ] **If ports in use**: Stop conflicting services or change ports

**Step 1.7: TypeScript Check**

- [ ] **Error Lens Extension**: Check for TypeScript errors inline in editor
- [ ] **Terminal**: Run `npm run check` (PowerShell: use `;` instead of `&&`)
- [ ] **If errors**: Use Error Lens to see errors inline, click to navigate
- [ ] **If errors**: Use Context7 MCP to research TypeScript errors
- [ ] **If errors**: Use StackOverflow MCP to search for specific errors
- [ ] **Fix all errors** before proceeding

**Step 1.8: Linting Check**

- [ ] **Error Lens Extension**: Check for ESLint/Flake8 errors inline in editor
- [ ] **Terminal**: Run `npm run lint`
- [ ] **Terminal**: Run `flake8 server_fastapi/` for Python linting
- [ ] **If errors**: Use Error Lens to see errors inline, click to navigate
- [ ] **If errors**: Use Context7 MCP to research ESLint/Flake8 rules
- [ ] **Fix all errors** before proceeding

**Step 1.9: Build Verification**

- [ ] **Terminal**: Run `npm run build`
- [ ] **If build fails**: Use Context7 MCP to research Vite build issues
- [ ] **If build fails**: Use StackOverflow MCP to search for build errors

### Phase 2: Run All Tests

**Step 2.1: Start All Services**

- [ ] **Terminal**: Run `npm run start:all`
- [ ] **Wait**: Wait for services to start (check terminal output)
- [ ] **Browser MCP**: Navigate to `http://localhost:8000/health` - Verify backend health
- [ ] **Browser MCP**: Navigate to `http://localhost:5173` - Verify frontend loads
- [ ] **Browser MCP**: Take screenshots: `browser_take_screenshot(filename: "services-started.png")`
- [ ] **Postgres MCP**: Verify database connection works
- [ ] **Redis MCP**: Verify Redis connection works (if available)

**Step 2.2: Run E2E Tests**

- [ ] **Terminal**: Run `npm run test:e2e:complete`
- [ ] **Monitor**: Watch for test failures
- [ ] **Filesystem MCP**: Read test result files in `test-results/`
- [ ] **Browser MCP**: Open HTML report: `browser_navigate(url: "file:///path/to/test-results/combined-report.html")`
- [ ] **For each failing test**: Use Browser MCP to manually test the flow
- [ ] **Store failures**: Use Memory-Bank MCP to store failure patterns

**Step 2.3: Run Backend Tests**

- [ ] **Terminal**: Run `pytest server_fastapi/tests/ -v --cov=server_fastapi`
- [ ] **Check coverage**: Verify ≥85% coverage
- [ ] **If tests fail**: Use Context7 MCP to research pytest patterns
- [ ] **If database errors**: Use Postgres MCP to inspect test database
- [ ] **For wallet tests**: Use Web3 MCP to verify blockchain operations
- [ ] **For trading tests**: Use CoinGecko MCP to verify price data
- [ ] **Store results**: Use Memory-Bank MCP to store test results

**Step 2.4: Run Frontend Tests**

- [ ] **Terminal**: Run `npm run test:frontend`
- [ ] **Coverage Gutters Extension**: View coverage in editor (green = covered, red = not covered)
- [ ] **Check coverage**: Verify ≥85% coverage target
- [ ] **Coverage Gutters**: Click on red lines to see untested components
- [ ] **If tests fail**: Use Error Lens to see test errors inline
- [ ] **If tests fail**: Use Context7 MCP to research Vitest/React Testing Library
- [ ] **If component tests fail**: Use Browser MCP to manually test components
- [ ] **Store results**: Use Memory-Bank MCP to store test results

### Phase 3: Analyze Results

**Step 3.1: Collect All Failures**

- [ ] **Error Lens Extension**: Review all errors shown inline in editor
- [ ] **TODO Tree Extension**: Check for FIXME/TODO comments that indicate known issues
- [ ] **Filesystem MCP**: Read all test result files
- [ ] **Browser MCP**: Open and analyze HTML test reports
- [ ] **Coverage Gutters Extension**: Identify untested code paths (red lines)
- [ ] **Memory-Bank MCP**: Store failure patterns: `write_global_memory_bank({docs: ".cursor", path: "issues/test-failures.json", content: "..."})`

**Step 3.2: Categorize Failures**

- [ ] **Sequential Thinking MCP**: Analyze and categorize failures by type
- [ ] **Group by**: Authentication, API, UI, Database, Performance, Security

**Step 3.3: Research Solutions**

- [ ] **For each failure**: Use StackOverflow MCP to search for error message
- [ ] **For library issues**: Use Context7 MCP to research patterns
- [ ] **For best practices**: Use Brave Search MCP to research solutions
- [ ] **For complex issues**: Use Sequential Thinking MCP to analyze

**Step 3.4: Prioritize Fixes**

- [ ] **Sequential Thinking MCP**: Analyze impact and prioritize
- [ ] **Priority order**: Critical → High → Medium → Low

### Phase 4: Fix Issues

**For each issue, follow this workflow:**

**Step 4.1: Research Solution**

- [ ] **Error Lens Extension**: Click on error to see details and navigate to code
- [ ] **GitLens Extension**: Check git history to see when error was introduced
- [ ] **Intelligence System**: Check `.cursor/extracted-patterns.md` for matching patterns
- [ ] **Memory-Bank MCP**: Retrieve stored fix patterns
- [ ] **Context7 MCP**: Research library-specific solutions
- [ ] **StackOverflow MCP**: Search for error solutions
- [ ] **Brave Search MCP**: Research best practices
- [ ] **Code Metrics Extension**: Check code complexity if refactoring needed

**Step 4.2: Apply Fix**

- [ ] **Match patterns**: Use patterns from `.cursor/extracted-patterns.md`
- [ ] **Apply fix**: Make code changes following project patterns
- [ ] **Files to modify**: Check plan for specific files

**Step 4.3: Test Fix**

- [ ] **Error Lens Extension**: Verify error is gone (no red underline)
- [ ] **REST Client Extension**: Test API endpoints quickly (if API fix)
- [ ] **Browser MCP**: Manually test the fix (navigate, interact, verify)
- [ ] **Browser MCP**: Take screenshot of fix working
- [ ] **PostgreSQL Extension or Postgres MCP**: Verify data operations (if applicable)
- [ ] **Web3 MCP**: Verify blockchain operations (if applicable)
- [ ] **CoinGecko MCP**: Verify price data (if applicable)
- [ ] **Coverage Gutters Extension**: Verify fix is covered by tests (green line)

**Step 4.4: Verify Fix**

- [ ] **Terminal**: Run relevant tests
- [ ] **Browser MCP**: Verify fix works visually
- [ ] **If still broken**: Repeat research and fix process

**Step 4.5: Store Fix Pattern**

- [ ] **Memory-Bank MCP**: Store fix pattern: `write_global_memory_bank({docs: ".cursor", path: "fixes/...", content: "..."})`

### Phase 5: Verify All Fixes

**Step 5.1: Re-run All Tests**

- [ ] **Terminal**: Run `npm run test:e2e:complete`
- [ ] **Terminal**: Run `pytest server_fastapi/tests/ -v`
- [ ] **Terminal**: Run `npm run test:frontend`
- [ ] **Verify**: All tests should pass

**Step 5.2: Manual Testing (Feature-by-Feature)**

- [ ] **REST Client Extension**: Quick API tests for each feature (optional, faster than Browser MCP)
- [ ] **Authentication**: Browser MCP test all auth flows + REST Client test API
- [ ] **Bot Management**: Browser MCP test all bot operations + REST Client test API
- [ ] **Trading**: Browser MCP test trading + CoinGecko MCP verify prices + REST Client test API
- [ ] **Wallet**: Browser MCP test wallet + Web3 MCP verify blockchain + REST Client test API
- [ ] **DEX Swaps**: Browser MCP test swaps + CoinGecko/Web3/DeFi Trading MCPs verify + REST Client test API
- [ ] **Portfolio**: Browser MCP test portfolio + CoinGecko/DeFi Trading MCPs verify + REST Client test API
- [ ] **WebSocket**: Browser MCP test real-time updates
- [ ] **Take screenshots**: Browser MCP screenshot all features
- [ ] **Paste Image Extension**: Add screenshots to documentation

**Step 5.3: Performance Validation**

- [ ] **Terminal**: Run `npm run load:test:comprehensive`
- [ ] **REST Client Extension**: Test API endpoints and measure response times
- [ ] **Browser MCP**: Measure API response times (Network tab)
- [ ] **PostgreSQL Extension or Postgres MCP**: Analyze slow queries (EXPLAIN ANALYZE)
- [ ] **Code Metrics Extension**: Check code complexity (complex code is often slow)
- [ ] **Compare**: Before/after metrics
- [ ] **Memory-Bank MCP**: Store performance metrics

**Step 5.4: Security Validation**

- [ ] **Terminal**: Run `npm run audit:security`
- [ ] **Browser MCP**: Test authentication, authorization, rate limiting
- [ ] **Brave Search MCP**: Research security fixes if vulnerabilities found
- [ ] **Verify**: All security checks pass

### Phase 6: Documentation

**Step 6.1: Create Test Report**

- [ ] **Filesystem MCP**: Read all test result files
- [ ] **Browser MCP**: Capture screenshots of test results
- [ ] **Paste Image Extension**: Add screenshots to markdown report
- [ ] **Markdown Extension**: Preview test report markdown
- [ ] **Coverage Gutters Extension**: Include coverage screenshots
- [ ] **Memory-Bank MCP**: Store test results: `write_global_memory_bank({docs: ".cursor", path: "test-results/final-report.json", content: "..."})`
- [ ] **Filesystem MCP**: Write comprehensive test report document

**Step 6.2: Update Documentation**

- [ ] **Markdown Extension**: Preview documentation while editing
- [ ] **TODO Tree Extension**: Update TODO.md, mark completed items
- [ ] **Paste Image Extension**: Add screenshots to documentation
- [ ] **Filesystem MCP**: Read and update README.md
- [ ] **Filesystem MCP**: Read and update CHANGELOG.md
- [ ] **Filesystem MCP**: Read and update TODO.md
- [ ] **GitLens Extension**: Review commit history for changelog
- [ ] **Memory-Bank MCP**: Store completion summary

## Quick Reference: Tool Selection by Task

| Task | Primary Tool | Secondary Tools | Research Tools |

|------|-------------|----------------|---------------|

| Test UI Feature | Browser MCP | - | Context7 MCP |

| Verify Price Data | CoinGecko MCP | Browser MCP | - |

| Verify Blockchain | Web3 MCP | Browser MCP | Context7 MCP |

| Verify Database | Postgres MCP | - | Context7 MCP |

| Research Error | StackOverflow MCP | Context7 MCP | Brave Search MCP |

| Research Pattern | Context7 MCP | - | Brave Search MCP |

| Research Best Practice | Brave Search MCP | Context7 MCP | - |

| Complex Analysis | Sequential Thinking MCP | - | - |

| Store Knowledge | Memory-Bank MCP | - | - |

| Read Files | Filesystem MCP | - | - |

| Test Trading | Browser MCP + CoinGecko MCP | DeFi Trading MCP | Context7 MCP |

| Test Wallet | Browser MCP + Web3 MCP | Postgres MCP | Context7 MCP |

| Test DEX Swap | Browser MCP + CoinGecko MCP + Web3 MCP | DeFi Trading MCP + Postgres MCP | Context7 MCP + Brave Search MCP |

| Find Errors | Error Lens Extension | - | Context7 MCP + StackOverflow MCP |

| Test API | REST Client Extension | Browser MCP | Context7 MCP |

| Check Coverage | Coverage Gutters Extension | Terminal (coverage report) | - |

| Inspect Database | PostgreSQL Extension | Postgres MCP | - |

| View Git History | GitLens Extension | GitHub MCP | - |

| Format Code | Prettier/Black Extensions | Terminal (format commands) | - |

| Find TODOs | TODO Tree Extension | - | - |

## Extension + MCP Tool Workflow Examples

### Example: Fixing a TypeScript Error

1. **Error Lens Extension**: See error inline in editor (red underline)
2. **Click error**: Navigate to error location
3. **GitLens Extension**: Check git history to see when error introduced
4. **Context7 MCP**: Research TypeScript error solution
5. **StackOverflow MCP**: Search for specific error message
6. **Apply fix**: Match extracted patterns from `.cursor/extracted-patterns.md`
7. **Error Lens Extension**: Verify error is gone (no red underline)
8. **Prettier Extension**: Auto-format on save
9. **Terminal**: Run `npm run check` to verify
10. **Coverage Gutters Extension**: Verify fix is covered by tests (green line)
11. **Memory-Bank MCP**: Store fix pattern

### Example: Testing API Endpoint

1. **REST Client Extension**: Create `.http` file with API request
2. **Send request**: Test endpoint quickly
3. **View response**: Check response in editor
4. **If issues**: Use Browser MCP for full UI flow testing
5. **If database issues**: Use PostgreSQL Extension to inspect database
6. **If blockchain issues**: Use Web3 MCP to verify blockchain state
7. **Store results**: Use Memory-Bank MCP to store test results

### Example: Finding and Fixing Untested Code

1. **Coverage Gutters Extension**: See red lines (untested code)
2. **Click red line**: See coverage details
3. **Write test**: Add test for untested code
4. **Run tests**: Terminal `pytest` or `npm run test:frontend`
5. **Coverage Gutters Extension**: Verify line turns green (covered)
6. **Verify coverage**: Check ≥85% coverage target

### Example: Debugging Database Issue

1. **Error Lens Extension**: See database error in code
2. **PostgreSQL Extension**: Connect to database, run query
3. **Postgres MCP**: Run EXPLAIN ANALYZE for slow queries
4. **GitLens Extension**: Check when database code was changed
5. **Apply fix**: Fix database query or connection
6. **PostgreSQL Extension**: Verify fix works
7. **Postgres MCP**: Verify with programmatic query
8. **Store fix**: Use Memory-Bank MCP to store fix pattern

### Example: Testing API Endpoint

1. **REST Client Extension**: Create `.http` file with API request
2. **Send request**: Test endpoint quickly
3. **View response**: Check response in editor
4. **If issues**: Use Browser MCP for full UI flow testing
5. **If database issues**: Use PostgreSQL Extension to inspect database
6. **If blockchain issues**: Use Web3 MCP to verify blockchain state
7. **Store results**: Use Memory-Bank MCP to store test results

### Example: Finding and Fixing Untested Code

1. **Coverage Gutters Extension**: See red lines (untested code)
2. **Click red line**: See coverage details
3. **Write test**: Add test for untested code
4. **Run tests**: Terminal `pytest` or `npm run test:frontend`
5. **Coverage Gutters Extension**: Verify line turns green (covered)
6. **Verify coverage**: Check ≥85% coverage target

### Example: Debugging Database Issue

1. **Error Lens Extension**: See database error in code
2. **PostgreSQL Extension**: Connect to database, run query
3. **Postgres MCP**: Run EXPLAIN ANALYZE for slow queries
4. **GitLens Extension**: Check when database code was changed
5. **Apply fix**: Fix database query or connection
6. **PostgreSQL Extension**: Verify fix works
7. **Postgres MCP**: Verify with programmatic query
8. **Store fix**: Use Memory-Bank MCP to store fix pattern

## Final Reminders

- **Browser MCP is PRIMARY** - Use for ALL manual testing and verification
- **Error Lens Extension is PRIMARY** - See all errors inline while coding
- **Coverage Gutters Extension is PRIMARY** - Visualize test coverage
- **Intelligence System FIRST** - Always check extracted patterns before implementing
- **Test Incrementally** - Don't wait, test after each fix
- **Store Everything** - Use Memory-Bank MCP to store all patterns and decisions
- **Research When Needed** - Use Context7, StackOverflow, Brave Search for solutions
- **Verify with MCPs** - Use Crypto MCPs and Database MCPs to verify operations
- **Use Extensions for Quick Tasks** - REST Client for API, PostgreSQL Extension for DB, Error Lens for errors
- **Use MCPs for Programmatic Tasks** - Postgres MCP for queries, Browser MCP for UI, Web3 MCP for blockchain
- **Combine Extensions + MCPs** - Use extensions for visual/quick tasks, MCPs for programmatic/automated tasks
- **Match Patterns** - Always match extracted patterns from codebase
- **Document Everything** - Update README, CHANGELOG, TODO.md with Markdown Extension
- **Format Automatically** - Prettier/Black extensions format on save
- **Track Work** - TODO Tree extension to find remaining work

## Feature-by-Feature Complete Testing Workflow

For each feature, follow this complete workflow:

### Step 1: Intelligence System (AUTOMATIC - MANDATORY)

1. ✅ **AUTOMATICALLY** Read `.cursor/extracted-patterns.md` - Find matching patterns
2. ✅ **AUTOMATICALLY** Read `.cursor/knowledge-base.md` - Check for existing solutions
3. ✅ **AUTOMATICALLY** Read `.cursor/quick-reference.md` - Fast lookup
4. ✅ **AUTOMATICALLY** Use Memory-Bank MCP: `read_global_memory_bank({docs: ".cursor"})` - Retrieve stored patterns
5. ✅ **AUTOMATICALLY** Check `.cursor/decisions.md` - Review similar decisions
6. ✅ **AUTOMATICALLY** Check `.cursor/predictive-suggestions.md` - Get proactive suggestions

### Step 2: Research (if needed)

- **Use Context7 MCP** for library patterns
- **Use StackOverflow MCP** for error solutions
- **Use Brave Search MCP** for best practices
- **Use Sequential Thinking MCP** for complex analysis

### Step 3: Test with Browser MCP (PRIMARY)

- Navigate to feature page: `browser_navigate(url: "http://localhost:5173/feature")`
- Take snapshot: `browser_snapshot()` to get page structure
- Test interactions: `browser_click()`, `browser_type()`, `browser_select_option()`
- Take screenshots: `browser_take_screenshot(filename: "feature-test.png")`
- Check console: `browser_console_messages()` for errors
- Check network: `browser_network_requests()` for API calls
- Verify functionality visually

### Step 4: Verify with Crypto MCPs (if applicable)

- **CoinGecko MCP**: Verify price data accuracy
- **Web3 MCP**: Verify blockchain operations (balances, transactions)
- **DeFi Trading MCP**: Verify trading operations and portfolio data

### Step 5: Verify with Database MCP

- **Postgres/SQLite MCP**: Verify data operations, check data integrity
- Run queries to verify data was saved correctly

### Step 6: Fix Issues

- Match extracted patterns from `.cursor/extracted-patterns.md`
- Apply fixes following project patterns
- Test again with Browser MCP to verify fixes work

### Step 7: Store Results

- Use Memory-Bank MCP to store fix patterns
- Update documentation with Filesystem MCP
- Store test results and metrics

## Complete Feature Testing Examples

### Example 1: Testing Bot Creation Feature

**Step 1: Intelligence System (AUTOMATIC)**

- Read `.cursor/extracted-patterns.md` - Find Bot Creation patterns
- Read `.cursor/knowledge-base.md` - Check bot creation solutions
- Use Memory-Bank MCP to retrieve stored bot patterns

**Step 2: Research (if needed)**

- Use Context7 MCP: "React form validation patterns", "FastAPI bot creation endpoints"

**Step 3: Test with Browser MCP**

- Navigate: `browser_navigate(url: "http://localhost:5173/bots")`
- Snapshot: `browser_snapshot()` to get page structure
- Click create button: `browser_click(element: "Create Bot button", ref: "...")`
- Fill form: `browser_type(element: "Bot name input", ref: "...", text: "Test Bot")`
- Submit: `browser_click(element: "Submit button", ref: "...")`
- Screenshot: `browser_take_screenshot(filename: "bot-creation.png")`
- Verify: Check bot appears in list

**Step 4: Verify with Crypto MCPs**

- CoinGecko MCP: Verify price data used in bot creation is accurate
- Not needed: Web3 MCP, DeFi Trading MCP (bot creation doesn't use blockchain)

**Step 5: Verify with Database MCP**

- Postgres MCP: `call-tool(serverName: "postgres", toolName: "query", toolArgs: {query: "SELECT * FROM bots WHERE name = 'Test Bot'"})`
- Verify bot data saved correctly

**Step 6: Fix Issues (if any)**

- Match FastAPI Route Pattern and React Query Hook Pattern
- Apply fixes
- Test again with Browser MCP

**Step 7: Store Results**

- Memory-Bank MCP: Store bot creation fix patterns

### Example 2: Testing DEX Swap Feature

**Step 1: Intelligence System (AUTOMATIC)**

- Read `.cursor/extracted-patterns.md` - Find DEX trading patterns
- Use Memory-Bank MCP to retrieve stored DEX patterns

**Step 2: Research (if needed)**

- Use Context7 MCP: "DEX aggregator integration", "Price impact calculation"
- Use Brave Search MCP: "DEX swap best practices 2025"

**Step 3: Test with Browser MCP**

- Navigate: `browser_navigate(url: "http://localhost:5173/dex-trading")`
- Snapshot: `browser_snapshot()` to get swap UI structure
- Select tokens: `browser_select_option(element: "Token in", ref: "...", values: ["USDC"])`
- Enter amount: `browser_type(element: "Amount input", ref: "...", text: "100")`
- Get quote: Click "Get Quote" button
- Verify price impact warning (if >1%)
- Execute swap: `browser_click(element: "Swap button", ref: "...")`
- Screenshot: `browser_take_screenshot(filename: "dex-swap.png")`
- Monitor transaction: Check transaction status updates

**Step 4: Verify with Crypto MCPs**

- CoinGecko MCP: Verify token prices for swap calculation
- Web3 MCP: Verify swap transaction on blockchain: `call-tool(serverName: "web3", toolName: "get_transaction", toolArgs: {tx_hash: "...", chain: "ethereum"})`
- DeFi Trading MCP: Verify swap execution and liquidity

**Step 5: Verify with Database MCP**

- Postgres MCP: Verify swap data saved in database

**Step 6: Fix Issues (if any)**

- Match DEX trading patterns
- Apply fixes
- Test again with Browser MCP

**Step 7: Store Results**

- Memory-Bank MCP: Store DEX swap fix patterns

## Research Workflow for Issues

When encountering an issue, follow this research workflow:

1. **Check Intelligence System FIRST** (AUTOMATIC):

- Read `.cursor/extracted-patterns.md`
- Read `.cursor/knowledge-base.md`
- Use Memory-Bank MCP to retrieve stored solutions

2. **Search Codebase**:

- Use `codebase_search` to find similar implementations
- Use `grep` to find specific patterns

3. **Research with MCPs** (in order):

- **Context7 MCP**: Library-specific patterns and documentation
- **StackOverflow MCP**: Error message solutions
- **Brave Search MCP**: Best practices and current standards
- **Sequential Thinking MCP**: Complex analysis

4. **Test with Browser MCP**:

- Reproduce issue in browser
- Take screenshots
- Check console and network

5. **Verify with Database/Crypto MCPs**:

- Postgres MCP for data issues
- Web3 MCP for blockchain issues
- CoinGecko MCP for price issues

6. **Fix and Verify**:

- Apply fix matching extracted patterns
- Test again with Browser MCP
- Store fix pattern in Memory-Bank MCP

## Complete Testing Execution Order

### Phase 1: Environment Setup (30 min)

1. Verify Python/Node.js - Terminal commands
2. Verify database/Redis - Postgres MCP, Redis MCP
3. Verify environment - Filesystem MCP
4. Install dependencies - Terminal commands
5. TypeScript check - Terminal + Context7 MCP if errors
6. Build verification - Terminal + Context7 MCP if errors

### Phase 2: Run All Tests (2-3 hours)

1. Start services - Terminal + Browser MCP to verify
2. Run E2E tests - Terminal + Browser MCP for manual verification
3. Run backend tests - Terminal + Postgres MCP for database verification
4. Run frontend tests - Terminal + Browser MCP for component verification
5. Generate reports - Filesystem MCP + Browser MCP to view

### Phase 3: Analyze Results (1 hour)

1. Collect failures - Filesystem MCP + Browser MCP
2. Categorize - Sequential Thinking MCP
3. Research solutions - Context7 MCP + StackOverflow MCP + Brave Search MCP
4. Prioritize - Sequential Thinking MCP
5. Store patterns - Memory-Bank MCP

### Phase 4: Fix Issues (4-8 hours)

For each issue:

1. Research - Context7 MCP + StackOverflow MCP + Brave Search MCP
2. Match patterns - `.cursor/extracted-patterns.md`
3. Apply fix - Code changes
4. Test - Browser MCP (primary) + Crypto MCPs + Database MCPs
5. Verify - Browser MCP + Postgres MCP
6. Store - Memory-Bank MCP

### Phase 5: Verify Fixes (2-3 hours)

1. Re-run tests - Terminal
2. Manual testing - Browser MCP for all features
3. Performance validation - Browser MCP + Postgres MCP
4. Security validation - Browser MCP + Brave Search MCP

### Phase 6: Documentation (1 hour)

1. Create reports - Filesystem MCP + Browser MCP (screenshots)
2. Update docs - Filesystem MCP
3. Store results - Memory-Bank MCP