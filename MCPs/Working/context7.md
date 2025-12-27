# Context7 MCP

**Status:** ✅ Working  
**Server:** context7  
**Tools:** 2 tools  
**API Key:** ✅ Configured

## Available Tools

1. `resolve-library-id` - Resolve package name to Context7 library ID
2. `get-library-docs` - Fetch library documentation

## Usage Example

```json
{
  "serverName": "context7",
  "toolName": "resolve-library-id",
  "toolArgs": {
    "libraryName": "react"
  }
}
```

## Features

- Resolves library names to Context7-compatible IDs
- Returns library metadata (snippets, reputation, benchmark scores)
- Fetches up-to-date documentation
- Supports code examples and API references

## API Key

- **Location:** `mcp-hub.json` line 34
- **Status:** ✅ Working
- **Format:** `ctx7sk-4887ae1b-7ba4-4b29-8ca1-7dfc726c744f`

## Notes

- Must call `resolve-library-id` before `get-library-docs`
- Returns multiple matching libraries with quality scores
- Prioritizes libraries with high reputation and snippet coverage
