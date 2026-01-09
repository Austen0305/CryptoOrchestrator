---
description: Triggerable review against SOC2/GDPR requirements.
---

# Compliance Review Workflow

1. **Audit Trail Review**
   - Verify financial operations are creating structured logs in the `audit_logs` table.`r`n   - Use `gcs` MCP to verify that immutable backups of these logs are present and intact.

2. **Access Control Check**
   - Review IAM roles and API key permissions.

3. **Data Residency Check**
   - Verify data storage locations align with regional requirements.

