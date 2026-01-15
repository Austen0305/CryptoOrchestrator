---
name: Compliance Check
description: Triggerable review against SOC2, GDPR, and MiCA 2026 requirements.
---

# Workflow: Compliance Check (2026)

This workflow verifies code changes against the latest regulatory and security standards.

## 📋 Steps

### 1. 🔍 Regulatory Threshold Check
- Identify if the change affects:
  - User funds or wallet balance.
  - PII (Personally Identifiable Information).
  - Trade execution or order booking.
  - Regional tax reporting (UK 2026).

### 2. 🛡️ MiCA RTS Audit
- Verify that transaction logs comply with ISO 20022 JSON schema standards.
- Check for proper asset segregation logic in service layers.

### 3. 🔐 Security & PII Scan
- Ensure no secrets are hardcoded.
- Verify that PII is encrypted/hashed before storage or logging.
- Check React 19 components for data exposure in the client-side state.

### 4. 📝 Compliance Report
- Generate a summary of compliance findings.
- **MANDATORY**: If any safety guards are bypassed, trigger an immediate `/security_audit`.

---

// turbo-all
