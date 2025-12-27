# Brave Search MCP

**Status:** ✅ Working  
**Server:** brave-search  
**Tools:** 2 tools  
**API Key:** ✅ Configured

## Available Tools

1. `brave_web_search` - Web search (general queries, news, articles)
2. `brave_local_search` - Local business/place search

## Usage Example

```json
{
  "serverName": "brave-search",
  "toolName": "brave_web_search",
  "toolArgs": {
    "query": "test",
    "count": 1
  }
}
```

## Features

- Web search with pagination (max 20 results per request)
- Local business search with ratings and reviews
- Content filtering and freshness controls
- Automatic fallback from local to web search

## API Key

- **Location:** `mcp-hub.json` line 51
- **Status:** ✅ Working
- **Format:** `BSAzjlwu9t2Hh8uuexDDJR-8I9uge9r`
- **Plan:** Free AI (2,000 queries/month)

## Notes

- Use `brave_web_search` for general queries
- Use `brave_local_search` for location-based queries
- Supports pagination with offset parameter
