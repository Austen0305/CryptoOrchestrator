---
trigger: always_on
glob: "server_fastapi/services/security/**/*"
description: Advanced security standards for high-stakes financial logic.
---

# Advanced Security Standards`r`n`r`n## Regulatory Alignment`r`n- **MiCA & GENIUS**: All custody, reserve, and AML logic must align with EU MiCA (2025) and US GENIUS Act (2026/2027) implementing regulations.

## Cryptography
- **MPC & ZKP**: Use multi-party computation (MPC) and zero-knowledge proofs (ZKP) for sensitive multi-signature operations.
- **Formal Verification**: Core state-machine logic for trade execution must undergo formal verification.

## Market Abuse Prevention`r`n- **Surveillance**: Implement Spoofing, Layering, and Momentum Ignition detection as defined in `FINANCIAL_COMPLIANCE.md`.`r`n`r`n## Hardening
- **Key Management**: Keys must never leave the HSM or secure enclave.
- **Circuit Breakers**: Implement security circuit breakers that pause trading if anomalous signature patterns are detected.

