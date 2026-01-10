
# Architecture & Trust Model TODOs

## Trust Model (Non-Custodial & Self-Hosted)
- [ ] **Key Management**:
    - [ ] **Self-Hosted Vault**: User hosts HashiCorp Vault (Open Source) locally or on their own VPS. No reliance on paid SaaS (AWS/Fireblocks).
    - [ ] **Client-Side Signing**: All transactions signed locally by the bot/user.
- [ ] **Cost Efficiency**:
    - [ ] **Free Tier First**: Architect system to run within AWS Free Tier (t3.micro) or locally.
    - [ ] **Data Feeds**: Strictly use CoinGecko Free API + On-chain RPCs (free endpoints).
- [ ] **Failure Domains**:
    - [ ] **RPC Failure**: Rotate between free public RPCs (Infura/Alchemy Free Tiers + Public nodes).

## Architecture Components
- [ ] **Frontend**: Electron (Local Desktop App) / React Native (User's Phone).
- [ ] **Backend**: FastAPI (Self-Hosted).
- [ ] **Database**: Postgres (Docker container - Free).
- [ ] **Cache**: Redis (Docker container - Free).
- [ ] **ML Engine**: PyTorch (Local Inference on User CPU/GPU).

## Critical Safety Path
- [ ] Map critical path used in `real_money_transaction_manager`.
- [ ] Verify `validation_2026.py` is applied at the API Gateway level.

## Phase 6: Financial Consistency Model (The "Perfect" Standard)
- [ ] **Acid Compliance**:
  - [ ] **DB**: `SERIALIZABLE` isolation for all wallet commands.
  - [ ] **Block**: 12-block confirmation rule for "settled" state.
- [ ] **Reorg Defense**:
  - [ ] **Optimistic Locking**: Use DB versioning for trade state.
  - [ ] **Watcher Service**: Independent daemon verifying past block hashes.
