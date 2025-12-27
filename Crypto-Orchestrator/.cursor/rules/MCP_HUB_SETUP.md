# MCP Hub Setup Guide

> **Current Date**: December 11, 2025  
> **Last Updated**: 2025-12-11

## Overview

MCP Hub is the recommended solution for managing multiple MCP servers in Cursor. It bypasses the 40-tool limit by exposing only 2-3 tools while providing access to all 150+ tools from all configured servers.

## Configuration Files

### Main Configuration (`~/.cursor/mcp.json`)
Contains only the MCP Hub entry:

```json
{
  "mcpServers": {
    "mcp-hub": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-hub-mcp",
        "--config-path",
        "C:\\Users\\William Walker\\.cursor\\mcp-hub.json"
      ]
    }
  }
}
```

### Server Configuration (`~/.cursor/mcp-hub.json`)
Contains all individual MCP server configurations that MCP Hub will manage:

```json
{
  "mcpServers": {
    "filesystem": { ... },
    "git": { ... },
    "github": { ... },
    "context7": { ... },
    "memory-bank": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory-bank"],
      "env": {
        "MEMORY_BANK_PATH": "C:\\Users\\William Walker\\.cursor\\memory-bank"
      }
    },
    // ... all other servers
  }
}
```

## Environment Variables

Required environment variables are set in the project's `.env` file:

- `GITHUB_TOKEN` - GitHub Personal Access Token
- `DATABASE_URL` - PostgreSQL connection string
- `SENTRY_DSN`, `SENTRY_AUTH_TOKEN` - Sentry error tracking
- `RENDER_API_KEY` - Render deployment
- `CONTEXT7_API_KEY` - Context7 documentation
- `BRAVE_API_KEY` - Brave Search
- `COINGECKO_API_KEY` - CoinGecko prices
- `USER_PRIVATE_KEY`, `USER_ADDRESS`, `ALCHEMY_API_KEY` - DeFi Trading (optional)
- `MEMORY_BANK_PATH` - Memory-Bank storage path (optional, defaults to `~/.cursor/memory-bank`)

## Python MCP Modules

Install required Python packages:

```bash
pip install mcp-server-sqlite arxiv-search-mcp
```

**Module Names:**
- SQLite: `mcp_server_sqlite` (not `mcp_sqlite_manager`)
- ArXiv: `arxiv_search_mcp` (not `mcp_arxiv_query`)

## Memory-Bank MCP (Recommended)

Memory-Bank MCP allows the agent to store and retrieve important decisions, patterns, and learnings:

**Configuration** (add to `~/.cursor/mcp-hub.json`):
```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory-bank"],
      "env": {
        "MEMORY_BANK_PATH": "C:\\Users\\William Walker\\.cursor\\memory-bank"
      }
    }
  }
}
```

**Usage**:
- Store architectural decisions
- Remember why patterns were chosen
- Track trade-offs and learnings
- Build knowledge base over time

**Benefits**:
- Persistent memory across sessions
- Searchable knowledge base
- Context-aware decision making
- Improved agent intelligence

## Setup Steps

1. **Configure MCP Hub** in `~/.cursor/mcp.json` (only mcp-hub entry)
2. **Configure all servers** in `~/.cursor/mcp-hub.json`
3. **Set environment variables** in project `.env` file
4. **Install Python modules** if using SQLite or ArXiv MCP
5. **Enable MCP Hub** in Cursor Settings > Tools & MCP
6. **Disable all individual servers** in Cursor Settings
7. **Restart Cursor** completely

## Using MCP Hub Tools

Access all MCP servers through MCP Hub's tools:

```typescript
// List all available tools
list-all-tools()

// Call a tool from any server
call-tool(
  serverName: "coingecko",
  toolName: "get_price",
  toolArgs: { symbol: "BTC" }
)

// Get tool information
get-tool-info(serverName: "git", toolName: "git_status")
```

## Benefits

- ✅ Bypasses 40-tool limit (exposes only 2-3 tools)
- ✅ Works immediately with npx (no binary downloads)
- ✅ All 150+ tools accessible through hub
- ✅ Centralized configuration management
- ✅ Automatic tool routing

## Troubleshooting

- **High tool count**: Make sure individual servers are disabled in Cursor Settings
- **Server not found**: Check `mcp-hub.json` configuration and environment variables
- **Python module errors**: Verify `mcp-server-sqlite` and `arxiv-search-mcp` are installed
- **Environment variables**: Ensure `.env` file has all required variables set
