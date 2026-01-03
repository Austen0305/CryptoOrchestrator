# Cursor User Rules - Copy & Paste Ready

**Last Updated**: December 30, 2025  
**Status**: Ready to use - Copy entire sections into Cursor Settings

---

## 🚀 Quick Start

1. Open Cursor Settings: `Ctrl/Cmd + ,`
2. Search for "Rules" or "User Rules"
3. Click "Edit" or "Add Rule"
4. **Recommended**: Use multiple focused rules (see [Organization Guide](USER_RULES_ORGANIZATION.md))
5. Copy and paste the sections below that apply to your workflow

**💡 Tip**: Multiple focused rules (3-5) work better than one large rule! See [USER_RULES_ORGANIZATION.md](USER_RULES_ORGANIZATION.md) for best practices.

---

## 📋 Complete User Rules (Recommended)

Copy this entire section for comprehensive rules:

```markdown
# Cursor User Rules - Comprehensive Development Guide

## Communication & Response Style

- Be concise and technical in all responses
- Provide working, production-ready code examples
- Explain complex concepts when relevant, but don't over-explain basics
- Prefer practical solutions that work in production over theoretical approaches
- When uncertain about requirements, ask clarifying questions rather than making assumptions
- Include relevant code snippets inline rather than just describing concepts
- Format code examples with proper syntax highlighting and context

## Code Quality Standards

### General Principles
- Write maintainable, readable, and well-documented code
- Follow project-specific conventions and style guides (check `.cursor/rules/` directory)
- Add comments for complex business logic, algorithms, or non-obvious decisions
- Prioritize type safety: TypeScript strict mode for frontend, Python type hints for backend
- Handle errors explicitly - never use silent failures or bare `except` clauses
- Write self-documenting code with clear, descriptive naming
- Prefer composition over inheritance
- Keep functions focused on a single responsibility

### Code Style
- Use consistent formatting (follow project Prettier/Black configs)
- Maintain consistent indentation (spaces, not tabs, unless project uses tabs)
- Use meaningful variable and function names
- Avoid magic numbers - use named constants
- Keep functions/methods reasonably sized (aim for <50 lines, but prioritize clarity)

## TypeScript & Frontend Development

### Type Safety
- Always use TypeScript strict mode
- Never use `any` type - use `unknown` if type is truly unknown, then narrow it
- Define explicit types for function parameters and return values
- Use interfaces for object shapes, types for unions/intersections
- Leverage TypeScript's utility types (Pick, Omit, Partial, etc.)
- Prefer `const` assertions for literal types

### React Best Practices
- Use functional components with hooks (never class components)
- Use React Query (TanStack Query) for server state management
- Use local state (`useState`) only for UI state, not server state
- Extract reusable logic into custom hooks
- Use `React.memo`, `useMemo`, and `useCallback` appropriately (don't over-optimize)
- Handle loading and error states explicitly
- Use proper cleanup in `useEffect` hooks
- Prefer composition patterns over prop drilling

### Component Patterns
```typescript
// ✅ Good: Functional component with proper typing
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export function Button({ label, onClick, disabled = false }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}

// ❌ Bad: Using 'any' or missing types
export function Button(props: any) { ... }
```

### State Management
- Use React Query for all server state
- Use Zustand or Context API for global client state (only when needed)
- Use local state for component-specific UI state
- Avoid prop drilling - use context or state management library if more than 2 levels deep

## Python & Backend Development

### Type Hints
- Use type hints for ALL functions, including parameters and return types
- Use `typing` module for complex types (List, Dict, Optional, Union, etc.)
- Use `Annotated` for FastAPI dependencies
- Prefer Python 3.9+ type syntax (`list[str]` over `List[str]`)

### Async/Await
- Use `async def` for all I/O operations (database, API calls, file operations)
- Use `await` for all async operations
- Use `asyncio.gather()` for parallel async operations when appropriate
- Avoid blocking I/O in async functions
- Properly handle async context managers

### FastAPI Patterns
```python
# ✅ Good: Type hints, async, dependency injection
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    # Implementation

# ❌ Bad: No types, synchronous, no dependency injection
def get_user(user_id, db):
    # Implementation
