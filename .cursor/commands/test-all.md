# Run All Tests

Execute the complete test suite for CryptoOrchestrator.

## Test Execution Order

1. **Backend Tests** (Python/pytest)
   ```bash
   pytest server_fastapi/tests/ -v --cov=server_fastapi --cov-report=html
   ```
   - Runs all backend unit and integration tests
   - Generates coverage report in `htmlcov/`

2. **Frontend Tests** (Vitest)
   ```bash
   npm run test:frontend
   ```
   - Runs all React component and utility tests
   - Uses Vitest test runner

3. **End-to-End Tests** (Playwright)
   ```bash
   npm run test:e2e
   ```
   - Runs complete E2E test suite
   - Tests user journeys across the application

4. **Generate Combined Coverage Report**
   ```bash
   npm run test:coverage
   ```
   - Generates coverage badge and trends
   - Combines backend and frontend coverage

## Quick Test Commands

- **All tests**: `npm run test:all`
- **Backend only**: `pytest server_fastapi/tests/ -v`
- **Frontend only**: `npm run test:frontend`
- **E2E only**: `npm run test:e2e`
- **With UI**: `npm run test:e2e:ui` or `npm run test:frontend:ui`

## Pre-Deployment Tests

For production readiness:
```bash
npm run test:pre-deploy
```

This runs:
- All test suites
- Infrastructure tests
- Security tests
- Load tests

## Test Coverage

View coverage reports:
- **Backend**: Open `htmlcov/index.html` in browser
- **Frontend**: Check console output or coverage directory
- **Combined**: Run `npm run test:coverage:badge` for badge

## Troubleshooting

If tests fail:
1. Ensure all services are running: `npm run start:all`
2. Check database is initialized: `alembic upgrade head`
3. Verify environment variables: `npm run validate:env`
4. Check test logs for specific errors
