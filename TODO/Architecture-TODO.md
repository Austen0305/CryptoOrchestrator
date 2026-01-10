
# Architecture & Trust Model TODOs

## Trust Model & Boundaries (Non-Custodial & Self-Hosted)
- [ ] **Strict Trust Boundaries**:
    - [ ] Enforce strict execution boundaries between UI, API Gateway, Execution Engine, Signing Service, and ML Advisory.
    - [ ] Ensure the Signing Service is isolated in a minimal, hardened process with zero-memory footprint after signing.
- [ ] **Key Management (Hardened)**:
    - [ ] **Self-Hosted Vault**: User hosts HashiCorp Vault (Open Source) locally or on their own VPS. No reliance on third-party SaaS for keys.
    - [ ] **Wallet Permission Scopes**: Enforce granular scopes for every key (e.g., single DEX, specific pair, max value).
    - [ ] **Client-Side Signing**: Parallelize signing logic; ensure keys never leave the HSM/Enclave.
- [ ] **Cost Efficiency**:
    - [ ] **Free Tier First**: Maintain AWS Free Tier (t3.micro) compatibility for core orchestration.
    - [ ] **Data Feeds**: Strictly use Free Market Data APIs (e.g., CoinCap, CoinLore) + On-chain RPCs (free endpoints).
- [ ] **Failure Domains & Resilience**:
    - [ ] **Stateless Services**: Ensure all core services are stateless, restart-safe, and replay-safe.
    - [ ] **RPC Rotation**: Implement automated rotation between public and private RPC endpoints (Infura/Alchemy/Public).
    - [ ] **Single Source of Truth**: Define a single source of truth for all strategy, wallet, and execution state.

## Architecture Components
- [ ] **Frontend**: Electron (Local Desktop App) / React Native (User's Phone).
- [ ] **Backend**: FastAPI (Self-Hosted).
- [ ] **Database**: Postgres (Docker container - Free).
- [ ] **Cache**: Redis (Docker container - Free).
- [ ] **ML Engine**: PyTorch (Local Inference on User CPU/GPU).

## Critical Safety Path
- [ ] Map critical path used in `real_money_transaction_manager`.
- [ ] Verify `validation_2026.py` is applied at the API Gateway level.

## Phase 6: Financial Consistency & Determinism
- [ ] **Deterministic Execution Engine**:
  - [ ] Guarantee same inputs + state → same outputs/broadcasts.
  - [ ] Enforce a strict execution state machine with no skipped states (e.g., Pending -> Simulating -> Validating -> Signing -> Confirming).
- [ ] **Acid Compliance**:
  - [ ] **DB**: `SERIALIZABLE` isolation for all wallet commands.
  - [ ] **Block**: 12-block confirmation rule for "settled" state.
- [ ] **Reorg Defense**:
  - [ ] **Optimistic Locking**: Use DB versioning for trade state.
  - [ ] **Watcher Service**: Independent daemon verifying past block hashes (1-5 block depth).
  - [ ] **Safe Replay**: Logic for handle idempotent execution even after partial failures or restarts.
