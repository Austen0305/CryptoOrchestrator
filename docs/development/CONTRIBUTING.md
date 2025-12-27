# Contributing to CryptoOrchestrator

Thank you for your interest in contributing to CryptoOrchestrator! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Commit Message Guidelines](#commit-message-guidelines)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Expected Behavior

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Accept responsibility for mistakes
- Celebrate others' contributions

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information
- Other conduct that could reasonably be considered inappropriate

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/Crypto-Orchestrator.git
cd Crypto-Orchestrator

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/Crypto-Orchestrator.git
```

### 2. Set Up Development Environment

Follow the [Developer Onboarding Guide](./DEVELOPER_ONBOARDING.md) for complete setup instructions.

**Quick Setup:**
```bash
# Install dependencies
pip install -r requirements.txt
npm install --legacy-peer-deps

# Create environment file
python scripts/generate_env.py  # or scripts/create_env.ps1 on Windows

# Initialize database
alembic upgrade head
```

### 3. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

---

## 🔄 Development Process

### 1. Make Your Changes

- Follow code standards (see below)
- Write tests for new features
- Update documentation
- Keep commits focused and atomic

### 2. Test Your Changes

```bash
# Run all tests
npm run test:all

# Backend tests
pytest server_fastapi/tests/ -v

# Frontend tests
npm run test:frontend

# E2E tests
npm run test:e2e

# Check code quality
npm run lint:py
npm run check
```

### 3. Commit Your Changes

Follow [Commit Message Guidelines](#commit-message-guidelines):

```bash
git add .
git commit -m "feat: add new trading strategy endpoint"
```

### 4. Keep Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase on main (preferred) or merge
git rebase upstream/main
# or
git merge upstream/main
```

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation updated
- [ ] No console.log/debug statements
- [ ] Error handling implemented
- [ ] Type hints/types added
- [ ] No sensitive data in logs
- [ ] Branch is up to date with main

### Creating a Pull Request

1. **Go to GitHub** and create a pull request from your fork
2. **Fill out the PR template:**
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

3. **Wait for CI checks** to pass
4. **Address review feedback** if requested
5. **Squash commits** if requested by maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process

1. **Automated Checks:**
   - CI tests must pass
   - Code coverage must not decrease
   - Linting must pass
   - Type checking must pass

2. **Code Review:**
   - At least one maintainer approval required
   - Address all review comments
   - Keep discussions constructive

3. **Merge:**
   - Maintainers will merge after approval
   - PRs are typically squashed before merging

---

## 📝 Code Standards

### Python Standards

**Formatting:**
- Use **Black** (88 char line length)
- Run: `npm run format:py` or `python -m black .`

**Linting:**
- Use **Flake8**
- Run: `npm run lint:py` or `python -m flake8 .`
- Max complexity: 10
- Max line length: 88

**Type Hints:**
- Use type hints on all functions
- Use `Annotated` for FastAPI dependencies
- Enable MyPy strict mode

**Key Patterns:**
```python
# ✅ Good: Use Annotated for dependencies
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        try:
            yield session
        except HTTPException:
            await session.rollback()
            raise
        finally:
            await session.close()

@router.post('/bots')
async def create_bot(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    # Implementation
    pass

# ✅ Good: SQLAlchemy boolean comparisons
query = select(Bot).where(Bot.is_active.is_(True))

# ❌ Bad: Direct boolean comparison
query = select(Bot).where(Bot.is_active == True)
```

### TypeScript Standards

**Formatting:**
- Use **Prettier**
- Run: `npm run format`

**Linting:**
- Use **ESLint**
- Run: `npm run lint`

**Type Safety:**
- No `any` types (use `unknown` if needed)
- TypeScript strict mode enabled
- Use type assertions sparingly

**Key Patterns:**
```typescript
// ✅ Good: React Query with proper query keys
export const useBots = () => {
  return useQuery({
    queryKey: ['bots'],
    queryFn: () => botApi.getBots(),
    staleTime: 30000,
  });
};

// ✅ Good: Trading mode normalization
const normalizedMode = mode === "live" ? "real" : mode;
await portfolioApi.getPortfolio(normalizedMode);

// ❌ Bad: Using any
function processData(data: any) { }

// ✅ Good: Using unknown
function processData(data: unknown) {
  if (typeof data === 'object' && data !== null) {
    // Type narrowing
  }
}
```

### Code Organization

**Backend:**
- Routes: Thin controllers, delegate to services
- Services: Business logic, stateless preferred
- Repositories: Data access only
- Models: SQLAlchemy ORM models
- Dependencies: FastAPI dependency providers

**Frontend:**
- Components: UI components (shadcn/ui)
- Hooks: Custom React hooks
- Lib: Utilities and API clients
- Pages: Page components
- Utils: Performance and optimization utilities

---

## 🧪 Testing Requirements

### Test Coverage

- **Backend:** ≥85% coverage
- **Frontend:** ≥85% coverage
- **E2E:** Critical user flows covered
- **Security:** All security checklist items verified

### Writing Tests

**Backend (pytest):**
```python
@pytest.mark.asyncio
async def test_create_bot_success(client: AsyncClient, test_user: dict):
    response = await client.post(
        "/api/bots",
        json={"name": "Test Bot", "strategy": "momentum"},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Bot"
```

**Frontend (Vitest):**
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('BotList', () => {
  it('should render bot list', () => {
    render(<BotList />);
    expect(screen.getByText('My Bot')).toBeInTheDocument();
  });
});
```

**E2E (Playwright):**
```typescript
test('should create bot', async ({ page }) => {
  await page.goto('/bots');
  await page.getByTestId('create-bot-btn').click();
  await page.fill('input[name="name"]', 'Test Bot');
  await page.click('button[type="submit"]');
  await expect(page.locator('text=Test Bot')).toBeVisible();
});
```

### Test Checklist

- [ ] Unit tests for new functions/methods
- [ ] Integration tests for new endpoints
- [ ] E2E tests for critical user flows
- [ ] Error cases covered
- [ ] Edge cases covered
- [ ] Tests are isolated and independent

---

## 📚 Documentation

### Code Documentation

**Python Docstrings:**
```python
async def create_bot(
    request: CreateBotRequest,
    user_id: str,
    db: AsyncSession
) -> BotResponse:
    """
    Create a new trading bot for the user.
    
    Args:
        request: Bot configuration request
        user_id: ID of the user creating the bot
        db: Database session
        
    Returns:
        BotResponse with created bot details
        
    Raises:
        HTTPException: If bot creation fails
    """
    # Implementation
```

**TypeScript JSDoc:**
```typescript
/**
 * Hook for fetching and managing trading bots.
 * 
 * @returns Query result with bots data, loading state, and error state
 */
export function useBots() {
  return useQuery({
    queryKey: ['bots'],
    queryFn: () => botApi.getBots(),
  });
}
```

### Documentation Updates

When adding new features:
- [ ] Update API documentation (`docs/API_REFERENCE.md`)
- [ ] Update user guide if user-facing
- [ ] Add code examples
- [ ] Update README if needed
- [ ] Add migration notes for breaking changes

---

## 💬 Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Test additions/updates
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```bash
feat(bots): add ML strategy support

Add support for machine learning-based trading strategies.
Includes LSTM model integration and backtesting capabilities.

Closes #123

fix(trades): resolve price calculation error

Correct price calculation for DEX swaps with slippage.
Previously miscalculated price impact for large orders.

Fixes #456

docs(api): update authentication examples

Add examples for JWT token refresh and MFA setup.

refactor(services): extract risk calculation logic

Move risk calculation to dedicated service for better
testability and reusability.
```

### Commit Best Practices

- Write clear, descriptive commit messages
- Keep commits focused (one logical change per commit)
- Use present tense ("add feature" not "added feature")
- Reference issues in footer: `Closes #123`
- Break large changes into multiple commits

---

## 🎯 Contribution Areas

### Good First Issues

Look for issues labeled `good first issue` on GitHub. These are:
- Well-defined and scoped
- Suitable for newcomers
- Have clear acceptance criteria

### Areas Needing Contributions

- **Testing:** Increase test coverage
- **Documentation:** Improve docs, add examples
- **Performance:** Optimize slow endpoints
- **Accessibility:** Improve WCAG compliance
- **Internationalization:** Add translations
- **Mobile:** React Native improvements

### Feature Requests

- Open an issue first to discuss
- Get maintainer approval before implementing
- Follow the feature request template
- Consider backward compatibility

---

## 🚫 What Not to Contribute

- **Security vulnerabilities:** Report privately via security@cryptoorchestrator.com
- **Breaking changes:** Discuss with maintainers first
- **Large refactors:** Open an issue to discuss approach
- **Dependencies:** Check with maintainers before adding new dependencies

---

## ✅ Checklist for Contributors

Before submitting:

- [ ] Read [Developer Onboarding Guide](./DEVELOPER_ONBOARDING.md)
- [ ] Followed code standards
- [ ] All tests pass
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main
- [ ] PR description is complete
- [ ] No sensitive data in code/logs
- [ ] Code is properly formatted
- [ ] Type hints/types are complete

---

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Recognized in project documentation

---

## 📞 Questions?

- **GitHub Issues:** For bug reports and feature requests
- **Discord:** For developer discussions
- **Email:** dev-support@cryptoorchestrator.com

---

**Thank you for contributing to CryptoOrchestrator!** 🚀

*Last updated: 2025-12-06*
