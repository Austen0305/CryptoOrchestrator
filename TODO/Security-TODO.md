
# Security Hardening TODOs

- [ ] **Advanced Cryptography (2026 Standard)**
  - [ ] **MPC (Multi-Party Computation) Key Management**:
    - [ ] **Library**: Integrate `PySyft` or `multi-party-sig` (Rust).
    - [ ] **Infrastructure**: Distribute key shares across 3 distinct environments (Local Enclave, Cloud KMS, Admin Device).
    - [ ] **Protocol**: Implement Gennaro-Goldfeder (GG20) or similar threshold signature scheme.
  - [ ] **Zero-Knowledge Proofs (ZKP)**:
    - [ ] **Proof of Solvency**: Implement `zk-SNARK` circuit to prove (Assets >= Liabilities) without revealing user balances.
    - [ ] **Identity**: Implement "Zero-Knowledge KYC" where users prove residency != Restricted Region without revealing exact address.

- [ ] **Infrastructure Hardening**
  - [ ] **HSM Integration**:
    - [ ] Use AWS KMS / Google Cloud KMS only for *signing key shares*, never for full key storage.
    - [ ] **Enclaves**: Deploy signing service to AWS Nitro Enclaves or SGX.

## Phase 3: Immediate Safeguards
- [ ] **Code Hardening (Static Analysis)**
  - [ ] **SAST**: Run `bandit` on all Python code to catch security issues (e.g. weak random, exec calls).
  - [ ] **Secrets Detection**: Pre-commit hook with `trufflehog` to prevent key commits.
  - [ ] **Dependency Scan**: Run `pip-audit` to check for known CVEs in `requirements.txt`.
- [ ] **Input Sanitization**
  - [ ] Audit all SQL queries for injection vulnerabilities (ensure ORM usage).
  - [ ] Validate all JSON payloads against strict Pydantic schemas.

## Phase 4: Production Key Management (Free / Self-Hosted)
- [ ] **Encrypted Key Storage (Free)** `(Priority: Critical)`
  - [ ] **Codebase Scrub**: Scan and remove ALL hardcoded mock keys (e.g., `0x...01` in `trading_orchestrator.py`).
  - [ ] **Logic**: Never store plain keys. Use Local Encryption (AES-GCM).
  - [ ] **Vault Alternative**: Instead of paid KMS, use `LocalEncryptedKeyManager` (Python) + Supabase Secrets.
  - [ ] **Hardware Wallet (Optional)**: If user has a Ledger (Free integration), use it for *admin* ops.

## Phase 5: Authentication & Access Control
- [ ] **RBAC (Role-Based Access Control)**
  - [ ] Define `Admin`, `User`, `Auditor` roles.
  - [ ] Enforce permission checks on critical endpoints (`/admin/*`, `/withdraw`).
- [ ] **2FA (Two-Factor Authentication)**
  - [ ] Implement TOTP (Google Authenticator) - Completely Free standard.
  - [ ] Enforce 2FA for *any* key export or API key creation.

## Phase 6: Advanced Defense
  - [ ] **Log Retention**: Use Google Cloud Logging (Free 50GB) for short term (30 days).
  - [ ] **Code Hooks**: Implement `structlog` for JSON-structured logging to ensure easy parsing.
