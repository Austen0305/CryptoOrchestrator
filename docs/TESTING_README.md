# Testing Infrastructure - Quick Reference

This document provides quick reference for running all testing infrastructure created for the Pre-Deployment Perfection Plan.

## 📁 Testing Files Overview

### Documentation
- `docs/TESTING_GUIDE.md` - Complete testing checklist and guide
- `docs/DEPLOYMENT_SCORECARD.md` - Deployment readiness scorecard template
- `README.md` - This file

### Test Scripts
- `scripts/test_infrastructure.py` - Phase 1: Infrastructure tests
- `scripts/test_security.py` - Phase 2: Security tests
- `scripts/load_test.py` - Phase 10: Load and performance tests
- `scripts/test_pre_deploy.py` - Comprehensive pre-deployment test runner

### E2E Tests
- `tests/e2e/critical-flows.spec.ts` - Critical user flow E2E tests
- Other E2E tests in `tests/e2e/`

## 🚀 Quick Start Commands

### Run All Tests
```bash
# Complete pre-deployment test suite
npm run test:pre-deploy

# Or run the Python orchestrator
python scripts/test_pre_deploy.py
```

### Run Individual Test Phases

#### Phase 1: Infrastructure
```bash
npm run test:phase1
# or
python scripts/test_infrastructure.py
```

#### Phase 2: Security
```bash
npm run test:phase2
# or
python scripts/test_security.py
```

#### Phase 4: Backend Unit Tests
```bash
npm test
# or
pytest server_fastapi/tests/ -v
```

#### Phase 9: E2E Tests
```bash
npm run test:e2e
# or with UI
npm run test:e2e:ui
```

#### Phase 10: Performance/Load Tests
```bash
npm run test:phase10
# or
npm run load:test:comprehensive
# or
python scripts/load_test.py --comprehensive
```

### Individual Test Types

#### Frontend Tests
```bash
npm run test:frontend
npm run test:frontend:coverage
npm run test:frontend:ui
```

#### Backend Tests
```bash
npm test
npm run test:watch
```

#### Security Audit
```bash
npm run audit:security
```

#### Code Quality
```bash
npm run lint:py
npm run format:py
npm run check
```

## 🔧 Test Script Details

### Infrastructure Tests (`test_infrastructure.py`)
Tests:
- Backend health endpoint
- Database connectivity
- Redis connectivity
- API endpoints accessibility
- CORS configuration

**Usage:**
```bash
python scripts/test_infrastructure.py
```

**Output:** Pass/fail results with connectivity status

---

### Security Tests (`test_security.py`)
Tests:
- SQL injection protection
- XSS protection
- Rate limiting
- Security headers (CSP, X-Frame-Options, etc.)
- Password validation
- CORS restrictions

**Usage:**
```bash
python scripts/test_security.py
```

**Output:** Security vulnerability assessment

---

### Load Tests (`load_test.py`)
Tests:
- API endpoint performance
- Concurrent request handling
- Response time percentiles (p50, p95, p99)
- Throughput metrics
- Error rates under load

**Usage:**
```bash
# Single endpoint
python scripts/load_test.py --endpoint /api/health --concurrent 50 --total 500

# Comprehensive test
python scripts/load_test.py --comprehensive
```

**Output:** Performance metrics and JSON report

---

### Pre-Deploy Test Runner (`test_pre_deploy.py`)
Orchestrates all tests:
- Phase 1: Infrastructure
- Phase 2: Security
- Phase 4: Backend
- Phase 9: E2E (requires server)
- Phase 10: Performance (requires server)
- Code Quality checks

**Usage:**
```bash
python scripts/test_pre_deploy.py
```

**Output:** Comprehensive test report with deployment recommendation

---

## 📊 Test Reports

### Automated Reports
Tests automatically generate reports:
- `test_report_YYYYMMDD_HHMMSS.json` - Pre-deployment test results
- `load_test_results_YYYYMMDD_HHMMSS.json` - Load test metrics
- `htmlcov/` - Code coverage HTML report
- `test-results/` - Playwright test results

### Manual Scorecards
Use these templates for manual assessment:
- `docs/DEPLOYMENT_SCORECARD.md` - Complete deployment readiness scorecard
- `docs/TESTING_GUIDE.md` - Detailed testing checklist

## 🎯 Testing Workflow

### Before Making Changes
1. Run baseline tests to understand current state
2. Document any existing failures (not your responsibility to fix)

```bash
python scripts/test_pre_deploy.py > baseline_results.txt
```

### During Development
1. Run relevant test phase frequently
2. Fix issues immediately

```bash
# While working on backend
npm test -- --watch

# While working on security
python scripts/test_security.py
```

### Before Committing
1. Run all tests
2. Ensure no new failures introduced

```bash
npm run test:all
```

### Before Deployment
1. Run comprehensive pre-deployment tests
2. Fill out deployment scorecard
3. Get sign-off from team leads

```bash
python scripts/test_pre_deploy.py
# Review docs/DEPLOYMENT_SCORECARD.md
```

## 🔍 Debugging Failed Tests

### Infrastructure Tests Failing
```bash
# Check backend is running
npm run health:advanced

# Check logs
tail -f logs/app.log

# Test database directly
python scripts/check_db.py
```

### Security Tests Failing
```bash
# Run with verbose output
python scripts/test_security.py 2>&1 | tee security_test.log

# Check security headers
curl -I http://localhost:8000/health
```

### Load Tests Failing
```bash
# Start with small load
python scripts/load_test.py --concurrent 5 --total 50

# Check server resources
top
# or
htop
```

### E2E Tests Failing
```bash
# Run with UI for debugging
npm run test:e2e:ui

# Run specific test
npx playwright test critical-flows.spec.ts --debug

# Check screenshots and videos
ls -la test-results/
```

## 📈 Performance Targets

Based on the testing guide, target metrics:

### API Performance
- p95 response time: < 200ms
- p99 response time: < 500ms
- Throughput: > 100 req/s
- Error rate: < 1%

### Frontend Performance
- Initial load: < 3 seconds
- Time to interactive: < 5 seconds
- First contentful paint: < 1.5 seconds
- Lighthouse score: > 90

### Load Handling
- Concurrent users: 100+
- WebSocket connections: 1000+
- No errors under load
- Memory stable

## 🚨 Critical Test Failures

If these fail, **DO NOT DEPLOY**:
- SQL injection protection
- Authentication bypass
- Payment processing
- Balance atomicity
- Rate limiting
- Security headers

## 📝 Test Coverage Goals

- Backend: > 80%
- Frontend: > 70%
- E2E: Critical flows covered
- Security: All OWASP Top 10

Check coverage:
```bash
# Backend
npm test
open htmlcov/index.html

# Frontend
npm run test:frontend:coverage
```

## 🤝 Contributing Tests

When adding new features:
1. Add unit tests in `server_fastapi/tests/`
2. Add E2E tests in `tests/e2e/` if UI changes
3. Update `TESTING_GUIDE.md` if new test category
4. Add to `test_pre_deploy.py` if new critical path

## 📞 Support

For testing issues:
1. Check `docs/TESTING_GUIDE.md` for detailed instructions
2. Review existing tests in `server_fastapi/tests/`
3. Check CI/CD logs for automated test results
4. Consult team leads for deployment approval

## 🔗 Related Documentation

- [Testing Guide](./TESTING_GUIDE.md) - Complete testing checklist
- [Deployment Scorecard](./DEPLOYMENT_SCORECARD.md) - Readiness assessment
- [Architecture](./architecture.md) - System architecture
- [API Documentation](./api.md) - API reference
