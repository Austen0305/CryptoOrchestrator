# MCP Servers Integration with Cursor

**Status**: ✅ 12 Working MCP Servers Configured  
**Date**: December 30, 2025

---

## Overview

CryptoOrchestrator has **12 working MCP (Model Context Protocol) servers** configured through **MCP Hub** that enhance Cursor's AI capabilities.

**Location**: `MCPs/` directory  
**Configuration**: `~/.cursor/mcp-hub.json` (MCP Hub configuration)  
**Access**: All MCPs accessed via `mcp-hub` server (not individual servers)

---

## Available MCP Servers

### Core Services (6)

| MCP | Server Name | Tools | Use Case |
|-----|------------|-------|----------|
| **Filesystem** | `filesystem` | 14 | File operations (read, write, list, search) |
| **Git** | `git` | 27 | Git operations (status, commit, push, etc.) |
| **Context7** | `context7` | 2 | Library documentation search |
| **StackOverflow** | `stackoverflow` | 6 | Find solutions to common problems |
| **Brave Search** | `brave-search` | 2 | Web search for current information |
| **CoinGecko** | `coingecko` | Multiple | Cryptocurrency price data |

### Browser Automation (2)

| MCP | Server Name | Tools | Use Case |
|-----|------------|-------|----------|
| **Puppeteer** | `puppeteer` | 7 | Browser automation for testing |
| **Browser Extension** | `cursor-browser-extension` | 18 | Browser interaction and testing |

### AI & Knowledge (2)

| MCP | Server Name | Tools | Use Case |
|-----|------------|-------|----------|
| **Memory** | `memory` | 9 | Knowledge graph and persistent memory |
| **Sequential Thinking** | `sequential-thinking` | 1 | Complex problem solving |

### Research (2)

| MCP | Server Name | Tools | Use Case |
|-----|------------|-------|----------|
| **ArXiv** | `arxiv` | 2 | Academic paper search |
| **AllThingsDev** | `allthingsdev` | 6 | API marketplace and tools |

---

## How to Use MCP Servers

### All MCPs via MCP Hub

**Important**: All MCPs are accessed through the **MCP Hub** server, not individually.

**Access Pattern**:
```json
{
  "serverName": "mcp-hub",
  "toolName": "call-tool",
  "toolArgs": {
    "serverName": "SERVER_NAME",
    "toolName": "tool_name",
    "toolArgs": {
      "param": "value"
    }
  }
}
```

**Example**: Access filesystem MCP
```json
{
  "serverName": "mcp-hub",
  "toolName": "call-tool",
  "toolArgs": {
    "serverName": "filesystem",
    "toolName": "read_text_file",
    "toolArgs": {
      "path": "server_fastapi/main.py"
    }
  }
}
```

### Browser Extension (Direct Access)

The browser extension is accessed directly (not via MCP Hub):

```json
{
  "server": "cursor-browser-extension",
  "toolName": "browser_navigate",
  "arguments": {
    "url": "https://example.com"
  }
}
```

---

## Common Use Cases

### File Operations
**Use**: `filesystem` MCP
- Read files: `read_text_file`
- Write files: `write_file`
- List directories: `list_directory`
- Search files: `search_files`

**Instead of**: Terminal commands like `cat`, `ls`, `grep`

### Git Operations
**Use**: `git` MCP
- Check status: `git_status`
- Commit changes: `git_commit`
- View history: `git_log`
- Branch operations: `git_branch`

**Instead of**: Terminal git commands

### Documentation Search
**Use**: `context7` MCP
- Find library docs: `resolve-library-id`
- Search documentation: `search-documentation`

**For**: React, FastAPI, Python library documentation

### Problem Solving
**Use**: `stackoverflow` MCP
- Search questions: `search_questions`
- Get solutions: `get_question_details`

**For**: Common coding problems and solutions

### Web Search
**Use**: `brave-search` MCP
- Search web: `brave_search`

**For**: Current information and research

### Crypto Data
**Use**: `coingecko` MCP
- Get prices: Various price endpoints
- Market data: Market information

