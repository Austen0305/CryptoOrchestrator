---
name: MCP Orchestration
description: Optimize the use of cognitive tools to maximize efficiency, accuracy, and depth of insight.
---

# Workflow: MCP Orchestration (Recursive Intelligence)

Optimize the use of cognitive tools to maximize efficiency, accuracy, and depth of insight.

## 🛠️ The Full Suite Integration

### 1. 🔍 Discovery & Intelligence
- **`mcp:brave-search`**: Mandatory for real-time 2026/2027 regulatory (MiCA/GENIUS) and industry standards.
- **`mcp:fetch`**: For deep ingestion of public documentation and transcripts.
- **`mcp:wikipedia`**: For non-technical domain context and historical financial benchmarks.
- **`mcp:context7`**: Primary source for deep library-specific documentation and code snippets (e.g., FastAPI v0.115+, React 19).

### 2. 🧠 Recursive Reasoning
- **`mcp:sequential-thinking`**: Mandatory for complexity > 5. Use to simulate edge cases and architectural trade-offs.
- **`mcp:memory`**: Persistent knowledge graph. Use to store/retrieve architectural rationale and cross-session context.

### 3. 🛡️ Advanced Engineering
- **`mcp:chrome-devtools`**: Mandatory for frontend debugging, DOM inspection, and lighthouse performance audits in the browser.
- **`mcp:filesystem`**: Deep local file manipulation and multi-file reads for impact analysis.
- **`mcp:git` & `mcp:github`**: Use `git_bulk_action` for complex commits and `github_create_pull_request` for team collaboration.

### 4. 🚀 Cloud & Deployment
- **`mcp:cloudrun`**: Full lifecycle management for GCP services (create project, deploy container, fetch logs).
- **`mcp:vercel`**: High-speed front-end deployments, build event monitoring, and meta-data management.

## 🧠 Recursive Intelligence Chain (Complexity > 5)

1.  **Exploration**: `filesystem_list` -> `filesystem_read_multiple`.
2.  **Context**: `brave-search` (current year) -> `context7` (exact lib versions).
3.  **Synthesis**: `sequential-thinking` (min 10 thoughts) -> `memory` (persist rationale).
4.  **Action**: `filesystem_write` -> `git_add/commit`.
5.  **Audit**: `chrome-devtools` (UI verification) -> `github_search_code` (regression check).

## 🚀 Hyper-Optimization

- **Parallelization**: Batch non-dependent `fetch` or `search` calls.
- **Memory Checkpoints**: Call `mcp:memory_add_observations` after every major state change to ensure the agent doesn't "forget" design constraints.

---

// turbo-all
