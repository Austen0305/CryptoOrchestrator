# Cursor MCP Handling Capabilities & Limits

**Last Updated:** January 3, 2026

## ✅ **IMPORTANT: mcp-hub Changes Everything!**

**You're absolutely right!** When using `mcp-hub`, the limitations are **completely different**:

### How `mcp-hub` Works (On-Demand Pattern)

1. **MCPs are configured, not active** - All 35 MCPs can be configured in `mcp-hub.json`
2. **On-demand invocation** - MCPs are only called when specifically requested
3. **No simultaneous loading** - Tools aren't all loaded at once
4. **No 40-tool limit issue** - Only the called MCP's tools are available per request
5. **Reduced token usage** - Only the called MCP's tool descriptions are included

### Usage Pattern:
```json
{
  "serverName": "evm-mcp-server",  // Only this MCP is called
  "toolName": "get_balance",
  "toolArgs": { "address": "0x..." }
}
```

---

## ⚠️ Limitations (Only Apply to Direct MCP Connections)

**Note:** These limitations only apply if you connect MCPs **directly to Cursor**, not via `mcp-hub`:

### 1. **40 Tools Per Session Limit** (Direct Connections Only)
If you connect MCPs directly to Cursor (not via mcp-hub), there's a hard limit of 40 tools per session.

**This does NOT apply when using mcp-hub** because:
- MCPs are called on-demand
- Only one MCP's tools are active per call
- No simultaneous tool loading

### 2. **High Input Token Usage** (Direct Connections Only)
When MCPs are connected directly, Cursor includes all tool descriptions in every request.

**With mcp-hub:** Only the called MCP's tool descriptions are included, significantly reducing token usage.

### 3. **Connection Management Issues** (Direct Connections Only)
Direct connections can open excessive simultaneous connections.

**With mcp-hub:** Connections are made on-demand, only when an MCP is called.

### 4. **Connection State Not Retained** (Direct Connections Only)
Direct MCP connections need reconfiguration after restart.

**With mcp-hub:** Configuration is stored in `mcp-hub.json` and persists across restarts.

---

## ✅ What Cursor CAN Handle with mcp-hub

### **All 35 MCPs - No Problem!**

When using `mcp-hub`, you can configure **all 35 MCPs** without issues:

✅ **No 40-tool limit** - Tools are called on-demand, not all loaded at once  
✅ **Low token usage** - Only called MCP's tools are included  
✅ **On-demand connections** - Connections made only when needed  
✅ **Persistent configuration** - All MCPs configured in `mcp-hub.json`  
✅ **No performance issues** - Only active MCP uses resources  

### Your Current Setup (17 MCPs via mcp-hub)
- **Status:** ✅ Working perfectly
- **Recommendation:** Add all 35 MCPs to `mcp-hub.json` - they'll only be used when called

---

## 🎯 Strategic Approach for Your 35 MCPs (via mcp-hub)

### ✅ **Recommended: Configure All 35 MCPs**

Since `mcp-hub` uses on-demand invocation, you should:

1. **Configure all 35 MCPs** in `mcp-hub.json`
2. **Call them as needed** - The agent will use the right MCP for each task
3. **No performance penalty** - Unused MCPs consume no resources

### Option 1: **Configure All MCPs (Best Practice)**
Add all 35 MCPs to your `mcp-hub.json`:

1. **Filesystem** ✅ (14 tools) - Essential
2. **Git** ✅ (27 tools) - Essential  
3. **EVM MCP Server** ⭐ (Blockchain - HIGH PRIORITY)
4. **PostgreSQL MCP** ⭐ (Database - HIGH PRIORITY)
5. **Redis MCP** ⭐ (Cache - HIGH PRIORITY)
6. **Docker MCP** ⭐ (Containers - HIGH PRIORITY)
7. **GitHub MCP** ⭐ (Version Control - HIGH PRIORITY)
8. **Context7** ✅ (Documentation - Already working)
9. **CoinGecko** ✅ (Crypto prices - Already working)
10. **API Tester** ✅ (Testing - Already working)

**Result:** All 35 MCPs available on-demand, no performance impact

### Option 2: **Prioritize by Usage** (Optional)
If you want to be selective, configure MCPs in order of priority:

**High Priority (Configure First):**
- Filesystem, Git, EVM MCP Server, PostgreSQL, Redis, Docker, GitHub

**Medium Priority:**
- Context7, CoinGecko, API Tester, Kubernetes, Stripe

**Low Priority (Add Later):**
- Everything else

**Note:** With mcp-hub, there's no penalty for configuring all 35, so this is optional.

---

## 📊 Tool Count Analysis (via mcp-hub)

### Your 35 MCPs Tool Breakdown:

