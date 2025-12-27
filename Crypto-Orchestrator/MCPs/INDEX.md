# MCP Index - Quick Lookup

## 📚 All Working MCPs

### Core Services
| MCP | Server Name | Tools | Status | Documentation |
|-----|------------|-------|--------|---------------|
| Filesystem | `filesystem` | 14 | ✅ | [filesystem.md](Working/filesystem.md) |
| Git | `git` | 27 | ✅ | [git.md](Working/git.md) |
| Context7 | `context7` | 2 | ✅ | [context7.md](Working/context7.md) |
| StackOverflow | `stackoverflow` | 6 | ✅ | [stackoverflow.md](Working/stackoverflow.md) |
| Brave Search | `brave-search` | 2 | ✅ | [brave-search.md](Working/brave-search.md) |
| CoinGecko | `coingecko` | Multiple | ✅ | [coingecko.md](Working/coingecko.md) |

### Browser Automation
| MCP | Server Name | Tools | Status | Documentation |
|-----|------------|-------|--------|---------------|
| Puppeteer | `puppeteer` | 7 | ✅ | [puppeteer.md](Working/puppeteer.md) |
| Browser Extension | `cursor-browser-extension` | 18 | ✅ | [cursor-browser-extension.md](Working/cursor-browser-extension.md) |

### AI & Knowledge
| MCP | Server Name | Tools | Status | Documentation |
|-----|------------|-------|--------|---------------|
| Memory | `memory` | 9 | ✅ | [memory.md](Working/memory.md) |
| Sequential Thinking | `sequential-thinking` | 1 | ✅ | [sequential-thinking.md](Working/sequential-thinking.md) |

### Research
| MCP | Server Name | Tools | Status | Documentation |
|-----|------------|-------|--------|---------------|
| ArXiv | `arxiv` | 2 | ✅ | [arxiv.md](Working/arxiv.md) |
| AllThingsDev | `allthingsdev` | 6 | ✅ | [allthingsdev.md](Working/allthingsdev.md) |

## 🔍 How to Use

### Via user-mcp-hub:
```json
{
  "serverName": "SERVER_NAME",
  "toolName": "tool_name",
  "toolArgs": {}
}
```

### Direct (browser extension):
```json
{
  "server": "cursor-browser-extension",
  "toolName": "browser_navigate",
  "arguments": {
    "url": "https://example.com"
  }
}
```

## 📖 Documentation

Each MCP has detailed documentation in `Working/` directory with:
- Available tools
- Usage examples
- Parameters
- Notes and tips

## 🚀 Quick Start

1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for server names
2. Read individual MCP docs in `Working/` for details
3. See `Examples/` for code samples

---

**Total Working:** 12 MCPs  
**Last Updated:** 2025-12-19
