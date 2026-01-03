# Cursor IDE - Team Onboarding Guide

**For New Team Members**  
**Date**: December 30, 2025

---

## Welcome! 👋

This guide will help you set up Cursor IDE for CryptoOrchestrator development. The setup is quick and most things are already configured!

---

## Quick Start (5 Minutes)

### Step 1: Install Cursor IDE

1. Download from [cursor.com](https://cursor.com)
2. Install Cursor IDE
3. Open Cursor IDE

### Step 2: Clone Repository

```bash
git clone <repository-url>
cd CryptoOrchestrator
```

### Step 3: Verify Setup

1. **Open Project**: Open the `CryptoOrchestrator` folder in Cursor
2. **Check Rules**: Settings → Rules and Commands → Project Rules (should show 9 rules)
3. **Check Commands**: Type `/` in chat (should show 9 commands)

**That's it!** Project Rules and Commands are automatically available.

---

## What's Already Configured

### ✅ Project Rules (Automatic)

**9 Project Rules** are already configured and shared via git:
- 4 Always Applied rules (core conventions)
- 5 Context-Aware rules (domain-specific)

**No setup needed** - they're automatically available when you open the project!

### ✅ Commands (Automatic)

**14 Commands** are already created and shared via git:
- Setup & development workflows
- Testing workflows
- Database operations
- Code quality checks
- Deployment workflows

**No setup needed** - type `/` in chat to use them!

---

## Optional Setup

### User Rules (Personal Preferences)

User Rules are **optional** personal preferences. They're useful if you have:
- Personal coding style preferences
- Communication preferences
- Workflow preferences

**Setup** (optional):
1. Settings → Rules and Commands → User Rules
2. Add your personal preferences
3. See [User Rules Guide](./USER_RULES_BEST_PRACTICES.md) for examples

**Note**: Project Rules provide most of what you need - User Rules are optional.

### Extensions (Recommended)

Extensions enhance Cursor's capabilities. **Recommended** but not required.

**Automatic Installation**:
- All 54 extensions are configured in `.vscode/extensions.json`
- Cursor will automatically prompt you to install when you open the project
- Click "Install All" or install individually

**Essential Extensions** (Phase 1):
- Error Lens - See errors inline
- ESLint - Code linting
- Prettier - Code formatting
- Python + Pylance - Python support
- GitLens - Enhanced Git features

**See**: 
- [Extensions Setup Guide](./EXTENSIONS_SETUP_GUIDE.md) - Complete guide (54 extensions)
- [Developer Onboarding](../../development/DEVELOPER_ONBOARDING.md) - Setup instructions

---

## Using Cursor Features

### Project Rules

**Automatic** - Rules are automatically applied based on:
- Always Applied: Included in every chat
- Pattern Matched: Applied when working with relevant files

**Example**: When you open a test file, the `testing.mdc` rule is automatically included.

### Commands

**Manual** - Type `/` in chat to see available commands.

**Common Commands**:
- `/setup` - Complete project setup
- `/dev-start` - Start development services
- `/test-all` - Run all tests
- `/migrate` - Database migrations
- `/code-quality` - Code quality checks

### Chat with AI

The AI agent has full project context from Project Rules:
- Knows project conventions
- Understands architecture patterns
- Follows coding standards
- Provides domain-specific guidance

**Just ask!** The AI knows the project inside and out.

---

## Common Workflows

### Starting Development

1. **Setup Project** (first time):
   ```
   /setup
   ```

2. **Start Services**:
   ```
   /dev-start
   ```

3. **Run Tests**:
   ```
   /test-all
   ```

### Daily Development

1. **Ask AI for help**: Just chat naturally - AI has full context
2. **Use commands**: Type `/` for common workflows
3. **Follow rules**: Rules are automatically applied

### Code Quality

1. **Check code quality**:
   ```
   /code-quality
   ```

2. **Fix issues**: AI will help based on project rules

### Database

1. **Run migrations**:
   ```
   /migrate
   ```

2. **Backup database**:
   ```
   /db-backup
   ```

---

## Troubleshooting

### Rules Not Showing

1. **Reload Cursor**: `Ctrl+Shift+P` → "Reload Window"
2. **Check git**: Ensure you pulled latest changes
3. **Verify files**: Check `.cursor/rules/` directory exists

### Commands Not Appearing

1. **Type `/`**: Make sure you're in chat
2. **Check git**: Ensure you pulled latest changes
3. **Verify files**: Check `.cursor/commands/` directory exists

### AI Not Following Rules

1. **Check rules are visible**: Settings → Rules and Commands → Project Rules
2. **Reload Cursor**: `Ctrl+Shift+P` → "Reload Window"
3. **Check file context**: Rules apply based on open files

---

## Getting Help

### Documentation

- **[Project Rules Guide](./PROJECT_RULES_GUIDE.md)** - Complete rules documentation
- **[Commands Guide](./CURSOR_COMMANDS_GUIDE.md)** - Complete commands documentation
- **[Setup Complete](./CURSOR_SETUP_COMPLETE.md)** - Complete setup guide
- **[User Rules Guide](./USER_RULES_BEST_PRACTICES.md)** - User Rules examples

### Ask the AI

The AI has full project context - just ask:
- "How do I create a new trading bot?"
- "What are the naming conventions?"
- "How do I run tests?"
- "What's the service layer pattern?"

---

## Best Practices

1. **Use Commands**: Type `/` for common workflows
2. **Trust the AI**: It has full project context
3. **Follow Rules**: Rules are automatically applied
4. **Ask Questions**: The AI knows the project inside and out
5. **Update Rules**: If you find improvements, update rules and commit

---

## Summary

✅ **What's Automatic**:
- Project Rules (9 rules)
- Commands (9 commands)

⚠️ **What's Optional**:
- User Rules (personal preferences)
- Extensions (recommended)
- MCP Servers (advanced features)

**You're ready to code!** The AI agent has full project context and workflows are standardized.

---

## Next Steps

1. ✅ Verify Project Rules are visible
2. ✅ Test Commands (type `/` in chat)
3. ⚠️ Install recommended extensions (optional)
4. ⚠️ Add User Rules if desired (optional)
5. 🚀 Start coding!

Welcome to the team! 🎉
