---\r\nPrerequisite: 00_system_exploration.md
description: Comprehensive lifecycle for implementing a new feature in CryptoOrchestrator.
---\r\nPrerequisite: 00_system_exploration.md

# Feature Lifecycle Workflow

Follow these steps to implement a feature that meets all safety and quality standards.

1. **Research & Audit**
   - Identify existing services or components to reuse.`r`n   - Use `brave-search` and `fetch` to research industry standards and external API documentation.
   - Map data flow and identify security risks.
   - // architect: Phase 1

2. **Technical Planning**
   - Define Pydantic/Zod schemas.
   - Draft the implementation plan in artifacts.`r`n   - Mandate usage of `server_fastapi/utils/validation_2026.py` for all new inputs.
   - // architect: Phase 2

3. **Backend Implementation**
   - Implement idempotent services.
   - Add unit tests with 90%+ coverage.

4. **Frontend Integration**
   - Create custom hooks for API access.
   - Build UI components with premium aesthetics (glassmorphism).

5. **Verification**
   - Run E2E tests (
pm run test:e2e:complete).
   - Monitor production logs/errors via `sentry` MCP.`r`n   - Perform "Chaos Simulation" by manually failing API dependencies in terminal to verify fallback logic.`r`n   - // architect: Phase 4



