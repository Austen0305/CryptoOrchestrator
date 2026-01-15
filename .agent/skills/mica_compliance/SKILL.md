---
name: mica_compliance
description: Regulatory requirements and auditing steps for MiCAR 2026 (Markets in Crypto-Assets Regulation).
---

# MiCA Compliance Skill

This skill ensures that all trading operations and record-keeping in CryptoOrchestrator align with the EU MiCAR 2026 standards.

## Capabilities

- **ISO 20022 Reporting**: Ensuring transaction logs are machine-readable and follow standardized financial message formats.
- **Asset Segregation Audit**: Verifying that client assets are managed in segregated wallets from operational funds.
- **Custody Rules**: Enforcing strict governance over private key management and HSM usage.

## Resources

- `resources/iso_20022_schema.json`: The reference schema for ESMA-aligned transaction reporting.
- `SKILL.md`: Compliance checklist and regulatory audit procedures.

## Compliance Checklist

1.  **Transaction Recording**: Does the log include mandatory ISO 20022 fields?
2.  **Wallet Management**: Are client addresses EIP-55 checksummed and segregated?
3.  **Governance**: Is the `RiskManager` circuit breaker active for high-volume trades?
4.  **Reporting**: Are weekly reconciliation reports generated using the `iso_20022` format?
