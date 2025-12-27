# Contributing to CryptoOrchestrator

Thank you for your interest in contributing to CryptoOrchestrator! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Commit Guidelines](#commit-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Code Review Guidelines](#code-review-guidelines)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/your-username/CryptoOrchestrator.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Test your changes**
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Setup Steps

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**:
   ```bash
   alembic upgrade head
   ```

5. **Start services**:
   ```bash
   docker-compose up -d  # Or start services manually
   ```

6. **Run development server**:
   ```bash
   # Backend
   uvicorn server_fastapi.main:app --reload
   
   # Frontend
   npm run dev
   ```

## Development Workflow

### Branch Naming

- `feature/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `docs/documentation-name` - Documentation updates
- `refactor/refactor-name` - Code refactoring
- `test/test-name` - Test additions/updates

### Workflow Steps

1. **Create a branch** from `develop`
2. **Make your changes**
3. **Write/update tests**
4. **Run tests and linting**
5. **Commit your changes**
6. **Push to your fork**
7. **Create a pull request**

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints
- Maximum line length: 120 characters
- Use `ruff` for linting
- Use `black` for formatting
- Use `mypy` for type checking

**Example**:
```python
from typing import Optional, Dict, Any

async def process_trade(
    trade_id: int,
    user_id: int,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Process a trade with optional configuration."""
    # Implementation
    pass
```

### TypeScript/React

- Follow ESLint rules
- Use TypeScript strict mode
- Use functional components with hooks
- Maximum line length: 120 characters
- Use Prettier for formatting

**Example**:
```typescript
interface TradeProps {
  tradeId: number;
  userId: number;
  config?: Record<string, unknown>;
}

export const TradeComponent: React.FC<TradeProps> = ({
  tradeId,
  userId,
  config,
}) => {
  // Implementation
  return <div>Trade {tradeId}</div>;
};
```

### Database

- Use Alembic for migrations
- Follow naming conventions (snake_case)
- Add indexes for frequently queried columns
- Document complex queries

## Testing Guidelines

### Backend Tests

- Use `pytest` for testing
- Aim for 90%+ code coverage
- Write unit tests for services
- Write integration tests for API endpoints
- Mock external dependencies

**Example**:
```python
import pytest
from fastapi.testclient import TestClient

def test_create_trade(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/trades",
        json={"symbol": "BTC/USD", "amount": 0.1},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["symbol"] == "BTC/USD"
```

### Frontend Tests

- Use Vitest for unit tests
- Use Playwright for E2E tests
- Test user interactions
- Test error handling

**Example**:
```typescript
import { render, screen } from '@testing-library/react';
import { TradeComponent } from './TradeComponent';

test('renders trade component', () => {
  render(<TradeComponent tradeId={1} userId={1} />);
  expect(screen.getByText(/Trade 1/i)).toBeInTheDocument();
});
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/updates
- `chore`: Build/tooling changes

### Examples

```
feat(trading): Add OCO order support

Implement One-Cancels-Other order type with proper
validation and execution logic.

Closes #123
```

```
fix(auth): Resolve session expiration issue

Fix bug where sessions were expiring prematurely
due to incorrect timestamp calculation.
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Commit messages follow guidelines

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How to test these changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
```

## Code Review Guidelines

### For Reviewers

- Be constructive and respectful
- Focus on code quality and correctness
- Ask questions if something is unclear
- Approve when satisfied
- Request changes with specific feedback

### For Authors

- Respond to all comments
- Make requested changes
- Explain decisions when needed
- Keep PRs focused and small
- Update PR description if needed

## Additional Resources

- [Architecture Documentation](docs/developer/ARCHITECTURE.md)
- [Code Style Guide](docs/developer/CODE_STYLE.md)
- [API Documentation](docs/developer/API_DESIGN.md)
- [Testing Guide](docs/developer/TESTING.md)

## Questions?

If you have questions, please:
- Open an issue for bugs or feature requests
- Start a discussion for questions
- Contact maintainers for urgent matters

Thank you for contributing to CryptoOrchestrator! 🚀