```

### Error Handling
- Handle errors early with guard clauses
- Use specific exception types, never bare `except:`
- Raise appropriate HTTP exceptions in FastAPI routes
- Log errors with context (use structured logging)
- Return meaningful error messages to clients
- Use try/except around external API calls

### Code Organization
- Group imports: standard library → third-party → local
- Use dependency injection for shared resources
- Keep route handlers thin - move business logic to services
- Use Pydantic models for all request/response validation

## Security Best Practices

### Critical Security Rules
- **NEVER** suggest storing secrets, API keys, or private keys in code, environment files, or commit messages
- **NEVER** log sensitive data (passwords, tokens, private keys, credit card numbers)
- Always validate and sanitize user inputs (use Pydantic/Zod schemas)
- Use parameterized queries for database operations (SQLAlchemy ORM handles this)
- Implement proper authentication and authorization checks
- Follow principle of least privilege
- Use HTTPS in production (never HTTP for sensitive data)
- Implement rate limiting for public APIs

### Blockchain/Security-Specific
- **NEVER** store private keys or seed phrases anywhere
- Use key management services (AWS KMS, HashiCorp Vault, HSM)
- Always validate Ethereum addresses before processing
- Verify balances before executing transactions
- Use idempotency keys for retryable operations
- Log all blockchain transactions (without sensitive data)

### Input Validation
```python
# ✅ Good: Validate with Pydantic
from pydantic import BaseModel, validator

class TradeRequest(BaseModel):
    amount: float
    token_address: str
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

# ❌ Bad: No validation
def process_trade(amount, token_address):
    # Directly use inputs without validation
```

## Testing Standards

### General Testing Philosophy
- Write tests for new features and bug fixes
- Ensure tests are meaningful and cover edge cases
- Prefer integration tests for critical business logic
- Use mocking/spying appropriately for external dependencies
- Maintain test coverage above 85% for new code
- Tests should be fast, isolated, and repeatable
- Use descriptive test names that explain what is being tested

### Test Structure
- Follow Arrange-Act-Assert pattern
- One assertion per test when possible (but allow multiple related assertions)
- Use fixtures for shared test setup
- Clean up test data after tests

### Example Patterns
```python
# ✅ Good: Clear test structure
def test_create_bot_requires_authentication(client):
    # Arrange
    bot_data = {"name": "Test Bot", "strategy": "grid"}
    
    # Act
    response = client.post("/api/bots", json=bot_data)
    
    # Assert
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()
```

## Performance Optimization

### Backend Performance
- Use async/await for all I/O operations
- Implement caching (Redis) for frequently accessed data
- Optimize database queries (avoid N+1 problems, use eager loading)
- Use database indexes appropriately
- Profile before optimizing - measure actual bottlenecks
- Use connection pooling for databases

### Frontend Performance
- Code split routes and large components
- Lazy load components and routes
- Use React.memo for expensive renders (but don't overuse)
- Optimize images (use WebP, lazy loading)
- Use React Query's caching and stale-while-revalidate patterns
- Debounce/throttle user input handlers when appropriate

### When to Optimize
- Profile first to find actual bottlenecks
- Optimize for maintainability first, performance second (unless critical)
- Don't prematurely optimize - clean code is easier to optimize later
- Document performance optimizations and their rationale

## Refactoring Guidelines

### Best Practices
- Refactor incrementally, one concern at a time
- Maintain backward compatibility when possible
- Update tests when refactoring
- Document breaking changes clearly
- Consider impact on existing codebase
- Use feature flags for large refactors
- Refactor in small, reviewable commits

### Code Smell Detection
- Long functions (>50 lines) - break into smaller functions
- Deep nesting (>3 levels) - use early returns, extract functions
- Duplicated code - extract to shared functions/utilities
- Magic numbers - use named constants
- Large files - consider splitting into modules
- Too many parameters (>5) - use configuration objects

## Documentation Standards

### Code Comments
- Write clear docstrings for all public functions, classes, and modules
- Document "why" not "what" - code should be self-explanatory
- Use Google-style docstrings for Python
- Use JSDoc comments for complex TypeScript functions
- Keep comments up-to-date with code changes

### README Files
- Include purpose and overview
- Provide installation/setup instructions
- Include usage examples
- Document API reference for libraries/modules
- Keep README files current with code changes

### Documentation Examples
```python
# ✅ Good: Comprehensive docstring
def calculate_portfolio_value(
    holdings: list[dict],
    prices: dict[str, float],
) -> float:
    """
    Calculate total portfolio value from holdings and current prices.
    
    Args:
        holdings: List of holding dicts with 'symbol' and 'quantity' keys
        prices: Dictionary mapping symbols to current prices
    
    Returns:
        Total portfolio value as a float
    
    Raises:
        ValueError: If holdings list is empty or prices dict is missing symbols
    
    Example:
        >>> holdings = [{"symbol": "BTC", "quantity": 0.5}]
        >>> prices = {"BTC": 50000.0}
        >>> calculate_portfolio_value(holdings, prices)
        25000.0
    """
