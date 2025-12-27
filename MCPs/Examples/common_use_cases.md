# Common MCP Use Cases

Quick examples for common tasks using working MCPs.

## 🔍 Search & Research

### Search the Web
```json
{
  "serverName": "brave-search",
  "toolName": "brave_web_search",
  "toolArgs": {
    "query": "your search query",
    "count": 10
  }
}
```

### Search StackOverflow
```json
{
  "serverName": "stackoverflow",
  "toolName": "search_questions",
  "toolArgs": {
    "query": "python async",
    "limit": 5
  }
}
```

### Search Academic Papers
```json
{
  "serverName": "arxiv",
  "toolName": "search_papers",
  "toolArgs": {
    "query": "machine learning",
    "max_results": 10
  }
}
```

### Find Library Documentation
```json
{
  "serverName": "context7",
  "toolName": "resolve-library-id",
  "toolArgs": {
    "libraryName": "react"
  }
}
```

## 📁 File Operations

### Read a File
```json
{
  "serverName": "filesystem",
  "toolName": "read_text_file",
  "toolArgs": {
    "path": "path/to/file.txt"
  }
}
```

### List Directory
```json
{
  "serverName": "filesystem",
  "toolName": "list_directory",
  "toolArgs": {
    "path": "path/to/directory"
  }
}
```

### Write a File
```json
{
  "serverName": "filesystem",
  "toolName": "write_file",
  "toolArgs": {
    "path": "path/to/file.txt",
    "contents": "file content here"
  }
}
```

## 🔧 Git Operations

### Check Status
```json
{
  "serverName": "git",
  "toolName": "git_status",
  "toolArgs": {
    "path": "C:\\Users\\William Walker\\OneDrive\\Desktop\\CryptoOrchestrator\\Crypto-Orchestrator"
  }
}
```

### View Commit History
```json
{
  "serverName": "git",
  "toolName": "git_log",
  "toolArgs": {
    "path": "C:\\Users\\William Walker\\OneDrive\\Desktop\\CryptoOrchestrator\\Crypto-Orchestrator",
    "limit": 10
  }
}
```

## 🌐 Browser Automation

### Navigate to URL
```json
{
  "serverName": "cursor-browser-extension",
  "toolName": "browser_navigate",
  "toolArgs": {
    "url": "https://example.com"
  }
}
```

### Take Screenshot
```json
{
  "serverName": "cursor-browser-extension",
  "toolName": "browser_take_screenshot",
  "toolArgs": {}
}
```

### Get Page Snapshot
```json
{
  "serverName": "cursor-browser-extension",
  "toolName": "browser_snapshot",
  "toolArgs": {}
}
```

## 🧠 Knowledge & AI

### Store Knowledge
```json
{
  "serverName": "memory",
  "toolName": "create_entities",
  "toolArgs": {
    "entities": [
      {
        "name": "Project X",
        "description": "A crypto trading platform"
      }
    ]
  }
}
```

### Search Knowledge
```json
{
  "serverName": "memory",
  "toolName": "search_nodes",
  "toolArgs": {
    "query": "crypto trading"
  }
}
```

### Sequential Thinking
```json
{
  "serverName": "sequential-thinking",
  "toolName": "sequentialthinking",
  "toolArgs": {
    "thought": "How to optimize API performance?",
    "nextThoughtNeeded": true,
    "thoughtNumber": 1,
    "totalThoughts": 5,
    "isRevision": false
  }
}
```

## 📊 API Marketplace

### List API Categories
```json
{
  "serverName": "allthingsdev",
  "toolName": "list_api_categories",
  "toolArgs": {}
}
```

### Search APIs
```json
{
  "serverName": "allthingsdev",
  "toolName": "search_apis",
  "toolArgs": {
    "keywords": "payment"
  }
}
```

---

**Note:** All examples use the `user-mcp-hub` server except `cursor-browser-extension` which is called directly.
