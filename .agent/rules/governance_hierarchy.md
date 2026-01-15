---
trigger: always_on
glob: ["**/*"]
description: Master rule defining the precedence and hierarchy of all project governance.
---

# Governance Hierarchy & Policy Precedence

This rule defines the operational hierarchy for all agents and contributors within the CryptoOrchestrator workspace.

## 👑 Hierarchy of Authority

In case of conflict between rules or workflows, the following precedence **MUST** be applied:

1.  **Safety & Security** ([safety.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/safety.md), [security_advanced.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/security_advanced.md))
2.  **Regulatory Compliance** ([compliance_standards.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/compliance_standards.md))
3.  **Financial Integrity** ([backend_idempotency.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/backend_idempotency.md))
4.  **Operational Resilience** ([infra_safety.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/infra_safety.md), [observability_standards.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/observability_standards.md))
5.  **Engineering Excellence** ([architect.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/architect.md), [code_modularity.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/rules/code_modularity.md))

## 🛡️ The "Chain of Command" for Tasks

All tasks **MUST** pass through the following filter sequence:

1.  **Intelligence Filter**: Research 2026/2027 standards (MiCA/GENIUS).
2.  **Safety Filter**: Validate against `RiskManager` and `validation_2026.py`.
3.  **Compliance Filter**: Ensure ISO 20022 schema alignment for logs.
4.  **Resilience Filter**: Mandatory Chaos Engineering simulation for financial paths.

## 🚩 Rule Conflicts

If a user request conflicts with a higher-priority rule (e.g., adding a feature that bypasses the `RiskManager`), the agent **MUST**:
1.  Identify the conflict explicitly.
2.  Refuse the bypass.
3.  Propose a compliant alternative that satisfies the higher-priority rule.
