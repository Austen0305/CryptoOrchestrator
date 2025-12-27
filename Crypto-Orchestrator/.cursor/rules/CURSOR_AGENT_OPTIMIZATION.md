# Cursor Agent Optimization Guide

> **Current Date**: December 11, 2025  
> **Last Updated**: 2025-12-11  
> **Purpose**: Reduce connection issues and improve Cursor agent stability

## 🎯 Overview

This guide provides comprehensive strategies to minimize MCP server connection issues and optimize Cursor agent performance based on 2025 best practices and research findings.

## 🔧 Connection Issue Prevention Strategies

### 1. MCP Hub Configuration Optimization

#### Current Setup (Verified)
- **MCP Hub**: Configured in `~/.cursor/mcp.json` (only mcp-hub entry)
- **Server Config**: All servers in `~/.cursor/mcp-hub.json`
- **Tool Limit**: Bypassed via MCP Hub (exposes only 2-3 tools, routes to 150+)

#### Recommended Improvements

**1.1 Add Connection Timeouts**
```json
{
  "mcpServers": {
    "mcp-hub": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-hub-mcp",
        "--config-path",
        "C:\\Users\\William Walker\\.cursor\\mcp-hub.json",
        "--timeout", "30000",
        "--retry-attempts", "3",
        "--retry-delay", "1000"
      ],
      "env": {
        "MCP_HUB_TIMEOUT": "30000",
        "MCP_HUB_MAX_RETRIES": "3",
        "MCP_HUB_RETRY_DELAY": "1000"
      }
    }
  }
}
```

**1.2 Windows-Specific Fixes**
For Windows systems, use `cmd /c` prefix to prevent "Client Closed" errors:

```json
{
  "mcpServers": {
    "mcp-hub": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-hub-mcp",
        "--config-path",
        "C:\\Users\\William Walker\\.cursor\\mcp-hub.json"
      ]
    }
  }
}
```

**1.3 Separate Credentials from Configuration**
Store sensitive credentials in `.env.mcp` file (not in `mcp.json`):

```bash
# .env.mcp (gitignored)
GITHUB_TOKEN=your_token_here
DATABASE_URL=postgresql://...
COINGECKO_API_KEY=your_key_here
```

Reference in `mcp-hub.json`:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### 2. Retry Strategies with Exponential Backoff

#### Implementation Pattern

**2.1 Exponential Backoff with Jitter**
```typescript
// Retry configuration for MCP calls
const retryConfig = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
  jitter: true // Add randomness to prevent thundering herd
};

// Retry logic
async function callMCPWithRetry(serverName, toolName, toolArgs) {
  let attempt = 0;
  let delay = retryConfig.initialDelay;
  
  while (attempt < retryConfig.maxRetries) {
    try {
      return await callTool(serverName, toolName, toolArgs);
    } catch (error) {
      if (error.isRetryable && attempt < retryConfig.maxRetries - 1) {
        const jitter = retryConfig.jitter 
          ? Math.random() * 0.3 * delay 
          : 0;
        await sleep(delay + jitter);
        delay = Math.min(delay * retryConfig.backoffMultiplier, retryConfig.maxDelay);
        attempt++;
      } else {
        throw error;
      }
    }
  }
}
```

**2.2 Protocol-Specific Retries**

**For SSE (Server-Sent Events) Backend Servers:**
- Re-establish connection on failure
- Use exponential backoff
- Maximum timeout: 30 seconds

**For HTTP Backend Servers:**
- Retry on connection errors
- Retry on 5xx status codes
- Don't retry on 4xx (client errors)

**For Stdio Backend Servers:**
- Restart process on failure
- Exponential backoff between restarts
- Maximum restart attempts: 3

### 3. Connection Health Monitoring

#### 3.1 Health Check Pattern

