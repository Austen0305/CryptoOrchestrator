---
name: finance_validator
description: Specialized skill for validating EIP-55 Ethereum addresses and ISO 20022 financial schemas.
---

# Finance Validator Skill

This skill provides automated validation logic for critical financial data in CryptoOrchestrator.

## Capabilities

- **EIP-55 Validation**: Ensures Ethereum addresses follow the checksum specification to prevent typos and fund loss.
- **ISO 20022 Schema Validation**: Validates transaction records against the MiCAR-compliant ISO 20022 standard.

## Usage

Use the provided `validate.py` script for automated checks during development and CI.

### Examples

**Validate an Ethereum Address:**
```bash
python .agent/skills/finance_validator/scripts/validate.py --address 0x5aAeb6053F3E94C9b9A09f33669415693fdaC2cF
```

**Validate an ISO 20022 JSON Transaction:**
```bash
python .agent/skills/finance_validator/scripts/validate.py --schema iso_20022 --file transaction.json
```

## Safety Guards

- This skill is a prerequisite for any trade execution or wallet management task.
- If validation fails, the `RiskManager` circuit breaker MUST be triggered.
