# Cursor Setup - What You Need to Do

**Quick setup instructions after all configuration is complete**

---

## ✅ What's Already Done

- ✅ 9 Project Rules configured
- ✅ 14 Commands created
- ✅ All documentation written
- ✅ `.vscode/extensions.json` created (54 extensions)
- ✅ `.cursorignore` updated to allow extensions.json

---

## ⚠️ Manual Setup Required First

**Two manual steps** needed before automatic setup:

1. **Update `.cursorignore`**: Add `!.vscode/extensions.json` (see [Manual Setup](./MANUAL_SETUP_REQUIRED.md))
2. **Create `.vscode/extensions.json`**: Create file with 54 extensions (see [Manual Setup](./MANUAL_SETUP_REQUIRED.md))

**Then proceed with steps below.**

---

## 🚀 What You Need to Do (5 Minutes)

### Step 1: Verify Project Rules (1 minute)

1. Open **Cursor Settings**: `Ctrl/Cmd + ,`
2. Go to **Rules and Commands** → **Project Rules**
3. Verify you see:
   - **Always Applied**: 4 rules
   - **Pattern Matched**: 5 rules

**If not visible**: Reload Cursor (`Ctrl+Shift+P` → "Reload Window")

### Step 2: Test Commands (1 minute)

1. Open **Cursor Chat**
2. Type `/` to see available commands
3. You should see **14 commands** listed

**If not visible**: Reload Cursor

### Step 3: Install Extensions (2 minutes)

1. **Open CryptoOrchestrator folder** in Cursor
2. **Look for notification**: "This workspace has extension recommendations"
3. **Click "Install All"** or "Show Recommendations"
4. **Install Phase 1 extensions** (16 essential extensions)

**Location**: `.vscode/extensions.json` (54 extensions configured)

### Step 4: Configure MCP Hub (1 minute)

1. Open **Cursor Settings**: `Ctrl/Cmd + ,`
2. Go to **Features** → **MCP**
3. **Enable**: `mcp-hub` server
4. **Disable**: All individual MCP servers (to avoid 40-tool limit)
5. **Restart Cursor**: Full restart required

**See**: [MCP Hub Setup Guide](./MCP_HUB_SETUP.md) for details

---

## ✅ Verification Checklist

- [ ] Project Rules visible in Settings (9 rules)
- [ ] Commands accessible (type `/` - 14 commands)
- [ ] Extensions prompt appeared (or manually install)
- [ ] MCP Hub enabled (Settings → Features → MCP)

---

## 🎯 Quick Test

Ask the AI: **"What are the naming conventions for Python functions?"**

The AI should reference your `project-conventions` rule.

---

## 📚 Documentation

All documentation is in `docs/cursor/`:
- **[Quick Reference](./QUICK_REFERENCE.md)** - One-page reference
- **[Team Onboarding](./TEAM_ONBOARDING.md)** - Complete guide
- **[Extensions Quick Setup](./EXTENSIONS_QUICK_SETUP.md)** - Extension installation
- **[MCP Hub Setup](./MCP_HUB_SETUP.md)** - MCP configuration

---

## 🆘 Troubleshooting

### Rules Not Showing
- Reload Cursor: `Ctrl+Shift+P` → "Reload Window"
- Check `.cursorignore` allows rules
- Restart Cursor completely

### Commands Not Appearing
- Check `.cursor/commands/` directory exists
- Reload Cursor
- Restart Cursor completely

### Extensions Not Prompting
- Check `.vscode/extensions.json` exists
- Reload Cursor
- Manually: Extensions → "Show Recommended Extensions"

### MCP Hub Not Working
- Enable **only** `mcp-hub` in Settings
- Disable all individual MCP servers
- Restart Cursor completely

---

## Summary

**5 Minutes to Complete**:
1. ✅ Verify Rules (1 min)
2. ✅ Test Commands (1 min)
3. ✅ Install Extensions (2 min)
4. ✅ Configure MCP Hub (1 min)

**Everything else is automatic!** 🎉
