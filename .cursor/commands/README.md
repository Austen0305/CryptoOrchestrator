# Cursor Commands for CryptoOrchestrator

**What are Cursor Commands?**

Cursor Commands are reusable workflows that you can trigger with the `/` prefix in the chat input. They help standardize common tasks and make development workflows more efficient.

**How Commands Work:**

1. Commands are stored in `.cursor/commands/` as `.md` files
2. Type `/` in chat to see available commands
3. Commands provide instructions to the AI for specific workflows
4. Commands can reference scripts, npm commands, or provide step-by-step guidance

**Difference from Rules:**

- **Rules**: Provide context and guidelines (always applied or context-aware)
- **Commands**: Provide specific workflows and tasks (triggered manually)

---

## Available Commands

### Setup & Development
- `/setup` - Complete project setup guide
- `/dev-start` - Start all development services
- `/quick-start` - Quick start guide for new developers

### Testing
- `/test-all` - Run all test suites
- `/test-backend` - Run backend tests with coverage
- `/test-frontend` - Run frontend tests
- `/test-e2e` - Run end-to-end tests
- `/test-coverage` - Generate and view test coverage

### Database
- `/migrate` - Run database migrations
- `/migrate-create` - Create new migration
- `/migrate-rollback` - Rollback last migration
- `/db-backup` - Backup database
- `/db-restore` - Restore database

### Code Quality
- `/lint` - Run linting checks
- `/format` - Format code (Prettier + Black)
- `/check-quality` - Comprehensive code quality check
- `/audit-security` - Security audit

### Deployment
- `/deploy-staging` - Deploy to staging
- `/deploy-production` - Deploy to production ⭐ NEW
- `/health-check` - Check service health ⭐ NEW
- `/verify-deployment` - Verify deployment

### Database
- `/db-backup` - Database backup
- `/db-restore` - Database restore ⭐ NEW

### Quick Start
- `/quick-start` - Quick start guide ⭐ NEW

### Security
- `/security-audit` - Security audit ⭐ NEW

### Troubleshooting
- `/troubleshoot-startup` - Troubleshoot startup issues
- `/troubleshoot-database` - Troubleshoot database issues
- `/troubleshoot-services` - Troubleshoot service issues

---

## Creating New Commands

1. Create a `.md` file in `.cursor/commands/`
2. Use descriptive filename (e.g., `test-all.md`)
3. Write clear instructions for the AI
4. Reference scripts, commands, or provide step-by-step guidance

**Example Command File** (`test-all.md`):

```markdown
# Run All Tests

Execute the complete test suite for CryptoOrchestrator:

1. **Backend Tests**: Run `pytest server_fastapi/tests/ -v --cov=server_fastapi --cov-report=html`
2. **Frontend Tests**: Run `npm run test:frontend`
3. **E2E Tests**: Run `npm run test:e2e`
4. **Generate Coverage Report**: Run `npm run test:coverage`

Check test results and coverage reports.
```

---

## Best Practices

1. **Be Specific**: Provide clear, actionable instructions
2. **Reference Scripts**: Use existing npm scripts or Python scripts when possible
3. **Include Context**: Explain what the command does and when to use it
4. **Keep Focused**: One command per file, focused on a single workflow
5. **Update Regularly**: Keep commands in sync with project changes

---

## Usage

Type `/` in the Cursor chat input to see all available commands, then select the one you need.
