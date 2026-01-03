# Code Quality Checks

Run comprehensive code quality checks for CryptoOrchestrator.

## Quick Quality Check

Run all quality checks:
```bash
npm run check:quality
```

This runs:
- TypeScript type checking
- ESLint linting
- Code formatting checks
- Dependency checks

## Individual Checks

### Linting

**Frontend (ESLint):**
```bash
npm run lint
```

**Backend (Flake8):**
```bash
npm run lint:py
```

### Formatting

**Check Formatting:**
```bash
npm run format:check
```

**Format Code:**
```bash
# Frontend
npm run format

# Backend
npm run format:py
```

### Type Checking

**TypeScript:**
```bash
npm run check
```

### Comprehensive Check

Run all checks:
```bash
npm run check:all
```

This includes:
- Type checking
- Linting (frontend + backend)
- Formatting checks
- Dependency checks
- Security audit

## Code Quality Analysis

### Performance Analysis
```bash
npm run analyze:performance
```

### Route Analysis
```bash
npm run analyze:routes
```

### Dependency Check
```bash
npm run check:dependencies
```

## Security Audit

Run security audit:
```bash
npm run audit:security
```

This checks:
- npm vulnerabilities
- Python package vulnerabilities (safety)
- Security best practices

## Best Practices

1. **Run Before Committing**: Always run `npm run check:quality` before committing
2. **Fix Linting Errors**: Don't commit code with linting errors
3. **Format Code**: Use `npm run format` to auto-fix formatting
4. **Type Safety**: Fix TypeScript errors before committing
5. **Security**: Address security vulnerabilities immediately

## Pre-Commit Checklist

- [ ] Type checking passes: `npm run check`
- [ ] Linting passes: `npm run lint` and `npm run lint:py`
- [ ] Formatting is correct: `npm run format:check`
- [ ] No security vulnerabilities: `npm run audit:security`
- [ ] Tests pass: `npm run test:all`
