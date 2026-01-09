# System Exploration & Freeze

Priority: BLOCKING
Prerequisite: NONE
Required: YES

## Objective
Traverse the entire repository to build a complete mental model before any code modification. This workflow enforces Rule 0 and the Global Safety Rule.

## Mandatory Steps
1. **Repository Traversal**:
   - Recursively list and examine all directories.
   - Identify main entry points (e.g., main.py, pp.py, index.ts).
   - Identify core financial modules and safety guards (RiskManager, alidation_2026.py).

2. **Logic Auditing**:
   - Trace execution paths for trade placement and signing.
   - Identify all external integrations (Gateways, APIs, Blockchain nodes).
   - Locate side-effect-heavy modules (Database writes, networking).

3. **Written System Map**:
   - Produce a concise summary of data flow and state transitions.
   - Explicitly declare which modules are **READ-ONLY** based on safety rules.
   - Identify ambiguous or unsafe logic and mark with TODO comments.

4. **Documentation**:
   - Document all findings in the session memory and artifacts.
   - Propose no changes until this step is verified.

## Enforcement
- **MODIFICATION FREEZE**: No code modifications are permitted during this workflow.
- **DEPENDENCY**: All subsequent workflows (feature_lifecycle, security_audit, etc.) require the successful completion and documentation of this exploration.