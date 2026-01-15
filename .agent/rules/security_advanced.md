---
trigger: always_on
glob: ["server_fastapi/services/security/**/*"]
description: Advanced security standards for high-stakes financial logic (MPC/ZKP/Formal).
---

# Advanced Security Standards (2027 Edition)

## 🔐 Cryptographic Sovereignty

### Multi-Party Computation (MPC)
- **Threshold Signatures**: All wallet signing operations **MUST** use MPC protocols (e.g., GG20, FROST) where no single party holds the full private key.
- **Key Sharding**: Shares must be stored across geographically distributed HSMs or secure enclaves.

### Zero-Knowledge Proofs (ZKP)
- **Private Compliance**: Use ZKPs (e.g., zk-SNARKs) to prove AML/KYC status to external parties without revealing the underlying PII.
- **State Validity**: Core trading state transitions must be accompanied by a ZK-proof of validity.

## 🛡️ Formal Verification
- **State Machine Integrity**: The core trade execution state machine **MUST** be formally verified using tools like TLA+ or Coq for safety and liveness properties.
- **Pydantic Strict Mode**: All financial models must enable `strict=True` to prevent implicit type coercion.

## 🕵️ Market Abuse & Surveillance
- **Real-time Detection**: Implement AI-driven surveillance for Spoofing, Wash Trading, and Layering.
- **Circuit Breaker**: Automatic 10-minute trading pause if anomalous signature volume is detected (>5 sigma from 30D average).

## 🚩 Hardening
- **Key Management**: Keys MUST NEVER leave the HSM. All signing must happen within the HSM environment.
- **Zero-Trust IPC**: All communication between microservices must be mutually authenticated (mTLS) and encrypted.