```typescript
// MCP server health check
async function checkMCPHealth(serverName: string): Promise<boolean> {
  try {
    const result = await callTool(serverName, "health_check", {});
    return result.status === "healthy";
  } catch (error) {
    logger.warn(`MCP server ${serverName} health check failed: ${error.message}`);
    return false;
  }
}

// Periodic health checks
setInterval(async () => {
  const servers = ["coingecko", "web3", "github", "postgres"];
  for (const server of servers) {
    const isHealthy = await checkMCPHealth(server);
    if (!isHealthy) {
      logger.error(`MCP server ${server} is unhealthy`);
      // Optionally: restart server or mark as unavailable
    }
  }
}, 60000); // Check every minute
```

#### 3.2 Connection Pooling

For frequently used MCP servers, implement connection pooling:

```typescript
class MCPConnectionPool {
  private pools: Map<string, Connection[]> = new Map();
  private maxConnections = 5;
  
  async getConnection(serverName: string): Promise<Connection> {
    if (!this.pools.has(serverName)) {
      this.pools.set(serverName, []);
    }
    
    const pool = this.pools.get(serverName)!;
    
    // Return existing connection if available
    const available = pool.find(c => c.isAvailable);
    if (available) {
      return available;
    }
    
    // Create new connection if under limit
    if (pool.length < this.maxConnections) {
      const connection = await this.createConnection(serverName);
      pool.push(connection);
      return connection;
    }
    
    // Wait for connection to become available
    return this.waitForConnection(serverName);
  }
}
```

### 4. Error Handling Best Practices

#### 4.1 Consistent Error Propagation

```typescript
// Standard error response format
interface MCPError {
  code: string;
  message: string;
  details?: any;
  retryable: boolean;
  serverName: string;
  toolName: string;
}

// Error handling wrapper
async function handleMCPError(error: any, serverName: string, toolName: string): Promise<MCPError> {
  const mcpError: MCPError = {
    code: error.code || "UNKNOWN_ERROR",
    message: error.message || "Unknown error occurred",
    details: error.details,
    retryable: isRetryableError(error),
    serverName,
    toolName
  };
  
  // Log error with context
  logger.error("MCP call failed", {
    serverName,
    toolName,
    error: mcpError,
    timestamp: new Date().toISOString()
  });
  
  return mcpError;
}

function isRetryableError(error: any): boolean {
  // Retry on network errors, timeouts, 5xx errors
  const retryableCodes = ["ECONNREFUSED", "ETIMEDOUT", "ENOTFOUND"];
  return retryableCodes.includes(error.code) || 
         (error.status >= 500 && error.status < 600);
}
```

#### 4.2 Graceful Degradation

```typescript
// Fallback pattern for critical operations
async function callMCPWithFallback(
  primaryServer: string,
  fallbackServers: string[],
  toolName: string,
  toolArgs: any
) {
  try {
    return await callTool(primaryServer, toolName, toolArgs);
  } catch (error) {
    logger.warn(`Primary MCP server ${primaryServer} failed, trying fallbacks`);
    
    for (const fallback of fallbackServers) {
      try {
        return await callTool(fallback, toolName, toolArgs);
      } catch (fallbackError) {
        logger.warn(`Fallback server ${fallback} also failed`);
        continue;
      }
    }
    
    throw new Error(`All MCP servers failed for ${toolName}`);
  }
}
```

### 5. MCP Server Selection Strategy

#### 5.1 Prioritize Official Servers

Only use MCP servers from:
- Official MCP directory: https://cursor.directory/mcp
- Trusted GitHub repositories (modelcontextprotocol organization)
- Verified community servers with good track records

#### 5.2 Disable Unused Servers

**Rule**: If you're not actively using an MCP server, disable it to:
- Reduce memory usage
- Reduce credit consumption
- Minimize connection overhead
- Lower error surface area

**Checklist**:
- [ ] Review all enabled MCP servers
- [ ] Disable servers not used in last 30 days
- [ ] Keep only essential servers active
- [ ] Document why each server is needed

