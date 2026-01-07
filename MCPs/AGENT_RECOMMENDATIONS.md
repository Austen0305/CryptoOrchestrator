# Agent-Recommended MCPs for CryptoOrchestrator

Based on a fresh scan of your codebase (as of Jan 2026), I have identified the most critical MCP servers that would allow **me** (your AI agent) to most effectively assist you with development, debugging, and orchestration.

These are filtered from your broader lists to focus on what is **technically relevant** to your current code state (ignoring removed dependencies like Stripe).

## 🚨 Critical Priority (Must Haves)

These enable me to interact with your core infrastructure directly.

### 1. PostgreSQL MCP
**Why:** Your backend (`server_fastapi`) relies heavily on SQLAlchemy/AsyncPG.
**Benefit:** Allows me to:
- Verify database migrations (`alembic`).
- Debug data inconsistencies without writing throwaway scripts.
- Validate that API changes are correctly persisting data.
**Config:**
```json
"postgresql": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-e",
    "POSTGRES_CONNECTION_STRING=postgresql://user:password@host:5432/dbname",
    "mcp/postgres"
  ]
}
```

### 2. Redis MCP
**Why:** You use `aioredis` and Celery.
**Benefit:** Allows me to:
- Inspect `celery` queues to see stuck jobs.
- Verify cache keys are being set/expired correctly.
- Flush cache during debugging sessions.
**Config:**
```json
"redis": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "mcp/redis",
    "redis-cli",
    "-u",
    "redis://localhost:6379"
  ]
}
```

### 3. Sentry MCP
**Why:** `sentry-sdk` is present in `requirements.txt`.
**Benefit:** Allows me to:
- actively look up the stack trace of the "latest error" you mention, rather than you pasting it.
- Connect reported issues directly to code locations.
**Config:**
```json
"sentry": {
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-sentry"
  ],
  "env": {
    "SENTRY_AUTH_TOKEN": "your-token"
  }
}
```

### 4. Docker MCP
**Why:** You have a complex `docker-compose` setup with `backend`, `frontend`, `grafana`, etc.
**Benefit:** Allows me to:
- Check container health status (`docker ps`).
- Read logs from specific containers (`docker logs`).
- Restart services that are stuck.
**Config:**
```json
"docker": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-v",
    "/var/run/docker.sock:/var/run/docker.sock",
    "mcp/docker"
  ]
}
```

## 🚀 High Value (Domain Specific)

### 5. EVM / Web3 MCP
**Why:** Your project is a Crypto Orchestrator using `web3.py`.
**Benefit:** A specialized EVM MCP is better than me "guessing" via generic fetch.
- Decode transaction data.
- Check contract state on-chain.
- Verify gas prices across networks.
**Recommendation:** `evm-mcp-server` (as noted in your existing list) is excellent here.

### 6. GitHub MCP
**Why:** You have a mature repo with CI/CD workflows (`.github/workflows`).
**Benefit:**
- I can create Issues for bugs I find.
- I can inspect PRs or check why a specific Action failed.
**Config:**
```json
"github": {
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-github"
  ],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"
  }
}
```

## ❌ NOT Recommended (Updates from Scan)

- **Stripe MCP**: Your `requirements.txt` specifically says `# REMOVED: Using free subscription service instead`. Do not install this; it is dead weight.
- **CCXT**: Also removed in favor of DEX-only.

## Summary Checklist for `mcp-hub.json`

[ ] PostgreSQL
[ ] Redis
[ ] Docker
[ ] Sentry
[ ] GitHub
[ ] EVM/Web3
