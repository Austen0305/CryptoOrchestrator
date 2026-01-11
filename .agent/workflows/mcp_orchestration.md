---
description: Intelligent orchestration and orchestration of Model Context Protocol (MCP) tools across the development lifecycle.
---

# MCP Orchestration Workflow

This workflow provides a strategic framework for using MCP tools to Maximize efficiency, accuracy, and safety.

## 1. Research & Exploration (Phase 1)
Use these tools to establish a baseline and gather requirements.

- **`brave-search` & `fetch`**:
  - // turbo
  - Always search for the latest regulatory standards (e.g., MiCA, GENIUS Act) before modifying financial logic.
  - Use `fetch` to extract specific API documentation or technical whitepapers.
- **`wikipedia`**:
  - // turbo
  - Use for general concepts, history of protocols, or high-level explanations of cryptographic primitives.
- **`filesystem` & `git`**:
  - // turbo
  - `mcp_filesystem_list_directory` to map workspace structure.
  - `mcp_git_status` and `mcp_git_branch_list` to understand the current environment state.

## 2. Structural Planning (Phase 2)
Use these tools to design the solution and maintain context.

- **`sequential-thinking`**:
  - // turbo
  - Use when faced with complex architectural decisions or multi-step refactors.
  - Breakdown the "how" before the "what."
- **`memory`**:
  - // turbo
  - Store critical architectural decisions, security findings, and entity relationships.
  - Check `memory` regularly for cross-project context.

## 3. Implementation & Execution (Phase 3)
Use these tools to modify code while maintaining safety.

- **`filesystem`**:
  - // turbo
  - Use `mcp_filesystem_read_text_file` to inspect code before editing.
  - Use `mcp_filesystem_write_file` and `mcp_filesystem_edit_file` for atomic changes.
- **`git`**:
  - // turbo
  - Create feature branches before making significant changes.
  - Stage changes (`mcp_git_add`) and commit (`mcp_git_commit`) with descriptive messages.

## 4. Verification & Debugging (Phase 4)
Use these tools to validate the solution and troubleshoot issues.

- **`chrome-devtools`**:
  - // turbo
  - Inspect UI elements for premium aesthetics (glassmorphism, animations).
  - Use the Performance panel to verify that inference/state-transfers stay within budget (e.g., <50ms).
  - Use `mcp_chrome_devtools_take_screenshot` or `mcp_chrome_devtools_take_snapshot` for walkthrough evidence.
- **`sequential-thinking`**:
  - // turbo
  - Re-evaluate the solution if verification reveals edge cases.
- **`filesystem`**:
  - // turbo
  - Read log files (`server_fastapi/logs/`) to diagnose runtime errors.

## 5. Security & Compliance
Apply these throughout all phases.

- **`brave-search`**:
  - // turbo
  - Search for recent CVEs related to dependencies being added or updated.
- **`memory`**:
  - // turbo
  - Record any security risks identified and the mitigation strategy used.