#### 5.3 Server Grouping Strategy

Group related servers and enable/disable as groups:

```json
{
  "serverGroups": {
    "crypto": ["coingecko", "web3", "defi-trading"],
    "development": ["context7", "stackoverflow", "brave-search"],
    "infrastructure": ["postgres", "redis", "docker"],
    "optional": ["arxiv", "sentry", "render"]
  }
}
```

### 6. Configuration Validation

#### 6.1 Pre-Flight Checks

```typescript
// Validate MCP configuration before use
async function validateMCPConfig() {
  const issues: string[] = [];
  
  // Check required environment variables
  const requiredEnvVars = {
    "github": ["GITHUB_TOKEN"],
    "postgres": ["DATABASE_URL"],
    "coingecko": ["COINGECKO_API_KEY"],
    "sentry": ["SENTRY_DSN", "SENTRY_AUTH_TOKEN"]
  };
  
  for (const [server, vars] of Object.entries(requiredEnvVars)) {
    for (const envVar of vars) {
      if (!process.env[envVar]) {
        issues.push(`Missing ${envVar} for ${server} server`);
      }
    }
  }
  
  // Check server accessibility
  const servers = ["coingecko", "web3", "github"];
  for (const server of servers) {
    try {
      await checkMCPHealth(server);
    } catch (error) {
      issues.push(`Server ${server} is not accessible: ${error.message}`);
    }
  }
  
  if (issues.length > 0) {
    throw new Error(`MCP configuration issues:\n${issues.join("\n")}`);
  }
}
```

#### 6.2 Configuration Schema Validation

```json
{
  "$schema": "https://json.schemastore.org/mcp-config.json",
  "mcpServers": {
    "mcp-hub": {
      "type": "object",
      "required": ["command", "args"],
      "properties": {
        "command": { "type": "string" },
        "args": { "type": "array", "items": { "type": "string" } },
        "env": { "type": "object" }
      }
    }
  }
}
```

### 7. Performance Optimization

#### 7.1 Request Deduplication

```typescript
// Deduplicate identical MCP requests
class MCPRequestCache {
  private cache: Map<string, Promise<any>> = new Map();
  private ttl: number = 5000; // 5 seconds
  
  async getCached(serverName: string, toolName: string, toolArgs: any): Promise<any> {
    const key = `${serverName}:${toolName}:${JSON.stringify(toolArgs)}`;
    
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }
    
    const promise = callTool(serverName, toolName, toolArgs);
    this.cache.set(key, promise);
    
    // Remove from cache after TTL
    setTimeout(() => this.cache.delete(key), this.ttl);
    
    return promise;
  }
}
```

#### 7.2 Batch Requests

```typescript
// Batch multiple MCP calls together
async function batchMCPCalls(requests: Array<{server: string, tool: string, args: any}>): Promise<any[]> {
  const promises = requests.map(req => 
    callTool(req.server, req.tool, req.args)
  );
  
  return Promise.allSettled(promises).then(results => 
    results.map((result, index) => {
      if (result.status === "fulfilled") {
        return result.value;
      } else {
        logger.error(`Batch request ${index} failed: ${result.reason}`);
        return null;
      }
    })
  );
}
```

### 8. Monitoring and Logging

#### 8.1 Connection Metrics

