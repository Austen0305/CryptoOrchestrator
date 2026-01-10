# Verification & QA Plan - Definition of "Perfection"

This document serves as the **Definition of Done** for the CryptoOrchestrator "Perfection" initiative. All items must pass before any production deployment.

## 1. Safety & Security Verification ("The Red Line")
- [ ] **Secret Scan**: Run `gitleaks` or `trufflehog` to ensure **ZERO** hardcoded keys remain.
  - [ ] Specific check: `grep -r "0x" .` to find any potential lingering mock addresses/keys.
- [ ] **Key Management Integration**:
  - [ ] Verify `ExecutionService` fails immediately if `MASTER_KEY` env var is missing.
  - [ ] Verify `ExecutionService` successfully decrypts a test key from Supabase and signs a dummy message (offline).
- [ ] **Mock Removal Confirmation**:
  - [ ] **Market Data**: Verify `MarketDataService` throws an explicit error (or alerts) on network failure, instead of falling back to "mock" $45k BTC.
  - [ ] **Bot List**: Verify `TradingOrchestrator` calls Supabase `user_bots` table. Empty table = Empty list (NOT mock list).

## 2. Infrastructure Limits (Free Tier)
- [ ] **Rate Limiter Stress Test**:
  - [ ] Simulate 100 requests/sec to `MarketDataService`.
  - [ ] Verify `TokenBucket` correctly throttles downstream calls to ~30-50/min (CoinGecko free tier).
  - [ ] Verify no "429 Too Many Requests" from external API.
- [ ] **Memory Pressure**:
  - [ ] Run bot engine on `e2-micro` equivalent (512MB RAM limit).
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

## 5. Compliance
- [ ] **Audit Trail**:
  - [ ] Execute a `stop_bot` command.
  - [ ] Verify an entry appears in Supabase `audit_logs` table AND Google Cloud Logging.
