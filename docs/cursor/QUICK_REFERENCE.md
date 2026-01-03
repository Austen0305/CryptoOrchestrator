# Cursor IDE - Quick Reference Card

**One-page quick reference for CryptoOrchestrator Cursor setup**

---

## 🚀 Quick Start

1. **Open Project**: Open CryptoOrchestrator folder in Cursor
2. **Verify Rules**: Settings → Rules and Commands → Project Rules (9 rules)
3. **Test Commands**: Type `/` in chat (9 commands)
4. **Start Coding**: AI has full project context!

---

## 📋 Project Rules (9 Total)

### Always Applied (4)
- `project-conventions` - Core conventions
- `python-fastapi` - Backend patterns
- `react-typescript` - Frontend patterns
- `security-blockchain` - Security rules

### Pattern Matched (5)
- `testing` - Test files
- `database-migrations` - Migration files
- `deployment` - Docker/K8s files
- `trading-blockchain-domain` - Trading/blockchain services
- `service-architecture` - Services/repositories

**Location**: `.cursor/rules/*.mdc`  
**Status**: ✅ Automatically applied

---

## ⚡ Commands (9 Total)

| Command | Purpose |
|---------|---------|
| `/setup` | Complete project setup |
| `/dev-start` | Start development services |
| `/test-all` | Run all tests |
| `/migrate` | Database migrations |
| `/code-quality` | Code quality checks |
| `/deploy-staging` | Deploy to staging |
| `/db-backup` | Database backup |
| `/troubleshoot-startup` | Fix startup issues |

**Usage**: Type `/` in Cursor chat  
**Location**: `.cursor/commands/*.md`

---

## 🔧 Common Workflows

### Starting Development
```
/setup          # First time setup
/dev-start      # Start services
```

### Daily Development
```
/test-all       # Run tests
/code-quality   # Check code quality
/migrate        # Run migrations
```

### Deployment
```
/deploy-staging     # Deploy to staging
/deploy-production  # Deploy to production
```

### Troubleshooting
```
/troubleshoot-startup   # Fix startup issues
/health-check           # Check service health
```

---

## 📚 Documentation

- **[Team Onboarding](./TEAM_ONBOARDING.md)** - Quick start for new members
- **[Project Rules Guide](./PROJECT_RULES_GUIDE.md)** - Complete rules docs
- **[Commands Guide](./CURSOR_COMMANDS_GUIDE.md)** - Complete commands docs
- **[Setup Complete](./CURSOR_SETUP_COMPLETE.md)** - Full setup guide
- **[Extensions Guide](./EXTENSIONS_SETUP_GUIDE.md)** - Extensions setup

---

## 🛠️ MCP Servers (12 Working)

**Core**: filesystem, git, context7, stackoverflow, brave-search, coingecko  
**Browser**: puppeteer, cursor-browser-extension  
**AI**: memory, sequential-thinking  
**Research**: arxiv, allthingsdev

**See**: [MCP Integration](./MCP_INTEGRATION.md)

---

## ✅ Verification

### Rules Working?
- Settings → Rules and Commands → Project Rules (should show 9 rules)

### Commands Working?
- Type `/` in chat (should show 9 commands)

### AI Has Context?
- Ask: "What are the naming conventions for Python?"
- AI should reference project-conventions rule

---

## 🆘 Quick Troubleshooting

**Rules not showing?**
- Reload Cursor: `Ctrl+Shift+P` → "Reload Window"

**Commands not appearing?**
- Check `.cursor/commands/` directory exists
- Reload Cursor

**AI not following rules?**
- Check rules are visible in Settings
- Reload Cursor
- Check file context (rules apply based on open files)

---

## 📊 Status

✅ **Project Rules**: 9 rules configured  
✅ **Commands**: 9 commands created  
✅ **Documentation**: Complete guides  
✅ **MCP Servers**: 12 working servers  
✅ **Extensions**: 54 recommended extensions

**Everything is ready!** 🎉

---

**Last Updated**: December 30, 2025
