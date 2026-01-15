---
name: Advanced Debugging
description: Advanced debugging workflow leveraging Chrome DevTools, Sentry, and cloud logs.
---

# Workflow: Advanced Debugging (Cross-Stack)

A systematic approach to identifying and resolving complex issues across the frontend, backend, and infrastructure.

## 🛠️ Step 1: Client-Side Diagnostics
1.  **DOM & State**: Use `mcp:chrome-devtools` to inspect the React component tree and current Redux/Context state.
2.  **Network Audit**: Use `mcp:chrome-devtools` to analyze network requests for failed API calls or slow response times.
3.  **Performance**: Run a Lighthouse audit or memory snapshot via `mcp:chrome-devtools` to identify layout shifts or memory leaks.

## 🛠️ Step 2: Backend & Infrastructure Logs
1.  **Error Tracking**: Use `sentry` MCP to retrieve the full stack trace and breadcrumbs for the specific error ID.
2.  **Cloud Logs**:
    - If on GCP: Use `mcp:cloudrun_get_service_log` for the relevant service.
    - If on Vercel: Use `mcp:vercel_getDeploymentEvents`.
3.  **Trace Analysis**: Use the OpenTelemetry IDs from the logs to trace the request across microservices (Redis, Celery).

## 🛠️ Step 3: Recursive Resolution
1.  **Intelligence**: Use `mcp:brave-search` to research the specific error message or library conflict.
2.  **Reasoning**: Initialize `mcp:sequential-thinking` (min 10 steps) to hypothesize the root cause.
3.  **Verification**: After applying a fix, repeat Step 1 to ensure the issue is resolved and no regressions were introduced.

---

// turbo-all