| Category | MCPs | Estimated Tools | Status with mcp-hub |
|----------|------|----------------|---------------------|
| **Core Utilities** | 5 | ~60 tools | ✅ All available on-demand |
| **Database** | 3 | ~15 tools | ✅ All available on-demand |
| **Blockchain** | 2 | ~20 tools | ✅ All available on-demand |
| **Development** | 2 | ~10 tools | ✅ All available on-demand |
| **Research** | 6 | ~20 tools | ✅ All available on-demand |
| **Deployment** | 2 | ~10 tools | ✅ All available on-demand |
| **Testing** | 1 | ~8 tools | ✅ All available on-demand |
| **Kubernetes** | 1 | ~15 tools | ✅ All available on-demand |
| **Redis** | 1 | ~10 tools | ✅ All available on-demand |
| **Package Mgmt** | 2 | ~8 tools | ✅ All available on-demand |
| **Code Search** | 1 | ~5 tools | ✅ All available on-demand |
| **GitHub** | 1 | ~15 tools | ✅ All available on-demand |
| **Sentry** | 1 | ~5 tools | ✅ All available on-demand |
| **Stripe** | 1 | ~10 tools | ✅ All available on-demand |
| **Other** | 5 | ~15 tools | ✅ All available on-demand |

**Total Estimated:** ~200+ tools  
**With mcp-hub:** ✅ **All tools accessible** - called on-demand, no limits!

---

## 💡 Recommendations (via mcp-hub)

### ✅ DO:
1. **Configure all 35 MCPs** - No performance penalty with mcp-hub
2. **Let the agent choose** - It will call the right MCP for each task
3. **Organize by category** - Group related MCPs in `mcp-hub.json` for easier management
4. **Test incrementally** - Add MCPs in batches to verify configuration
5. **Document your setup** - Keep notes on which MCPs you use most

### ❌ DON'T:
1. **Don't worry about limits** - mcp-hub handles on-demand invocation
2. **Don't manually activate/deactivate** - mcp-hub does this automatically
3. **Don't duplicate MCPs** - Each MCP should be configured once
4. **Don't forget API keys** - Ensure all required keys are in `env` sections

---

## 🔧 Practical Implementation

### Step 1: Identify Your Core MCPs
Based on your CryptoOrchestrator project, prioritize:

**Must Have (Always Active):**
- Filesystem, Git, EVM MCP Server, PostgreSQL, Redis

**Should Have (Activate as needed):**
- Docker, GitHub, CoinGecko, Context7, API Tester

**Nice to Have (On-demand):**
- Everything else

### Step 2: Create MCP Profiles
Create different `mcp-hub.json` configurations:

- `mcp-hub.core.json` - Essential MCPs only
- `mcp-hub.development.json` - Development-focused
- `mcp-hub.blockchain.json` - Blockchain-focused
- `mcp-hub.full.json` - All MCPs (for reference)

### Step 3: Monitor and Optimize
- Check Cursor's connection count
- Monitor token usage
- Track which MCPs you actually use
- Adjust your active set accordingly

---

## 📈 Performance Impact (via mcp-hub)

### With All 35 MCPs Configured:
- ✅ **Excellent performance** - Only called MCP uses resources
- ✅ **Low token usage** - Only called MCP's tools included
- ✅ **On-demand connections** - Connections made only when needed
- ✅ **No tool limits** - All tools accessible on-demand
- ✅ **Persistent config** - All MCPs configured once in `mcp-hub.json`

### Key Advantage:
**mcp-hub = On-Demand Architecture**
- Configured MCPs consume **zero resources** until called
- Only the **actively called MCP** uses tokens/connections
- **No simultaneous loading** = No performance degradation

---

## 🎯 Final Answer

**Can Cursor handle all 35 MCPs via mcp-hub?**
- **Yes! Absolutely!** ✅
- **No limits** - All 35 MCPs can be configured
- **No performance issues** - On-demand invocation means zero overhead
- **All tools accessible** - No 40-tool limit with mcp-hub

**Best Approach:**
1. **Configure all 35 MCPs** in `mcp-hub.json`
2. **Let the agent use them** - It will call the right MCP for each task
3. **No manual management** - mcp-hub handles everything automatically
4. **Enjoy unlimited tools** - All ~200+ tools available on-demand

**Your Current Status:**
- You have 17 MCPs configured via mcp-hub ✅
- **You can safely add all 35** - No performance penalty
- **All tools will be accessible** - Called on-demand as needed
- **No limits to worry about** - mcp-hub handles everything

---

## 📚 Resources

- [Cursor Forum - Tool Limits](https://forum.cursor.com/t/tools-limited-to-40-total/67976)
- [Cursor Forum - Connection Issues](https://forum.cursor.com/t/cursor-makes-way-too-many-simultaneous-connections-to-mcp-servers/135969)
- [Cursor Forum - Token Usage](https://forum.cursor.com/t/high-input-token-usage-when-many-mcp-servers-are-connected-mcp-connection-state-not-retained-on-restart/142547)
