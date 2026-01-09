---
description: Triggerable workflow for generating unit tests.
---

# Unit Test Generation Workflow

Use this workflow to generate comprehensive unit tests for a specific module or set of files.

1. **Analysis**
   - Identify public methods and edge cases.`r`n   - Use `sequential-thinking` to map out complex edge cases and failure modes.
   - // architect: Phase 1

2. **Test Drafting**
   - Generate unit tests with 	est_ prefix.
   - Ensure mocks are used for external dependencies (APIs, Database).
   - Target 90% logic coverage.

3. **Execution**
   - Run the tests: pytest (backend) or itest (frontend).
   - Iterate if tests fail or coverage is low.
   - // architect: Phase 4