```typescript
// Track MCP connection metrics
interface MCPMetrics {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  averageLatency: number;
  lastError?: string;
  lastErrorTime?: Date;
}

class MCPMetricsCollector {
  private metrics: Map<string, MCPMetrics> = new Map();
  
  recordCall(serverName: string, success: boolean, latency: number, error?: string) {
    if (!this.metrics.has(serverName)) {
      this.metrics.set(serverName, {
        totalCalls: 0,
        successfulCalls: 0,
        failedCalls: 0,
        averageLatency: 0
      });
    }
    
    const metric = this.metrics.get(serverName)!;
    metric.totalCalls++;
    
    if (success) {
      metric.successfulCalls++;
    } else {
      metric.failedCalls++;
      metric.lastError = error;
      metric.lastErrorTime = new Date();
    }
    
    // Update average latency (exponential moving average)
    metric.averageLatency = (metric.averageLatency * 0.9) + (latency * 0.1);
  }
  
  getMetrics(serverName: string): MCPMetrics | undefined {
    return this.metrics.get(serverName);
  }
  
  getHealthScore(serverName: string): number {
    const metric = this.metrics.get(serverName);
    if (!metric || metric.totalCalls === 0) return 1.0;
    
    const successRate = metric.successfulCalls / metric.totalCalls;
    const latencyScore = metric.averageLatency < 1000 ? 1.0 : 0.5;
    
    return successRate * latencyScore;
  }
}
```

#### 8.2 Structured Logging

```typescript
// Structured logging for MCP operations
logger.info("MCP call initiated", {
  serverName: "coingecko",
  toolName: "get_price",
  toolArgs: { symbol: "BTC" },
  timestamp: new Date().toISOString(),
  requestId: generateRequestId()
});

logger.error("MCP call failed", {
  serverName: "coingecko",
  toolName: "get_price",
  error: error.message,
  errorCode: error.code,
  retryable: isRetryableError(error),
  timestamp: new Date().toISOString(),
  requestId: requestId
});
```

### 9. Troubleshooting Checklist

#### 9.1 Connection Issues

- [ ] **Check MCP server is running**: Verify server process is active
- [ ] **Verify credentials**: Check API keys and tokens are valid
- [ ] **Check network connectivity**: Test connection to MCP server endpoint
- [ ] **Review Cursor logs**: Check Developer Console for errors
- [ ] **Restart Cursor**: Completely quit and relaunch Cursor
- [ ] **Validate configuration**: Check `mcp.json` and `mcp-hub.json` syntax
- [ ] **Check environment variables**: Ensure all required env vars are set
- [ ] **Test server independently**: Run MCP server outside Cursor to verify it works

#### 9.2 Performance Issues

- [ ] **Check server health**: Use health check endpoints
- [ ] **Review metrics**: Check success rates and latency
- [ ] **Disable unused servers**: Reduce active MCP servers
- [ ] **Check rate limits**: Verify you're not hitting API rate limits
- [ ] **Review connection pooling**: Ensure connections are reused
- [ ] **Check for memory leaks**: Monitor memory usage over time

#### 9.3 Windows-Specific Issues

- [ ] **Use `cmd /c` prefix**: Add `cmd /c` before `npx` commands
- [ ] **Check path separators**: Use backslashes for Windows paths
- [ ] **Verify Node.js installation**: Ensure Node.js is in PATH
- [ ] **Check antivirus**: Ensure antivirus isn't blocking MCP servers
- [ ] **Run as administrator**: If permission issues occur

### 10. Recommended Configuration Template

#### 10.1 Optimized `mcp.json`

```json
{
  "$schema": "https://json.schemastore.org/mcp-config.json",
  "mcpServers": {
    "mcp-hub": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-hub-mcp",
        "--config-path",
        "C:\\Users\\William Walker\\.cursor\\mcp-hub.json",
        "--timeout", "30000",
        "--retry-attempts", "3",
        "--retry-delay", "1000",
        "--health-check-interval", "60000"
      ],
      "env": {
        "MCP_HUB_TIMEOUT": "30000",
        "MCP_HUB_MAX_RETRIES": "3",
        "MCP_HUB_RETRY_DELAY": "1000",
        "MCP_HUB_HEALTH_CHECK": "true"
      }
    }
  }
}
```

