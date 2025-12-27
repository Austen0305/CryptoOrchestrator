# MCP Troubleshooting Quick Reference

> **Quick fixes for common MCP connection issues**

## 🚨 Immediate Fixes

### Connection Timeout Errors

**Symptom**: `ETIMEDOUT`, `Connection timeout`, `Request timeout`

**Quick Fix**:
1. Add timeout configuration to `mcp.json`:
```json
{
  "mcpServers": {
    "mcp-hub": {
      "command": "cmd",
      "args": [
        "/c", "npx", "-y", "mcp-hub-mcp",
        "--timeout", "30000"
      ]
    }
  }
}
```

2. Restart Cursor completely

### "Client Closed" Errors (Windows)

**Symptom**: `Client Closed`, `Connection closed unexpectedly`

**Quick Fix**:
Add `cmd /c` prefix to all `npx` commands in `mcp.json`:
```json
{
  "command": "cmd",
  "args": ["/c", "npx", "-y", "mcp-hub-mcp", ...]
}
```

### Server Not Found Errors

**Symptom**: `Server not found`, `MCP server unavailable`

**Quick Fix**:
1. Check `mcp-hub.json` has the server configured
2. Verify environment variables are set in `.env`
3. Test server independently:
```bash
npx -y @modelcontextprotocol/server-github
```

### Too Many Tools Error

**Symptom**: `Tool limit exceeded`, `40 tool limit`

**Quick Fix**:
1. Ensure only `mcp-hub` is enabled in Cursor Settings
2. Disable all individual MCP servers
3. Use MCP Hub tools: `list-all-tools`, `call-tool`, `get-tool-info`

### Authentication Errors

**Symptom**: `401 Unauthorized`, `Invalid token`, `Authentication failed`

**Quick Fix**:
1. Check `.env` file has correct API keys
2. Verify tokens haven't expired
3. Regenerate tokens if needed
4. Move credentials to `.env.mcp` (not in `mcp.json`)

## 🔍 Diagnostic Steps

### Step 1: Check Cursor Developer Console
1. Open: `Help → Toggle Developer Tools → Console`
2. Look for MCP-related errors
3. Note error messages and timestamps

### Step 2: Validate Configuration
```bash
# Check mcp.json syntax
cat ~/.cursor/mcp.json | python -m json.tool

# Check mcp-hub.json syntax
cat ~/.cursor/mcp-hub.json | python -m json.tool
```

### Step 3: Test MCP Server Directly
```bash
# Test GitHub MCP
npx -y @modelcontextprotocol/server-github

# Test CoinGecko MCP
npx -y @coingecko/mcp-server

# Test Web3 MCP
npx -y @strangelove-ventures/web3-mcp
```

### Step 4: Check Environment Variables
```bash
# Windows PowerShell
Get-ChildItem Env: | Where-Object { $_.Name -like "*GITHUB*" -or $_.Name -like "*MCP*" }

# Linux/Mac
env | grep -E "(GITHUB|MCP|DATABASE|COINGECKO)"
```

## 🛠️ Common Solutions

### Solution 1: Restart Everything
1. Close Cursor completely
2. Restart Cursor
3. Wait 30 seconds for MCP servers to initialize
4. Try again

### Solution 2: Clear MCP Cache
```bash
# Windows
rmdir /s /q "%USERPROFILE%\.cursor\mcp-cache"

# Linux/Mac
rm -rf ~/.cursor/mcp-cache
```

### Solution 3: Reinstall MCP Hub
```bash
npm uninstall -g mcp-hub-mcp
npm install -g mcp-hub-mcp
```

### Solution 4: Reduce Active Servers
1. Open Cursor Settings → Tools & MCP
2. Disable unused MCP servers
3. Keep only essential servers active
4. Restart Cursor

### Solution 5: Update Node.js
```bash
# Check version
node --version  # Should be 18+

# Update if needed
# Windows: Download from nodejs.org
# Mac: brew upgrade node
# Linux: Use nvm
```

## 📋 Pre-Flight Checklist

Before reporting issues, verify:

- [ ] Node.js 18+ installed
- [ ] Cursor is latest version
- [ ] Only `mcp-hub` enabled in Cursor Settings
- [ ] All individual servers disabled
- [ ] `mcp.json` has only `mcp-hub` entry
- [ ] `mcp-hub.json` has all server configs
- [ ] `.env` file has all required variables
- [ ] No syntax errors in JSON files
- [ ] Windows: Using `cmd /c` prefix
- [ ] Restarted Cursor after changes

## 🔗 Full Documentation

For comprehensive solutions, see:
- **`.cursor/rules/CURSOR_AGENT_OPTIMIZATION.md`** - Complete optimization guide
- **`.cursor/rules/MCP_HUB_SETUP.md`** - Setup instructions
- **`docs/MCP_SETUP_GUIDE.md`** - Detailed configuration

## 📞 Still Having Issues?

1. Check Cursor Developer Console for detailed errors
2. Review `.cursor/rules/CURSOR_AGENT_OPTIMIZATION.md` for advanced solutions
3. Verify all prerequisites are met
4. Test MCP servers independently
5. Check for Cursor updates

---

**Remember**: Most connection issues are resolved by:
1. ✅ Using `cmd /c` on Windows
2. ✅ Restarting Cursor completely
3. ✅ Validating configuration files
4. ✅ Checking environment variables
5. ✅ Using MCP Hub (not individual servers)
