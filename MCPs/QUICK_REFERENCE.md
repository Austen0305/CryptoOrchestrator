# MCP Quick Reference Guide

Quick lookup for all working MCP servers and their tools.

## 🚀 Quick Access

All working MCPs are documented in the `Working/` directory:
- `filesystem.md` - File operations
- `git.md` - Git operations
- `context7.md` - Documentation search
- `brave-search.md` - Web search
- `stackoverflow.md` - Stack Overflow search
- `puppeteer.md` - Browser automation
- `cursor-browser-extension.md` - Browser extension
- `memory.md` - Knowledge graph
- `sequential-thinking.md` - Problem solving
- `arxiv.md` - Academic papers
- `allthingsdev.md` - API marketplace
- `coingecko.md` - Crypto prices

## 📋 Server Names

When calling MCPs via `user-mcp-hub`, use these server names:

- `filesystem`
- `git`
- `context7`
- `stackoverflow`
- `brave-search`
- `coingecko`
- `puppeteer`
- `memory`
- `sequential-thinking`
- `arxiv`
- `allthingsdev`
- `cursor-browser-extension` (direct call, not via user-mcp-hub)

## 🔑 API Keys

### Configured and Working:
- **Context7:** `ctx7sk-4887ae1b-7ba4-4b29-8ca1-7dfc726c744f`
- **Brave Search:** `BSAzjlwu9t2Hh8uuexDDJR-8I9uge9r`

### Location:
- `C:\Users\William Walker\.cursor\mcp-hub.json`

## 💡 Usage Pattern

```json
{
  "serverName": "SERVER_NAME",
  "toolName": "tool_name",
  "toolArgs": {
    "param": "value"
  }
}
```

## 📊 Status

- **Working:** 12/13 connected (92.3%)
- **Last Tested:** 2025-12-19
- **All Core Functionality:** ✅ Operational

---

For detailed documentation, see individual files in `Working/` directory.
