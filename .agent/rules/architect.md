Priority: HIGH
Scope: REFACTOR-ONLY
Overrides: compliance_standards, infra_safety

---
trigger: always_on
glob: "**/*"
description: Orchestration rule for Architect mode, prioritizing research and planning.
---

# Architect Orchestration Rule

This rule governs the systematic workflow for complex engineering tasks, following the "Research -> Plan -> Build" cycle.

## Phase 1: Deep Research (MANDATORY)
Before any code modification:
- **Understand Scope**: Explore all affected modules, entry points, and execution paths.`r`n  - **MANDATORY**: Audit `docs/compliance/` and `docs/developer/` before modifying financial or architectural logic.
- **Mental Model**: Build a complete data flow and state transition model.
- **Identify Risks**: Locate ambiguous, misleading, or unsafe logic, especially in financial paths.
- **Currency Check**: Validate that proposed patterns align with 2025-2026 industry standards.`r`n  - Use `brave-search`, `wikipedia`, and `fetch` to verify current best practices and latest tool documentation.

## Phase 2: Structural Planning
- **Implementation Plan**: Create a detailed implementation_plan.md in the current session's artifact directory.
- **Review Guards**: Identify all financial safety guards (e.g., `RiskManager`, `validation_2026.py`) and validation layers_required.
- **Decomposition**: Break the task into granular, verifiable steps in `task.md`.

## Phase 3: Explicit Execution
- **Safety First**: Prioritize safety, correctness, and determinism over speed.
- **Pure Logic**: Prefer pure functions and strict side-effect isolation.
- **Explicit Transitions**: Replace implicit behavior with explicit, auditable state transitions.
- **Financial Validation**: Enforce schema validation (Zod/Pydantic) for all financial data.

## Phase 4: Verification & Walkthrough
- **Coverage**: Ensure tests meet the project threshold (90% backend, 85% frontend).
- **Walkthrough**: Create a walkthrough.md capturing changes, test results, and visual proof of correctness.`r`n- **Chaos Simulation**: Verify system resiliency by simulating API/Node timeouts using the terminal.



