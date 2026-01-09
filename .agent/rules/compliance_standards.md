---
trigger: always_on
glob: "**/*"
description: Standards for SOC2 and GDPR compliance.
---

# Compliance Standards

## Audit Logging`r`n- **Performance**: Optimize audit log queries using `idx_audit_logs_user_action_created`.
- **Immutable Logs**: State changes in financial modules must be logged to an immutable audit trail. Verify storage integrity using `gcs` MCP.
- **PII Protection**: Ensure no PII (Personally Identifiable Information) is logged in plaintext.

## Regional Compliance`r`n- **UK 2026**: Enforce tax reporting details (personal detail collection) for UK-based traders starting Jan 1, 2026.`r`n`r`n## SOC2 & GDPR
- **Access Review**: Enforce RBAC for all administrative endpoints.
- **Data Deletion**: Implement `gdpr_service.py` hooks for user data deletion requests.


