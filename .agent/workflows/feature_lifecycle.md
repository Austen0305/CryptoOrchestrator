---
name: Feature Lifecycle
description: Comprehensive lifecycle for implementing a new feature in CryptoOrchestrator.
---

# Feature Lifecycle Workflow (Master Edition)

A 5-phase lifecycle designed for maximum safety, premium aesthetics, and regulatory compliance.

## 🚀 Phases

### 1. 🔍 Intelligence Audit (Cortex: Phase 1)
- **Goal**: Research and mental modeling.
- **Actions**:
  - `mcp:brave-search` for 2026/2027 industry benchmarks.
  - Audit `docs/compliance/` for MiCA/GENIUS alignment.
  - Map every potential side effect in the trading pipeline.

### 2. 🧠 Recursive Planning (Cortex: Phase 2)
- **Goal**: Deep design and safety guards.
- **Actions**:
  - `mcp:sequential-thinking` (min 15 steps) for edge cases.
  - Create `implementation_plan.md` with a "Verification Plan".
  - **MANDATORY**: Identify every `RiskManager` interaction point.

### 3. ⚡ Explicit Implementation (Cortex: Phase 3)
- **Goal**: Clean code and strict typing.
- **Actions**:
  - Implement idempotent services via `real_money_transaction_manager.py`.
  - Use **React 19 Server Components** for sensitive dashboards.
  - Enforce strict Pydantic v2 schemas.

### 4. 🛡️ Verification & Chaos (Cortex: Phase 4)
- **Goal**: Proving resilience.
- **Actions**:
  - 90% logic coverage with `pytest`.
  - Mandatory `/chaos_engineering` run for financial paths.
  - `/compliance_check` against MiCA ISO 20022 schemas.

### 5. 🎨 UI Modernization & Walkthrough
- **Goal**: Premium UX and documentation.
- **Actions**:
  - Apply glassmorphism and animated transitions.
  - Create `walkthrough.md` with embedded recordings.

---

// turbo-all
