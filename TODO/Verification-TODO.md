# Verification & QA Plan - Definition of "Perfection"

This document serves as the **Definition of Done** for the CryptoOrchestrator "Perfection" initiative. All items must pass before any production deployment.

## 1. Safety & Security Verification ("The Red Line")
- [ ] **Secret Scan**: Run `gitleaks` or `trufflehog` to ensure **ZERO** hardcoded keys remain.
  - [ ] Specific check: `grep -r "0x" .` to find any potential lingering mock addresses/keys.
- [ ] **Key Management Integration**:
  - [ ] Verify `ExecutionService` fails immediately if `MASTER_KEY` env var is missing.
  - [ ] Verify `ExecutionService` successfully decrypts a test key from Supabase and signs a dummy message (offline).
- [ ] **Mock Removal Confirmation**:
  - [x] **Market Data**: Verify `MarketDataService` throws an explicit error (or alerts) on network failure, instead of falling back to "mock" prices. (Uses CoinCap w/ CoinLore fallback)
  - [ ] **Bot List**: Verify `TradingOrchestrator` calls Supabase `user_bots` table. Empty table = Empty list (NOT mock list).

## 2. Infrastructure Limits (Free Tier)
- [ ] **Rate Limiter Stress Test**:
    - [x] Simulate ~3 requests/sec (burst) or 200/min to `MarketDataService`.
    - [x] Verify `TokenBucket` correctly throttles downstream calls to ~200/min (CoinCap free tier).
    - [x] Verify no "429 Too Many Requests" from external API.
- [ ] **Memory Pressure**:
    - [ ] Run bot engine on `t3.micro` or local Docker (512MB RAM limit).
  - [ ] Verify no `OOMKilled` events during normal operation + 1 ML model load.

## 3. End-to-End Logic (The "Perfect" Flow)
- [ ] **DEX Integration**:
  - [ ] **Uniswap V3**: Generate a stored transaction payload for a Swap. Verify `calldata` is correct against V3 ABI.
  - [ ] **CowSwap**: Generate an EIP-712 Order. Verify signature recovers to the correct bot wallet address.
- [ ] **Risk Engine Gates**:
  - [ ] Submit a trade violating Max Drawdown.
  - [ ] Verify `RiskManagementEngine` returns `False` and **NO** transaction builds.

## 4. Frontend & User Experience
- [ ] **Vercel Limits**:
  - [ ] Verify bundle size is < 1MB (gzip) for fast Edge loading.
  - [ ] specific check: Ensure no heavy server-side processing in Edge Middleware (CPU limit).

## 6. Deterministic Proof & Reliability
- [ ] **Deterministic Replay Tests**:
  - [ ] Create a "Time Machine" test suite that replays past historical data through the entire pipeline (Model -> Risk -> Execution) and verifies exact identical outputs.
- [ ] **Paper-to-Live Shadow Mode**:
  - [ ] Require mandatory 48-hour "Shadow Trading" on every new strategy version before real capital is deployed.
- [ ] **Disaster Recovery Drills**:
  - [ ] Conduct automated "Chaos Drills": Simulate API outages, sudden 10% price drops, and database connection loss.
  - [ ] Verify the system enters a safe "Pause" state and the **Global Kill Switch** successfully terminates all in-flight execution.
