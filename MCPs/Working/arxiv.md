# ArXiv MCP

**Status:** ✅ Working  
**Server:** arxiv  
**Tools:** 2 tools

## Available Tools

1. `search_papers` - Search papers with pagination
2. `get_paper` - Get detailed paper information

## Usage Example

```json
{
  "serverName": "arxiv",
  "toolName": "search_papers",
  "toolArgs": {
    "query": "machine learning",
    "max_results": 1
  }
}
```

## Features

- Search academic papers
- Pagination support
- Detailed paper information
- PDF URL access
- Author and category information

## Paper Information

Each paper includes:
- ID (arXiv ID)
- Title
- Summary
- Authors
- Published/Updated dates
- PDF URL
- Categories
- DOI (if available)

## Notes

- Results sorted by submission date (newest first)
- Supports pagination for large result sets
- Can get full paper details by ID
- Python module: `arxiv_search_mcp`