#### 10.2 Optimized `mcp-hub.json` (Essential Servers Only)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\path\\to\\project"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@cyanheads/git-mcp-server", "--repository", "C:\\path\\to\\project"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "memory-bank": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory-bank"],
      "env": {
        "MEMORY_BANK_PATH": "C:\\Users\\William Walker\\.cursor\\memory-bank"
      }
    },
    "coingecko": {
      "command": "npx",
      "args": ["-y", "@coingecko/mcp-server"],
      "env": {
        "COINGECKO_API_KEY": "${COINGECKO_API_KEY}"
      }
    },
    "web3": {
      "command": "npx",
      "args": ["-y", "@strangelove-ventures/web3-mcp"],
      "env": {
        "ETH_RPC_URL": "${ETH_RPC_URL}",
        "BASE_RPC_URL": "${BASE_RPC_URL}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

### 11. Agent Behavior Rules

#### 11.1 MCP Tool Usage Guidelines

**DO:**
- ✅ Use MCP Hub tools (`list-all-tools`, `call-tool`, `get-tool-info`)
- ✅ Implement retry logic with exponential backoff
- ✅ Cache frequently accessed data
- ✅ Use health checks before critical operations
- ✅ Log all MCP operations with context
- ✅ Handle errors gracefully with fallbacks

**DON'T:**
- ❌ Don't call MCP tools directly (use MCP Hub)
- ❌ Don't retry on non-retryable errors (4xx client errors)
- ❌ Don't ignore connection errors
- ❌ Don't make redundant calls (use caching)
- ❌ Don't skip error handling
- ❌ Don't use deprecated MCP servers

#### 11.2 Connection Error Handling

```typescript
// Recommended error handling pattern
async function safeMCPCall(serverName: string, toolName: string, toolArgs: any) {
  try {
    // Health check first
    const isHealthy = await checkMCPHealth(serverName);
    if (!isHealthy) {
      throw new Error(`MCP server ${serverName} is unhealthy`);
    }
    
    // Call with retry
    return await callMCPWithRetry(serverName, toolName, toolArgs);
  } catch (error) {
    // Log error
    logger.error("MCP call failed", {
      serverName,
      toolName,
      error: error.message,
      retryable: isRetryableError(error)
    });
    
    // Try fallback if available
    if (hasFallback(serverName)) {
      return await tryFallback(serverName, toolName, toolArgs);
    }
    
    // Re-throw if no fallback
    throw error;
  }
}
```

### 12. Maintenance Schedule

#### 12.1 Weekly Checks

- [ ] Review MCP server health metrics
- [ ] Check for MCP server updates
- [ ] Review error logs for patterns
- [ ] Validate environment variables
- [ ] Test critical MCP integrations

#### 12.2 Monthly Reviews

- [ ] Audit enabled MCP servers (disable unused)
- [ ] Review connection performance metrics
- [ ] Update MCP server versions
- [ ] Review and update credentials
- [ ] Check for security advisories

#### 12.3 Quarterly Audits

- [ ] Full configuration review
- [ ] Performance optimization review
- [ ] Security audit of MCP servers
- [ ] Documentation updates
- [ ] Disaster recovery testing

## 📊 Success Metrics

Track these metrics to measure improvement:

- **Connection Success Rate**: Target > 99%
- **Average Latency**: Target < 500ms
- **Error Rate**: Target < 1%
- **Retry Success Rate**: Target > 80%
- **Health Check Pass Rate**: Target 100%

## 🔗 References

- [MCP Specification](https://modelcontextprotocol.io/specification/latest/)
- [Cursor MCP Directory](https://cursor.directory/mcp)
- [MCP Hub Documentation](https://github.com/modelcontextprotocol/hub)
- [Cursor Troubleshooting Guide](https://docs.cursor.com/troubleshooting)

---

**Remember**: Connection stability is achieved through:
1. ✅ Proper configuration (timeouts, retries)
2. ✅ Health monitoring and proactive checks
3. ✅ Graceful error handling and fallbacks
4. ✅ Regular maintenance and updates
5. ✅ Using only essential, trusted MCP servers
