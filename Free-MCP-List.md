# Complete Free MCP Servers List for Cursor

**Last Updated:** January 3, 2026  
**Source:** [cursor.directory/mcp](https://cursor.directory/mcp)  
**Focus:** Completely free MCPs only (no tiers, no trials, no credit card required) OR permanent free tiers (forever free, not time-limited)

---

## 🔌 MCP-Hub Compatibility

**All 35 MCPs in this list are compatible with `mcp-hub`**, but they require different setup approaches:

### ✅ **Direct Compatibility (18 MCPs)**
These work directly via `mcp-hub` discovery/registry:
- All **Official MCP Servers** (Filesystem, Git, Fetch, Time, Everything, Memory, Sequential Thinking, Puppeteer, SQLite, Sentry)
- **Context7, StackOverflow, Brave Search, ArXiv, AllThingsDev** (already working)
- **CoinGecko, Render, API Tester** (already working)
- **TypeScript Definition Finder** (already working)

### ⚙️ **Requires Manual Configuration (17 MCPs)**
These need to be added to `C:\Users\William Walker\.cursor\mcp-hub.json`:

1. **PostgreSQL MCP** - Requires `command` and `args` pointing to PostgreSQL connection
2. **MCP DB Utils** - Requires database connection string in `env`
3. **Docker MCP** - Requires Docker CLI access
4. **Stripe MCP** - Requires Stripe API key in `env`
5. **Graphfied Documentation Search** - Standard npx installation
6. **Endgame MCP** - Standard npx installation
7. **Kubernetes MCP Server** - Requires kubectl access and cluster config
8. **Redis MCP Server** - Requires Redis connection string in `env`
9. **NPM Search MCP Server** - Standard npx installation
10. **Package Registry MCP** - Standard npx installation
11. **EVM MCP Server** ⭐ - Standard npx installation (HIGH PRIORITY)
12. **Elastic Semantic Code Search** - Requires codebase indexing setup
13. **PyPI Query MCP Server** - Standard npx installation
14. **Coinbase AgentKit MCP** - Standard npm package installation
15. **GitHub MCP Server** ⭐ - Requires GitHub token in `env`

**Note:** All of these follow the standard MCP protocol and will work with `mcp-hub` once properly configured in your `mcp-hub.json` file.

---

## 📋 Quick Reference Table

| Category | Count | Key MCPs |
|----------|-------|----------|
| **Core Utilities** | 5 | Filesystem, Git, Fetch, Time, Everything |
| **AI & Knowledge** | 2 | Memory, Sequential Thinking |
| **Browser Automation** | 1 | Puppeteer |
| **Database** | 3 | PostgreSQL, MCP DB Utils, SQLite |
| **Development Tools** | 2 | TypeScript Finder, Docker |
| **API & Services** | 1 | Stripe |
| **Research & Documentation** | 6 | Context7, StackOverflow, Brave Search, ArXiv, AllThingsDev, Graphfied |
| **Cryptocurrency** | 1 | CoinGecko |
| **Deployment** | 2 | Render, Endgame |
| **Testing & Quality** | 1 | API Tester |
| **Kubernetes & Containers** | 1 | Kubernetes (Official) |
| **Cache & Data Stores** | 1 | Redis (Official) |
| **Package Management** | 2 | NPM Search, Package Registry |
| **Blockchain** | 2 | EVM MCP Server ⭐, Coinbase AgentKit |
| **Code Search** | 1 | Elastic Semantic Code Search |
| **Package Intelligence** | 1 | PyPI Query |
| **GitHub Integration** | 1 | GitHub MCP Server |

**Total:** 35 Practical Free MCPs for CryptoOrchestrator | **Your Current:** 17 Installed | **Recommended:** 8-10 More

---

## 🎯 Official Model Context Protocol Servers (100% Free & Open Source)

These are the official reference servers from the [ModelContextProtocol/servers](https://github.com/modelcontextprotocol/servers) repository. All are MIT licensed and completely free.

### Core Utilities

1. **Filesystem MCP** ✅ (Already Installed)
   - **Server Name:** `filesystem`
   - **Description:** Secure file operations with configurable access controls
   - **Tools:** 14 tools (read, write, list, search files)
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

2. **Git MCP** ✅ (Already Installed)
   - **Server Name:** `git`
   - **Description:** Read, search, and manipulate Git repositories
   - **Tools:** 27 tools (commit, diff, blame, log, etc.)
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/git
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

3. **Fetch MCP** ✅ (Already Installed)
   - **Server Name:** `fetch`
   - **Description:** Web content fetching and conversion (HTML to markdown)
   - **Tools:** Fetch URLs, convert HTML to markdown
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/fetch
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

4. **Time MCP** ✅ (Already Installed)
   - **Server Name:** `time`
   - **Description:** Time and timezone conversion capabilities
   - **Tools:** Time conversion, timezone utilities
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/time
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

5. **Everything MCP** ✅ (Already Installed)
   - **Server Name:** `everything`
   - **Description:** Test server with prompts, resources, and tools
   - **Tools:** Various test tools
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/everything
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

### AI & Knowledge

6. **Memory MCP** ✅ (Already Installed)
   - **Server Name:** `memory`
   - **Description:** Knowledge graph-based persistent memory system
   - **Tools:** 9 tools (store, retrieve, search memories)
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/memory
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

7. **Sequential Thinking MCP** ✅ (Already Installed)
   - **Server Name:** `sequential-thinking`
   - **Description:** Dynamic and reflective problem-solving through thought sequences
   - **Tools:** 1 tool (sequential thinking process)
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/sequential-thinking
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility

### Browser Automation

8. **Puppeteer MCP** ✅ (Already Installed)
   - **Server Name:** `puppeteer`
   - **Description:** Browser automation capabilities for web interaction
   - **Tools:** 7 tools (navigate, screenshot, execute JavaScript)
   - **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer
   - **Status:** Free, open source, MIT license
   - **mcp-hub:** ✅ Direct compatibility


### Database

10. **PostgreSQL MCP**
    - **Server Name:** `postgresql`
    - **Description:** Read-only access to PostgreSQL databases
    - **Tools:** Inspect schemas, execute read-only queries
    - **URL:** https://cursor.directory/mcp/postgresql
    - **Status:** Free, open source
    - **Note:** Perfect for your project since you use PostgreSQL!
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` with PostgreSQL connection string

11. **MCP DB Utils**
    - **Server Name:** `mcp-db-utils`
    - **Description:** All-in-one database access for SQLite, MySQL, PostgreSQL, and more
    - **Tools:** Unified database connection and data analysis
    - **URL:** https://cursor.directory/mcp/mcp-db-utils
    - **Status:** Free, open source
    - **Note:** Supports multiple database types including PostgreSQL!
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` with database connection string

### Development Tools

11. **TypeScript Definition Finder** ✅ (Already Installed)
    - **Server Name:** `typescript-definition-finder`
    - **Description:** Find TypeScript symbol definitions in codebase
    - **Tools:** 1 tool (find definitions)
    - **Status:** Free, open source
    - **mcp-hub:** ✅ Direct compatibility

12. **Docker MCP**
    - **Server Name:** `docker`
    - **Description:** Manage containers, images, volumes, and networks
    - **Tools:** Docker management tools
    - **URL:** https://cursor.directory/mcp/docker
    - **Status:** Free, open source
    - **Note:** Great for your Docker Compose setup!
    - **mcp-hub:** ⚙️ Requires Docker CLI access and config in `mcp-hub.json`


### API & Services

23. **Stripe MCP**
    - **Server Name:** `stripe`
    - **Description:** Interact with the Stripe API
    - **Tools:** Stripe API operations
    - **URL:** https://cursor.directory/mcp/stripe
    - **Status:** Free (requires Stripe account, but MCP is free)
    - **Note:** You already use Stripe in your project!
    - **mcp-hub:** ⚙️ Requires Stripe API key in `env` section of `mcp-hub.json`


### Research & Documentation

26. **Context7 MCP** ✅ (Already Installed)
    - **Server Name:** `context7`
    - **Description:** Library documentation search
    - **Tools:** 2 tools (resolve library ID, query docs)
    - **Status:** Free (API key required, but service is free)
    - **mcp-hub:** ✅ Direct compatibility

27. **StackOverflow MCP** ✅ (Already Installed)
    - **Server Name:** `stackoverflow`
    - **Description:** Search StackOverflow questions and answers
    - **Tools:** 6 tools (search by tags, get questions, etc.)
    - **Status:** Free (uses StackOverflow API, free tier available)
    - **mcp-hub:** ✅ Direct compatibility

28. **Brave Search MCP** ✅ (Already Installed)
    - **Server Name:** `brave-search`
    - **Description:** Web search using Brave Search API
    - **Tools:** 2 tools (web search, local search)
    - **Status:** Free (API key required, free tier available)
    - **mcp-hub:** ✅ Direct compatibility

29. **ArXiv MCP** ✅ (Already Installed)
    - **Server Name:** `arxiv`
    - **Description:** Search academic papers on arXiv
    - **Tools:** 2 tools (search papers, get paper details)
    - **Status:** Free, open source
    - **mcp-hub:** ✅ Direct compatibility

30. **AllThingsDev MCP** ✅ (Already Installed)
    - **Server Name:** `allthingsdev`
    - **Description:** API marketplace search
    - **Tools:** 6 tools (search APIs, get pricing, etc.)
    - **Status:** Free
    - **mcp-hub:** ✅ Direct compatibility

31. **Graphfied Documentation Search MCP**
    - **Server Name:** `graphfied-documentation-search`
    - **Description:** Retrieve latest Python library documentation from LangChain, LlamaIndex, OpenAI
    - **Tools:** Documentation search and extraction
    - **URL:** https://cursor.directory/mcp/graphfied-documentation-search
    - **Status:** Free, open source
    - **Note:** Great for Python/FastAPI documentation lookup!
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (standard npx installation)

### Cryptocurrency

29. **CoinGecko MCP** ✅ (Already Installed)
    - **Server Name:** `coingecko`
    - **Description:** Cryptocurrency price data and market information
    - **Tools:** Multiple tools (prices, markets, exchanges, etc.)
    - **Status:** Free (API key required, free tier available)
    - **Note:** Perfect for your crypto trading platform!
    - **mcp-hub:** ✅ Direct compatibility

### Deployment

33. **Render MCP** ✅ (Already Installed)
    - **Server Name:** `render`
    - **Description:** Render.com deployment and management
    - **Tools:** 3 tools (create services, query Postgres, get metrics)
    - **Status:** Free tier available (requires Render account)
    - **mcp-hub:** ✅ Direct compatibility

34. **Endgame MCP**
    - **Server Name:** `endgame`
    - **Description:** Deployment superpowers for Cursor (Fast + Self-healing + Free)
    - **Tools:** Deployment tools
    - **URL:** https://cursor.directory/mcp/endgame
    - **Website:** https://endgame.dev
    - **Status:** Free (as advertised: "Fast + Self-healing + Free")
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (standard npx installation)

### Testing & Quality

32. **API Tester MCP** ✅ (Already Installed)
    - **Server Name:** `api-tester`
    - **Description:** API testing and load testing from OpenAPI specs
    - **Tools:** 8 tools (ingest spec, generate tests, run tests, load testing)
    - **Status:** Free, open source
    - **Note:** Excellent for your FastAPI project!
    - **mcp-hub:** ✅ Direct compatibility


### Kubernetes & Container Orchestration

74. **Kubernetes MCP Server (Official)**
    - **Server Name:** `kubernetes-mcp-server`
    - **Description:** Standardized protocol for managing Kubernetes and OpenShift clusters
    - **Tools:** Kubernetes operations, multi-cluster support, read-only mode
    - **GitHub:** https://github.com/containers/kubernetes-mcp-server
    - **Status:** Free, open source (Apache-2.0 license)
    - **Note:** Official containers project - supports AWS EKS, Google GKE, Azure AKS
    - **mcp-hub:** ⚙️ Requires kubectl access and cluster config in `mcp-hub.json`


### Cache & Data Stores

76. **Redis MCP Server (Official)**
    - **Server Name:** `mcp-redis`
    - **Description:** Natural language interface for managing and searching data in Redis
    - **Tools:** Support for strings, hashes, lists, sets, sorted sets, streams, JSON documents
    - **GitHub:** https://github.com/redis/mcp-redis
    - **Status:** Free, open source (official Redis Ltd.)
    - **Note:** Perfect for your Redis cache setup!
    - **mcp-hub:** ⚙️ Requires Redis connection string in `env` section of `mcp-hub.json`


### Package Management

78. **NPM Search MCP Server**
    - **Server Name:** `npm-search-mcp-server`
    - **Description:** Search for npm packages by calling npm search command
    - **Tools:** NPM package search
    - **GitHub:** https://github.com/btwiuse/npm-search-mcp-server
    - **Status:** Free, open source
    - **Note:** Search npm packages directly from MCP
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (standard npx installation)

79. **Package Registry MCP**
    - **Server Name:** `package-registry-mcp`
    - **Description:** Search package registries and retrieve up-to-date information
    - **Tools:** Search NPM, Cargo, PyPI, and NuGet packages
    - **GitHub:** https://github.com/artmann/package-registry-mcp
    - **Status:** Free, open source
    - **Note:** Multi-registry package search
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (standard npx installation)


### Blockchain & Cryptocurrency

64. **EVM MCP Server** ⭐⭐⭐ (HIGHEST PRIORITY FOR YOUR PROJECT)
    - **Server Name:** `evm-mcp-server`
    - **Description:** Blockchain services across 60+ EVM-compatible networks (Ethereum, Optimism, Arbitrum, Base, Polygon, etc.)
    - **Tools:** Unified interface for EVM chains
    - **GitHub:** https://github.com/mcpdotdirect/evm-mcp-server
    - **Status:** Free, open source
    - **Note:** Perfect for your DEX trading platform! Supports all major EVM chains
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (standard npx installation)


### Additional Database Options

94. **SQLite MCP** (Official)
    - **Server Name:** `sqlite`
    - **Description:** Database interaction and business intelligence capabilities
    - **Tools:** SQLite database operations
    - **GitHub:** https://github.com/modelcontextprotocol/servers (official)
    - **Status:** Free, open source (official MCP server)
    - **Note:** Official reference server from ModelContextProtocol
    - **mcp-hub:** ✅ Direct compatibility

### Error Tracking & Monitoring

87. **Sentry MCP** (Official)
    - **Server Name:** `sentry`
    - **Description:** Retrieve and analyze issues from Sentry.io
    - **Tools:** Sentry issue management and analysis
    - **GitHub:** https://github.com/modelcontextprotocol/servers (official)
    - **Status:** Free, open source (official MCP server)
    - **Note:** Official reference server - requires Sentry account (free tier available permanently)
    - **mcp-hub:** ✅ Direct compatibility


### Code Search & Analysis

101. **Elastic Semantic Code Search MCP Server**
    - **Server Name:** `semantic-code-search-mcp-server`
    - **Description:** Semantic code search - exposes indexed data for AI coding agents to interact with codebase
    - **Tools:** Semantic code search, codebase interaction
    - **GitHub:** https://github.com/elastic/semantic-code-search-mcp-server
    - **Status:** Free, open source (Apache 2.0 license)
    - **Note:** Official Elastic project - ML models for code understanding
    - **mcp-hub:** ⚙️ Requires codebase indexing setup and config in `mcp-hub.json`


### Package Intelligence

105. **PyPI Query MCP Server**
    - **Server Name:** `pypi-query-mcp-server`
    - **Description:** Python package intelligence - structured queries for PyPI packages and GitHub repositories
    - **Tools:** PyPI package queries, GitHub repository queries
    - **URL:** https://mcp.so/server/pypi-query-mcp-server
    - **Status:** Free, open source
    - **Note:** Python package and repository intelligence
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (standard npx installation)


### Blockchain & Cryptocurrency (Additional)

110. **Coinbase AgentKit MCP**
    - **Server Name:** `@coinbase/agentkit-model-context-protocol`
    - **Description:** MCP extension of Coinbase's AgentKit - interact with on-chain actions
    - **Tools:** Blockchain functionalities, on-chain operations
    - **NPM:** `@coinbase/agentkit-model-context-protocol`
    - **Status:** Free, open source
    - **Note:** Requires Node.js 18+, agentic workflows for blockchain
    - **mcp-hub:** ⚙️ Requires config in `mcp-hub.json` (npm package installation)

### GitHub Integration

65. **GitHub MCP Server** ⭐⭐⭐ (HIGH PRIORITY)
    - **Server Name:** `github-mcp-server`
    - **Description:** Official GitHub integration - manage issues, PRs, repositories, workflows
    - **Tools:** Repository management, issue tracking, pull requests, GitHub Actions
    - **GitHub:** https://github.com/github/github-mcp-server
    - **Status:** Free, open source (official GitHub)
    - **Note:** Perfect for your GitHub Actions workflows and repository management!
    - **mcp-hub:** ⚙️ Requires GitHub token in `env` section of `mcp-hub.json`


---

## ⚠️ MCPs with Paid Tiers (Not Included)

These MCPs require paid accounts or have limited free tiers:

- **Mailtrap Email Sending** - Requires Mailtrap account (paid service)
- **Postmark MCP** - Requires Postmark account (paid service)
- **Midday** - Requires API key from paid service
- **GibsonAI** - Requires paid account
- **Statsig** - Requires paid account
- **Agent Evals by Galileo** - Requires paid account
- **Atono** - Requires paid account
- **Pearl** - Human expert service (paid)
- **Google Ads MCP** - Requires Google Ads account (paid service)
- **Infobip** - Requires Infobip account (paid service)

---

## 📊 Summary

### Already Installed (17 MCPs)
- ✅ All official ModelContextProtocol servers you have
- ✅ Context7, StackOverflow, Brave Search
- ✅ CoinGecko, ArXiv, AllThingsDev
- ✅ Render, API Tester, TypeScript Definition Finder

### Recommended Additional Free MCPs for Your Project

Based on your CryptoOrchestrator project needs:

1. **EVM MCP Server** ⭐⭐⭐ (HIGHEST PRIORITY - CRYPTO PROJECT)
   - Blockchain services for 60+ EVM networks
   - Perfect for your DEX trading platform
   - Supports Ethereum, Optimism, Arbitrum, Base, Polygon, etc.
   - **GitHub:** https://github.com/mcpdotdirect/evm-mcp-server
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json`

2. **PostgreSQL MCP** ⭐⭐⭐ (HIGH PRIORITY)
   - Perfect for your PostgreSQL database
   - Read-only queries and schema inspection
   - **URL:** https://cursor.directory/mcp/postgresql
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` with connection string

3. **MCP DB Utils** ⭐⭐⭐ (HIGH PRIORITY)
   - Unified database access (PostgreSQL, MySQL, SQLite)
   - Data analysis capabilities
   - Perfect for your multi-database needs
   - **URL:** https://cursor.directory/mcp/mcp-db-utils
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` with connection string

4. **Redis MCP Server (Official)** ⭐⭐⭐ (HIGH PRIORITY)
   - Natural language interface for Redis
   - Perfect for your Redis cache setup
   - Official Redis Ltd. server
   - **GitHub:** https://github.com/redis/mcp-redis
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` with Redis connection string

5. **Docker MCP** ⭐⭐⭐ (HIGH PRIORITY)
   - Manage your Docker containers
   - Perfect for docker-compose setup
   - **URL:** https://cursor.directory/mcp/docker
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` (requires Docker CLI)

6. **Kubernetes MCP Server** ⭐⭐⭐ (HIGH PRIORITY)
   - Manage Kubernetes clusters
   - Perfect if you deploy to K8s
   - **GitHub:** https://github.com/containers/kubernetes-mcp-server
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` (requires kubectl)

7. **GitHub MCP Server** ⭐⭐⭐ (HIGH PRIORITY)
   - Official GitHub integration
   - Perfect for your GitHub Actions workflows
   - **GitHub:** https://github.com/github/github-mcp-server
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` with GitHub token

8. **Stripe MCP** ⭐⭐ (MEDIUM PRIORITY)
   - You already use Stripe
   - Manage payments and subscriptions
   - **URL:** https://cursor.directory/mcp/stripe
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json` with Stripe API key

9. **Graphfied Documentation Search** ⭐⭐ (MEDIUM PRIORITY)
   - Python/FastAPI documentation lookup
   - Great for backend development
   - **URL:** https://cursor.directory/mcp/graphfied-documentation-search
   - **mcp-hub:** ⚙️ Add to `mcp-hub.json`

10. **Sentry MCP** ⭐ (LOW PRIORITY)
    - Error tracking and monitoring
    - You already use Sentry SDK
    - **GitHub:** https://github.com/modelcontextprotocol/servers (official)
    - **mcp-hub:** ✅ Direct compatibility

---

## 🔗 Installation Resources

- **Official MCP Servers:** https://github.com/modelcontextprotocol/servers
- **Cursor Directory:** https://cursor.directory/mcp
- **MCP Registry:** https://github.com/modelcontextprotocol/registry
- **MCP Hub Documentation:** Check your `mcp-hub.json` config file

## 📝 Notes

1. **Free Tier vs Completely Free:**
   - Some MCPs require accounts with free tiers (e.g., Cloudflare, Neon, Mapbox, ConfigCat)
   - These are marked as "Free tier available" or "Free tier permanent"
   - Only included if free tier is permanent (not time-limited)
   - Truly free MCPs require no account at all

2. **API Keys:**
   - Some free MCPs require API keys (e.g., Context7, Brave Search, CoinGecko)
   - These are still free - you just need to get the API key
   - Free tiers are usually generous and permanent

3. **Open Source:**
   - All official MCP servers are open source (MIT, Apache-2.0, AGPL-3.0 licenses)
   - You can self-host or modify them
   - Most community servers are also open source

4. **Your Current Setup:**
   - You already have 17 excellent free MCPs installed
   - Focus on adding EVM MCP Server, PostgreSQL, MCP DB Utils, Docker, Redis, and GitHub MCPs

5. **MCP Registry:**
   - Official MCP Registry: https://github.com/modelcontextprotocol/registry
   - Community-maintained directory of available servers
   - Regularly updated with new free MCP servers
   - MCP Registry API: https://registry.modelcontextprotocol.io/v0/servers

6. **Additional Resources:**
   - MCPKit: https://www.mcpkit.com (1,185+ servers)
   - Open MCP Directory: https://www.openmcpdirectory.com (3,919+ servers)
   - MCP Index: https://mcpindex.net (real-time updates)
   - MCPHub: https://mcphub.com (curated directory)

7. **Security Note:**
   - Always review MCP server source code before installing
   - Some malicious MCP servers have been found on PyPI/npm
   - Prefer official or well-maintained servers with many stars/contributors

8. **mcp-hub Compatibility:**
   - ✅ **18 MCPs** work directly via mcp-hub discovery
   - ⚙️ **17 MCPs** require manual configuration in `mcp-hub.json`
   - All 35 MCPs are compatible - they just need proper setup
   - Configuration examples available in your existing `mcp-hub.json`

---

**Last Updated:** January 3, 2026  
**Total Free MCPs Listed:** 35 (Filtered specifically for CryptoOrchestrator project - only practical, relevant MCPs that you can actually use)  
**Your Current MCPs:** 17 installed  
**Recommended to Add:** 8-10 more (EVM MCP Server, PostgreSQL, MCP DB Utils, Docker, GitHub, Redis, Kubernetes, Sentry, Elastic Semantic Code Search)
