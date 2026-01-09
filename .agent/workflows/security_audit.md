---\r\nPrerequisite: 00_system_exploration.md
description: Triggerable workflow for security auditing.
---\r\nPrerequisite: 00_system_exploration.md

# Security Audit Workflow

Run this workflow before major deployments or after security-sensitive changes.

1. **Secret Scanning**
   - Scan files for hardcoded API keys, tokens, or credentials.`r`n   - Use `github` MCP to check commit history for previously deleted but still valid secrets.

2. **Dependency Audit**
   - Run 
pm audit or safety check -r requirements.txt.

3. **Logic Review**
   - Verify CSP headers in lectron and client.
   - Check RBAC (Role-Based Access Control) in financial endpoints.`r`n   - Manually verify ZKP/MPC proof integrity in multi-signature execution paths.
   - Ensure all financial inputs are validated via Pydantic/Zod.

4. **Report**
   - Document any vulnerabilities found and their remediation status.`r`n   - Perspective relevant context into `memory` MCP to track recurring issues.