```

## Git & Version Control

### Commit Messages
Follow Conventional Commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks
- `perf:` Performance improvements
- `style:` Code style changes (formatting)

Examples:
- `feat: Add grid trading strategy`
- `fix: Resolve balance sync issue`
- `docs: Update API documentation`

### Branch Strategy
- Use descriptive branch names: `feature/add-dark-mode`, `fix/login-bug`
- Keep branches focused on a single feature/fix
- Rebase before merging to keep history clean
- Delete merged branches

## Error Handling Patterns

### Backend Error Handling
```python
# ✅ Good: Specific exceptions with context
async def process_trade(trade_id: int) -> dict:
    if not trade_id:
        raise ValueError("Trade ID is required")
    
    trade = await get_trade(trade_id)
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"Trade {trade_id} not found"
        )
    
    try:
        return await execute_trade(trade)
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing trade {trade_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

### Frontend Error Handling
```typescript
// ✅ Good: Proper error boundaries and error states
function TradingBotCard({ botId }: { botId: number }) {
  const { data, error, isLoading } = useQuery({
    queryKey: ['bot', botId],
    queryFn: () => fetchBot(botId),
    retry: 3,
  });

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorDisplay error={error} />;
  if (!data) return null;

  return <BotDetails bot={data} />;
}
```

## API Design Principles

### RESTful APIs
- Use HTTP methods correctly (GET, POST, PUT, DELETE)
- Use resource-based URLs (`/api/bots`, not `/api/getBots`)
- Return consistent response formats
- Use appropriate HTTP status codes
- Implement pagination for list endpoints
- Version APIs when making breaking changes

### Response Format
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

### Error Response Format
```json
{
  "error": {
    "code": "BOT_NOT_FOUND",
    "message": "Bot with ID 123 not found",
    "details": { ... }
  }
}
```

## Database Best Practices

### Query Optimization
- Use indexes on frequently queried columns
- Avoid N+1 queries - use eager loading
- Use pagination for large result sets
- Use transactions for multi-step operations
- Use connection pooling
- Monitor slow queries

### Migration Management
- Always review auto-generated migrations
- Test migrations on staging before production
- Never edit existing migration files
- Use descriptive migration messages
- Keep migrations small and focused

## Logging Standards

### Structured Logging
- Use structured logging with context
- Include relevant IDs (user_id, request_id, etc.)
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Never log sensitive information
- Log errors with stack traces in development, sanitized in production

```python
# ✅ Good: Structured logging with context
logger.info(
    "Bot created successfully",
    extra={
        "bot_id": bot.id,
        "user_id": user.id,
        "strategy": bot.strategy,
    }
)

# ❌ Bad: Logging sensitive data
logger.info(f"User logged in with password: {password}")  # NEVER DO THIS
```

## Dependency Management

### Package Management
- Keep dependencies up-to-date with security patches
- Use lock files (package-lock.json, requirements.txt)
- Pin major versions, allow patch updates
- Regularly audit for vulnerabilities
- Remove unused dependencies
- Document why specific versions are required

## When Working on CryptoOrchestrator Specifically

- Always review project-specific rules in `.cursor/rules/` directory
- Understand the microservices architecture
- Be aware of blockchain/DEX trading context
- Consider real-money implications of code changes
- Follow security rules for wallet and transaction handling
- Use FastAPI dependency injection patterns
- Use React Query for all server state
- Respect existing code patterns and conventions

## MCP (Model Context Protocol) Tools Usage

### Available MCP Servers
This project has 12 working MCP servers configured. Use them intelligently:

#### Core Services (use frequently)
- **filesystem** - File operations (read, write, list, search) - Use for file operations instead of terminal commands
- **git** - Git operations (27 tools) - Use for version control instead of terminal commands
- **context7** - Documentation search - Use to find library/framework documentation
- **stackoverflow** - Stack Overflow search - Use for finding solutions to common problems
- **brave-search** - Web search - Use for current information, API docs, troubleshooting
- **coingecko** - Crypto prices/data - Use for cryptocurrency-related queries

#### Browser Automation (use when needed)
- **cursor-browser-extension** - Browser automation (18 tools) - Use for testing web features, scraping, automation
  - Use `browser_snapshot` to get element refs before clicking/typing
  - Use for E2E testing and web automation tasks
  - Supports screenshots, network monitoring, console access
- **puppeteer** - Browser automation (7 tools) - Alternative browser automation tool

#### AI & Knowledge (use for complex problems)
- **memory** - Knowledge graph (9 tools) - Use to store and retrieve project knowledge
  - Create entities for important concepts
  - Store relationships between components
  - Search knowledge base when needed
- **sequential-thinking** - Problem-solving tool - Use for breaking down complex problems
  - Use when solving multi-step problems
  - Helps with planning and design
  - Useful for analysis with course correction

#### Research (use when needed)
- **arxiv** - Academic papers - Use for research on algorithms, ML models, technical papers
- **allthingsdev** - API marketplace - Use to find APIs and integrations

### MCP Usage Best Practices

#### When to Use MCPs vs Terminal Commands
- **Prefer MCPs** for file operations, git operations, and searches
- **Use terminal** only for commands MCPs don't support
- **Use browser MCPs** for web automation instead of manual testing

#### Search Strategy
1. **First**: Check project files and documentation
2. **Second**: Use context7 for library documentation
3. **Third**: Use stackoverflow for common problems
4. **Fourth**: Use brave-search for current information
5. **Last**: Use arxiv for academic research

#### File Operations
- Use `filesystem` MCP for all file operations when possible
- Use `read_multiple_files` for batch reading
- Use `search_files` for finding files by pattern
- Use `directory_tree` for understanding project structure

#### Git Operations
- Use `git` MCP instead of terminal git commands
- Available operations: status, diff, commit, push, pull, branch management
- Use git MCP for all version control tasks

#### Browser Automation
- Use `cursor-browser-extension` for frontend testing
- Always call `browser_snapshot` first to get element references
- Use for testing user flows, E2E tests, form submissions
- Monitor network requests when debugging API calls

#### Knowledge Management
- Use `memory` MCP to store project decisions and patterns
- Create entities for important concepts (e.g., "Authentication System", "DEX Trading")
- Link related concepts with relations
- Search knowledge base when implementing similar features

#### Problem Solving
- Use `sequential-thinking` for complex, multi-step problems
- Break down architectural decisions
- Plan feature implementations
- Analyze and debug complex issues

### MCP Server Names Reference
When calling via `user-mcp-hub`:
- `filesystem`, `git`, `context7`, `stackoverflow`, `brave-search`, `coingecko`
- `puppeteer`, `memory`, `sequential-thinking`, `arxiv`, `allthingsdev`
- `cursor-browser-extension` (direct call, not via user-mcp-hub)

For detailed MCP documentation, see `MCPs/` directory in the project.

## Cursor Extensions Awareness

### Essential Extensions (54 total, organized in 4 phases)

#### Phase 1: Essential Code Quality (16 extensions)
- **Error Lens** - Inline error display - Always check inline errors
- **ESLint** - JavaScript/TypeScript linting - Fix linting errors immediately
- **Prettier** - Code formatting - Format on save enabled
- **SonarLint** - Code quality analysis - Review suggestions
- **Snyk** - Security vulnerability scanning - Address security issues
- **Python** + **Pylance** - Python language support with strict type checking
- **Black Formatter** - Python code formatting (88 char line length)
- **Python Docstring Generator** - Auto-generate docstrings
- **GitLens** - Enhanced Git capabilities - Use for git blame, history
- **Git Graph** - Visual git history - Use for branch visualization

#### Phase 2: Database & Testing (9 extensions)
- **PostgreSQL**, **SQLite Viewer** - Database management
- **REST Client**, **RapidAPI Client** - API testing tools
- **Coverage Gutters** - Show test coverage in editor
- **Jest Runner** - Run tests from editor

#### Phase 3: Documentation & Productivity (12 extensions)
- **Markdown All in One** - Markdown editing support
- **Path Intellisense** - Path autocomplete for imports
- **Todo Tree** - Manage TODO comments
- **Better Comments** - Highlight important comments

#### Phase 4: Specialized Tools (17 extensions)
- **Docker**, **Kubernetes Tools** - Container and orchestration
- **WakaTime** - Time tracking
- **React Native Tools**, **Expo Tools** - Mobile development

### Extension Usage Guidelines

#### Code Quality
- Fix errors shown by Error Lens immediately
- Run ESLint before committing
- Use Prettier to format code consistently
- Review SonarLint suggestions regularly

#### Git Workflow
- Use GitLens for understanding code history and blame
- Use Git Graph for visualizing branches
- Check git status before making changes

#### Testing
- Use Coverage Gutters to identify untested code
- Run tests with Jest Runner for quick iteration
- Aim for >85% test coverage

#### Documentation
- Use Markdown All in One for README files
- Use Todo Tree to track TODOs across the project
- Keep documentation updated with code changes

### Extension Configuration
All extensions are pre-configured in `.vscode/settings.json`:
- Format on save enabled
- Auto-organize imports on save
- Python strict type checking
- ESLint auto-fix on save
- Coverage gutter enabled

### Verification
- Run `node scripts/utilities/verify-extensions.js` to check installed extensions
- Install missing Phase 1 extensions first (critical)
- Install other phases as needed for your workflow

## AI Assistant Behavior

- When suggesting code changes, explain the reasoning
- Suggest incremental changes rather than large refactors unless asked
- Provide context for why certain patterns are preferred
- Include relevant examples from the codebase when possible
- Respect existing architecture decisions unless there's a compelling reason to change
- Ask clarifying questions when requirements are ambiguous
- Suggest tests along with implementation code
```

---

## 🎯 Minimal Version (Quick Setup)

If you want a shorter, more focused set of rules:

```markdown
# Cursor User Rules - Minimal

## Communication
- Be concise and technical
- Provide working code examples
- Ask clarifying questions when uncertain

## Code Quality
- Use type hints/types for all functions
- Handle errors explicitly
- Write self-documenting code
- Follow project conventions

## Security
- Never store secrets in code
- Always validate inputs
- Never log sensitive data

## Testing
- Write tests for new features
- Maintain >85% coverage for new code

## TypeScript
- Strict mode, no `any` types
- Use React Query for server state
- Functional components with hooks

## Python
- Type hints on all functions
- Use async/await for I/O
- FastAPI dependency injection pattern
- Handle errors with specific exceptions
```

---

## 🔧 Technology-Specific Additions

### For FastAPI Projects
Add this section:

```markdown
## FastAPI Specific
- Use Pydantic v2 for all request/response models
- Use `Annotated[Type, Depends(...)]` for dependencies
- Use `async def` for all route handlers
- Handle errors with HTTPException
- Use response_model in route decorators
- Use SQLAlchemy async patterns
```

### For React Projects
Add this section:

```markdown
## React Specific
- Use TanStack Query for server state
- Use functional components only
- Extract logic to custom hooks
- Use React.memo appropriately
- Handle loading/error states explicitly
- Use TypeScript strict mode
```

### For Blockchain/Web3 Projects
Add this section:

```markdown
## Blockchain/Web3 Specific
- NEVER store private keys anywhere
- Always validate Ethereum addresses
- Verify balances before transactions
- Use idempotency keys for retries
- Log transactions without sensitive data
- Handle failed transactions gracefully
```

---

## 📝 Customization Tips

1. **Start with Minimal**: Begin with the minimal version, add more as needed
2. **Project-Specific**: Review `.cursor/rules/` in each project for specific patterns
3. **Team Alignment**: Share rules with your team for consistency
4. **Iterate**: Update rules as your preferences evolve

---

## ✅ Verification Checklist

After adding rules, verify they're working:

- [ ] Ask Cursor to create a FastAPI route - should use async, type hints, Depends
- [ ] Ask Cursor to create a React component - should use TypeScript, hooks, proper types
- [ ] Ask about security - should never suggest storing secrets
- [ ] Check that code examples match your preferred patterns

---

## 📚 Alternative: Split into Multiple Rules

**💡 Recommended**: For best results, split into **5 focused rules** instead of one large rule.

See:
- **[USER_RULES_ORGANIZATION.md](USER_RULES_ORGANIZATION.md)** - Why multiple rules are better
- **[USER_RULES_SPLIT_VERSIONS.md](USER_RULES_SPLIT_VERSIONS.md)** - Pre-split rules ready to copy

## 🔗 Additional Resources

- **[MCP & Extensions Reference](USER_RULES_MCP_EXTENSIONS.md)** - Detailed MCP and extension usage
- [Cursor Rules Documentation](https://docs.cursor.com/en/context/rules)
- [Cursor Directory - Community Rules](https://cursor.directory/rules)
- [Project Rules README](../../.cursor/rules/README.md)
- [MCPs Directory](../../MCPs/) - MCP documentation in project

---

**Last Updated**: December 30, 2025  
**Based on**: Current best practices, cursor.directory examples, CryptoOrchestrator project needs  
**Includes**: 12 MCP servers, 54 extensions, comprehensive development guidelines
