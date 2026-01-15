---
trigger: always_on
glob: ["**/*"]
description: Orchestration rule for Architect mode, prioritizing research and planning.
---

# Architect Orchestration Rule

This rule governs the systematic workflow for complex engineering tasks, following the "Research -> Plan -> Build" cycle.

## Phase 1: Deep Research (MANDATORY)
Before any code modification:
- **Understand Scope**: Explore all affected modules, entry points, and execution paths.
  - **MANDATORY**: Audit docs/compliance/ and docs/developer/ before modifying financial or architectural logic.
- **Regulatory Intelligence**: Validate compliance against **2026 MiCA and GENIUS Act** requirements using mcp:brave-search and mcp:fetch.
- **Registry & Libs**: Use mcp:context7 to resolve exact library IDs for all new dependencies.
- **Mental Model**: Build a complete data flow and state transition model.
- **Identify Risks**: Locate ambiguous, misleading, or unsafe logic, especially in financial paths.
- **Currency Check**: Validate that proposed patterns align with 2025-2026 industry standards.
  - Use rave-search, wikipedia, and etch to verify current best practices and latest tool documentation.

## Phase 2: Structural Planning
- **Recursive Reasoning**: Use mcp:sequential-thinking (min 15 steps) to analyze edge cases and design fallback strategies.
- **Knowledge Retention**: Call mcp:memory_add_observations for significant architectural decisions.
- **Implementation Plan**: Create a detailed implementation_plan.md in the current session's artifact directory.
- **Review Guards**: Identify all financial safety guards (e.g., RiskManager, alidation_2026.py) and validation layers required.
- **Decomposition**: Break the task into granular, verifiable steps in 	ask.md.

## Phase 3: Explicit Execution
- **Safety First**: Prioritize safety, correctness, and determinism over speed.
- **Pure Logic**: Prefer pure functions and strict side-effect isolation.
- **Explicit Transitions**: Replace implicit behavior with explicit, auditable state transitions.
- **Financial Validation**: Enforce schema validation (Zod/Pydantic) for all financial data using ESMA-aligned formats where applicable.

## Phase 4: Verification & Walkthrough
- **Coverage**: Ensure tests meet the project threshold (90% backend, 85% frontend).
- **Chaos Simulation**: Verify system resiliency by simulating failure scenarios via the /chaos_engineering workflow.
- **UX Audit**: Use mcp:chrome-devtools to verify UI performance and layout stability.
- **Walkthrough**: Create a walkthrough.md capturing changes, test results, and visual proof of correctness.
