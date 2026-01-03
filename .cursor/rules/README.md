# Cursor Rules for CryptoOrchestrator

This directory contains Project Rules for the CryptoOrchestrator platform. These rules help Cursor understand our coding standards, conventions, and best practices.

## Available Rules

### Always Applied Rules

These rules are automatically included in every chat session:

1. **`project-conventions.mdc`** - Project-wide conventions and patterns
   - File structure and organization
   - Naming conventions
   - API design patterns
   - Git and commit conventions
   - Testing and deployment standards

2. **`python-fastapi.mdc`** - Python and FastAPI backend development
   - Python 3.12 best practices
   - FastAPI patterns and conventions
   - SQLAlchemy async patterns
   - Type hints and error handling
   - Testing standards

3. **`react-typescript.mdc`** - React and TypeScript frontend development
   - React 18 and TypeScript 5.9+ standards
   - Component patterns and hooks
   - React Query usage
   - TailwindCSS and shadcn/ui conventions
   - Form handling and validation

4. **`security-blockchain.mdc`** - Security and blockchain-specific rules
   - Private key management
   - Authentication and authorization
   - Input validation
   - Blockchain transaction security
   - DEX trading security patterns

### Context-Aware Rules

These rules are applied when working with relevant files:

5. **`testing.mdc`** - Testing standards and patterns
   - pytest patterns for backend
   - Vitest patterns for frontend
   - Playwright E2E testing
   - Test organization and best practices
   - Applied when: `**/*test*.py`, `**/*test*.ts`, `**/*test*.tsx`, `**/*.spec.ts`, `tests/**/*`

6. **`database-migrations.mdc`** - Database migration patterns
   - Alembic migration best practices
   - Migration file structure
   - Data migration patterns
   - Applied when: `alembic/**/*`, `**/migrations/**/*`, `**/*migration*.py`

7. **`deployment.mdc`** - Deployment patterns and best practices
   - Docker and Docker Compose
   - Kubernetes manifests
   - Environment configuration
   - Health checks and monitoring
   - Applied when: `docker-compose*.yml`, `Dockerfile*`, `k8s/**/*`, `terraform/**/*`, `*.toml`, `Procfile`, `render.yaml`

8. **`trading-blockchain-domain.mdc`** - Domain-specific trading and blockchain patterns
   - Trading bot execution patterns
   - DEX trading with aggregators (0x, OKX, Rubic)
   - Blockchain integration patterns
   - ML/AI prediction patterns
   - Risk management patterns
   - Applied when: `server_fastapi/services/trading/**/*`, `server_fastapi/services/blockchain/**/*`, `server_fastapi/services/ml/**/*`, `server_fastapi/repositories/**/*`, `server_fastapi/dependencies/**/*`

9. **`service-architecture.mdc`** - Service layer and repository patterns
   - Service layer architecture
   - Repository pattern implementation
   - Dependency injection patterns
   - Transaction management
   - Service composition
   - Applied when: `server_fastapi/services/**/*`, `server_fastapi/repositories/**/*`, `server_fastapi/dependencies/**/*`

## Rule Format

Each rule is a `.mdc` file (Markdown with YAML frontmatter) that includes:

```markdown
---
description: Brief description of the rule
globs: ["**/*.py"]  # File patterns where rule applies
alwaysApply: true   # Whether to always include in context
---

# Rule Content
...
```

## Rule Types

Based on the frontmatter configuration, rules can be:

- **Always Apply**: Included in every chat session (`alwaysApply: true`)
- **Apply Intelligently**: When Agent decides it's relevant based on description
- **Apply to Specific Files**: When file matches a specified pattern (`globs`)
- **Apply Manually**: When @-mentioned in chat (e.g., `@testing`)

## How Rules Work

Large language models don't retain memory between completions. Rules provide persistent, reusable context at the prompt level.

When applied, rule contents are included at the start of the model context. This gives the AI consistent guidance for generating code, interpreting edits, or helping with workflows.

## Using Rules in Chat

You can manually invoke rules in chat:

```
@testing How should I structure my test for the new trading bot feature?
@database-migrations What's the best way to add a new column to the users table?
@deployment How do I set up health checks for Kubernetes?
```

## Updating Rules

When updating rules:

1. Edit the appropriate `.mdc` file in `.cursor/rules/`
2. Ensure YAML frontmatter is valid
3. Save the file (important - rules may not appear until saved)
4. Test the rule with Cursor's AI features
5. Commit changes to version control

## Troubleshooting

### Rules Not Showing in Settings

If rules don't appear in Cursor Settings:

1. **Save the files**: Make sure all `.mdc` files are saved
2. **Reload Cursor**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) → "Reload Window"
3. **Check `.cursorignore`**: Ensure rules aren't being ignored (see `.cursorignore` file)
4. **Check file format**: Verify YAML frontmatter is correct (must start with `---`)
5. **Restart Cursor**: Sometimes a full restart is needed

### Known Issues

- **RULE.md folder format**: The `RULE.md` folder format (`.cursor/rules/<folder>/RULE.md`) has a known bug in Cursor versions up to 2.3.10 where rules don't show in settings. The `.mdc` format works reliably.
- **File recognition**: Cursor may take a few seconds to recognize new rule files. Try reloading the window.

## Best Practices

1. **Keep rules focused**: Each rule file should cover one topic
2. **Update regularly**: Keep rules in sync with project standards
3. **Be specific**: Use glob patterns to target relevant files
4. **Document examples**: Include code examples in rules
5. **Version control**: Commit rules to git so the team shares them
6. **Keep under 500 lines**: Split large rules into multiple, composable rules

## File Structure

```
.cursor/rules/
├── README.md                    # This file
├── COMPLETE_SETUP.md           # Complete setup guide
├── SETUP_COMPLETE.md           # Setup verification
├── project-conventions.mdc      # ✅ Always applied
├── python-fastapi.mdc          # ✅ Always applied
├── react-typescript.mdc        # ✅ Always applied
├── security-blockchain.mdc     # ✅ Always applied
├── testing.mdc                  # ✅ Context-aware
├── database-migrations.mdc     # ✅ Context-aware
├── deployment.mdc              # ✅ Context-aware
├── trading-blockchain-domain.mdc  # ✅ Context-aware
└── service-architecture.mdc    # ✅ Context-aware
```

## How Cursor Reads Rules

For detailed information on how Cursor processes and applies rules, see:
- **[HOW_CURSOR_READS_RULES.md](HOW_CURSOR_READS_RULES.md)** - Comprehensive guide on rule processing, performance optimization, and best practices

## Cursor Commands

Cursor Commands are reusable workflows triggered with `/` in chat. See:
- **[Commands README](../commands/README.md)** - Complete commands guide
- **[Commands Guide](../commands/CURSOR_COMMANDS_GUIDE.md)** - All available commands

**Available Commands:**
- `/setup` - Complete project setup
- `/dev-start` - Start development services
- `/test-all` - Run all tests
- `/migrate` - Database migrations
- `/code-quality` - Code quality checks
- `/deploy-staging` - Deploy to staging
- `/db-backup` - Database backup
- `/troubleshoot-startup` - Troubleshoot startup issues

## Learning More

- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [Cursor Directory](https://cursor.directory/rules) - Examples from the community
- [Project Code Style Guide](../docs/developer/CODE_STYLE.md)

## Feedback

If you find issues with these rules or have suggestions for improvements, please:

1. Review the rule file
2. Update it with your improvements
3. Commit and share with the team