**For**: Cryptocurrency price data and market information

---

## Configuration

### MCP Hub Configuration

**Location**: `~/.cursor/mcp-hub.json`  
**Status**: ✅ 12 servers configured and working  
**Access**: All MCPs accessed via `mcp-hub` server

**Setup**:
1. Open Cursor Settings → Features → MCP
2. Enable **only** `mcp-hub` server
3. **Disable all individual MCP servers** (to avoid 40-tool limit)
4. Restart Cursor

**See**: [MCP Hub Setup Guide](./MCP_HUB_SETUP.md) for detailed setup instructions

**Important**: 
- Enable **only** `mcp-hub` in Cursor Settings → Features → MCP
- Disable all individual MCP servers (to avoid 40-tool limit)
- All MCPs are accessed through the hub, not individually

### API Keys

**Configured**:
- Context7: `ctx7sk-4887ae1b-7ba4-4b29-8ca1-7dfc726c744f`
- Brave Search: `BSAzjlwu9t2Hh8uuexDDJR-8I9uge9r`

**Location**: Stored in MCP Hub configuration file (`~/.cursor/mcp-hub.json`)

---

## Integration with Cursor

### Automatic Usage

The AI agent automatically uses MCP servers via MCP Hub when:
- File operations are needed (filesystem via mcp-hub)
- Git operations are needed (git via mcp-hub)
- Documentation lookup is needed (context7 via mcp-hub)
- Web search is needed (brave-search via mcp-hub)
- Problem solving is needed (stackoverflow via mcp-hub)

**Note**: The agent uses `mcp-hub` to call individual MCP servers automatically.

### Manual Usage

You can explicitly request MCP usage:
- "Search Stack Overflow for React Query patterns"
- "Find FastAPI documentation for dependency injection"
- "Get current Bitcoin price from CoinGecko"

---

## Documentation

### Quick Reference
- **[MCP Quick Reference](../../MCPs/QUICK_REFERENCE.md)** - Quick lookup guide
- **[MCP Index](../../MCPs/INDEX.md)** - Complete index of all MCPs

### Detailed Documentation
- **[MCP README](../../MCPs/README.md)** - Complete MCP documentation
- **[Working Directory](../../MCPs/Working/)** - Individual MCP guides
- **[Examples](../../MCPs/Examples/)** - Usage examples

---

## Best Practices

1. **Use MCPs Instead of Terminal**: Prefer MCP tools over terminal commands
2. **Leverage Documentation Search**: Use context7 for library documentation
3. **Use Memory for Context**: Store important patterns in memory MCP
4. **Search Before Asking**: Use stackoverflow MCP for common problems
5. **Web Search for Current Info**: Use brave-search for up-to-date information

---

## Troubleshooting

### MCP Not Working

1. **Check MCP Hub Enabled**: Settings → Features → MCP → Enable `mcp-hub`
2. **Disable Individual Servers**: Disable all individual MCP servers (use hub only)
3. **Check Configuration**: Verify `~/.cursor/mcp-hub.json` exists
4. **Restart Cursor**: Full restart sometimes needed
5. **Check API Keys**: Verify API keys are configured in mcp-hub.json

### MCP Not Available

1. **Check Server Status**: Some MCPs may be temporarily unavailable
2. **Check Documentation**: See `MCPs/Working/` for server-specific issues
3. **Use Alternative**: Some operations can be done manually

---

## Summary

✅ **12 Working MCP Servers** configured in **MCP Hub** and ready to use:
- Core services (filesystem, git, context7, etc.)
- Browser automation (puppeteer, browser extension)
- AI & knowledge (memory, sequential-thinking)
- Research (arxiv, allthingsdev)

**Access**: All MCPs accessed via `mcp-hub` server (not individually)

**Setup**:
1. Enable **only** `mcp-hub` in Cursor Settings → Features → MCP
2. Disable all individual MCP servers (to avoid 40-tool limit)
3. All MCPs automatically accessible through the hub

**Status**: ✅ Fully operational and integrated with Cursor

**See**: [MCP Documentation](../../MCPs/README.md) for complete details
