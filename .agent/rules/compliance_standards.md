---
trigger: always_on
glob: ["server_fastapi/**/*"]
description: Standards for regulatory compliance (MiCA, GENIUS, SOC2).
---

# Compliance Standards (2026)

## Audit Logging
- **Performance**: Optimize audit log queries using `idx_audit_logs_user_action_created`.
- **MiCA RTS 2026**: All transaction records MUST use **ISO 20022 compliant JSON schemas** to ensure machine-readable audit trails for competent authorities.
- **Immutable Logs**: State changes in financial modules must be logged to an immutable audit trail. Verify storage integrity using `gcs` MCP or similar redundant storage.
- **PII Protection**: Ensure no PII (Personally Identifiable Information) is logged in plaintext. Use salted hashes for deterministic auditing.

## Regional Compliance
- **UK 2026**: Enforce tax reporting details (personal detail collection) for UK-based traders starting Jan 1, 2026.
- **EU MiCA**: Enforce asset segregation and strict custody rules as defined in the 2025/2026 RTS.

## SOC2 & GDPR
- **Access Review**: Enforce RBAC for all administrative endpoints.
- **Data Deletion**: Implement `gdpr_service.py` hooks for user data deletion requests.
- **Privacy by Design**: Use React 19 Server Components to minimize PII exposure in the frontend bundle.
