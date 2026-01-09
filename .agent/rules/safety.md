Priority: CRITICAL
Scope: READ-ONLY
Overrides: NONE

---
trigger: always_on
glob: "**/*"
description: Core safety and architectural rules for high-risk financial codebase.
---

# Workspace Rules for CryptoOrchestrator`r`n`r`n## Rule 0: AI Safety & HITL`r`n- **No Bypass**: The AI assistant MUST NOT bypass `RiskManager` or `server_fastapi/utils/validation_2026.py` for any financial logic.`r`n- **Human-in-the-Loop**: Trade signing and wallet key management require explicit user validation via `notify_user` before execution.

These rules apply to the entire workspace and prioritize safety, correctness, and Google Antigravity standards.

## Financial Safety Guards
- **Validation**: Every financial transaction must be validated against `validation_2026.py` (Python) or `validation.ts` (TS) using EIP-55 checksumming for addresses.
- **Auditability**: All state-changing operations in the trading or wallet modules must be logged with structured metadata. Use `github` MCP to audit related code history during reviews.
- **Side Effects**: Isolate all API calls and database writes within dedicated service modules (server_fastapi/services/ or client/src/services/).

## Tech Stack Compliance (2026)
- **Frontend**: Use React 19+ with functional components and Server Actions where appropriate. and TanStack Query v5. Avoid direct state mutations.
- **Backend**: Use FastAPI with async/await. All endpoints must handle request timeouts and return standard error formats.
- **Infrastructure**: Use Alembic for any database schema changes. Ensure migrations are tested for both upgrade and downgrade paths.

## Antigravity Workflow
- **Proactiveness**: Explore dependencies and side effects before implementing changes.
- **Refactoring**: Focus on improving testability and clarity. Replace implicit logic with explicit state transitions.
- **Documentation**: Use JSDoc/TSDoc for frontend and Google-style docstrings for backend. Leverage `memory` MCP to persist architectural context and security decisions.

## Testing Standards
- **Backend**: Run 'pytest' with 90%+ coverage targets.
- **Frontend**: Run 'npm run test:frontend'.
- **E2E**: Use 'npm run test:e2e:complete' for critical path verification.



