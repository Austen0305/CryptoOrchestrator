# CoinGecko MCP

**Status:** ✅ Working  
**Server:** coingecko  
**Tools:** Multiple crypto tools

## Available Tools

Various cryptocurrency price and market data tools.

## Usage

Check available tools via:
```json
{
  "serverName": "user-mcp-hub",
  "toolName": "list-all-tools-in-server",
  "toolArgs": {
    "serverName": "coingecko"
  }
}
```

## Features

- Cryptocurrency prices
- Market data
- Historical data
- Pro features available with API key

## Notes

- Basic features work without API key
- Pro features require `COINGECKO_API_KEY`
- API key optional for basic usage
