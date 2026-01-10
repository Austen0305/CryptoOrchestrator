
# Backend Execution TODOs

## Phase 3: Critical Fixes & Realification
- [x] **Realify Risk Engine**
  - [x] Replace mock data in `RiskManagementEngine` with real market data provided by `MarketDataService`. (Completed via `get_market_data_service` integration)
  - [x] Integrate real historical volatility calculation.
- [x] **Execution Bridge Implementation**
  - [x] Create `ExecutionService` to bridge `TradingOrchestrator` and `TransactionService`.
  - [x] Implement safety checks in `ExecutionService` before transaction submission.
  - [x] Inject `ExecutionService` into `TradingOrchestrator`.
- [x] **Key Management (Phase 3 Interim)**
  - [x] Implement `LocalEncryptedKeyManager` for local development usage.
  - [x] Update `KeyManagementService` to use local secure storage.

## Phase 4: Core Backend Improvements
- [ ] **Codebase Cleanup (Deep Audit)**
  - [ ] **Database Precision (CRITICAL)**:
    - [ ] **Refactor Models**: Search & Replace all `Float` fields in `models/*.py` with `Numeric(precision=32, scale=18)`.
    - [ ] **Rationale**: `Float` causes rounding errors in Crypto. `DECIMAL` is mandatory for 2026 financial standards.
  - [ ] **Refactor `main.py`**:
    - [ ] **Decomposition**: Extract `setup_middleware` and `lifespan` into `server/core/bootstrap.py`.
    - [ ] **Cleanup**: Remove legacy "Registration shim" comments and unused imports.
  - [ ] **Purge Mocks**:
    - [ ] **Trading**: Delete `trading_orchestrator.py` mock keys (`0x...01`) and replace with `KeyManagementService`.
    - [ ] **Settings**: Remove "Optimized for 2026" magic comments; use distinct config profiles (dev/prod).

- [ ] **Secure Key Management (State of the Art)**
  - [ ] **MPC (Multi-Party Computation)**
    - [ ] **Threshold Signatures (TSS)**: Implement `n-of-m` signing using `IySyft` or `multi-party-sig` (Rust bindings).
    - [ ] **Key Sharding**: Never reconstruct the full private key in memory.
    - [ ] **Nodes**: 1 Share Local, 1 Share AWS KMS, 1 Share User Device (Mobile).
  - [ ] **Encrypted Database Storage (Fallback/Legacy)**
    - [ ] **Schema Design**: Create `secrets` table with `user_id`, `key_ciphertext`, `nonce`, `tag`.
    - [ ] **Zero-Trust Loading**: Logic to fetch encrypted blob and decrypt *only* in memory using transient `MASTER_KEY`.
    - [ ] **Audit**: Ensure `MASTER_KEY` is never printed to logs or stored in variable dumps (use `pydantic.SecretStr`).
  - [ ] **Refactor Execution Bridge**:
    - [ ] **Remove**: Hardcoded `private_key` arguments in `ExecutionService`.
    - [ ] **Inject**: `KeyManagementService` with MPC support.
    - [ ] **Logic**: `execute_trade` calls `mpc_signer.sign(tx_hash, shares)`, ensuring no single point of failure.

- [ ] **Advanced Trading Logic**
  - [ ] **Flashbots Integration** `(Priority: High)`
    - [ ] Install `web3-flashbots`.
    - [ ] Wrap `web3` provider to send "bundles" (private transactions) to avoid mempool sniping.
    - [ ] Use for all standard Uniswap V2/V3 transactions.
  - [ ] **CowSwap (MEV Protection)** `(Priority: High)`
    - [ ] Implement EIP-712 signing for "Intent" based trading.
    - [ ] Use CowSwap API (`api.cow.fi`) to post orders.
    - [ ] **Benefit**: Zero gas fees for failed trades, complete MEV protection.
  - [ ] **DEX Aggregation**
    - [ ] Smart Router: Check CowSwap quote vs Uniswap V3 + Gas. Route to best price.

- [ ] **Financial Integrity (The "Perfect" Standard)**
  - [ ] **Database Integrity**:
    - [ ] **Isolation**: Enforce `isolation_level="SERIALIZABLE"` for all Ledger/Balance updates in SQLAlchemy `async_session`.
    - [ ] **Atomic Locks**: Use `SELECT ... FOR UPDATE` on wallet rows during trade execution.
  - [ ] **Blockchain Resilience**:
    - [ ] **Reorg Handling**:
      - [ ] Add `confirmation_depth` to `transactions` table.
      - [ ] Worker: Only mark trade as `COMPLETED` after 12 confirmations (Ethereum).
      - [ ] **Rollback**: Logic to detect reorg (block hash mismatch) and revert DB state.
    - [ ] **Nonce Management**:
      - [ ] **Redis Counter**: Maintain local nonce counter in Redis (or DB). Do NOT rely on `eth_getTransactionCount` for high-frequency bursts.
      - [ ] **Sync**: On startup, query chain for `latest` nonce and reset Redis counter.
  - [ ] **Performance Safety**:
    - [ ] **CPU Protection**: Offload `account.sign_transaction` (CPU heavy) to `loop.run_in_executor` to prevent blocking the FastAPI event loop.

- [ ] **Core Logic Perfection (Remove Stubs)**
  - [ ] **Market Data Service**:
    - [ ] **Rate Limiter**: Implement **Token Bucket** algorithm (Max 30 req/min global).
      - [ ] Use `asyncio.Lock` for thread safety.
      - [ ] Implement exponential backoff for 429 retries.
    - [ ] **Data Integrity**:
      - [ ] **Strict Typing**: Migrate all data models to **Pydantic V2**. Use `@field_validator` for price sanity checks (e.g., price > 0).
      - [ ] **Error Handling**: Replace generic exceptions with `MarketDataError`, `RateLimitError`.
    - [x] **Removal**: Delete `CoinGeckoService` (DEPRECATED) and move to `MarketDataService`. (Completed)
  - [ ] **Execution Service (Real DEX Integration)**:
    - [ ] **CowSwap (Defacto 2026 Standard)**:
      - [ ] **Intent Architecture**: Replace "Swap" logic with "Signed Intents" (EIP-712).
      - [ ] **MEV Blocker**: Route ALL eligible trades via CowSwap to guarantee MEV protection.
      - [ ] **Fallback**: Uniswap V3 (via Flashbots RPC) ONLY if CowSwap auction fails/timeouts.
    - [ ] **Uniswap V3**: Implement `build_swap_transaction` using `web3.py` and Uniswap Router ABI (Secondary).
  ## Phase 7: Agent & Automation Governance
- [ ] **Agent Guardrails**:
  - [ ] **Proposal-Only Mode**: Ensure agents/ML can only propose, simulate, or analyze trades—never execute them directly.
  - [ ] **Protocol Validation**: Enforce strict JSON schema validation, semantic versioning, and cryptographic hashing of all agent outputs.
  - [ ] **Loop Prevention**: Implement detection for agent self-feedback loops and self-reinforcement biases.
  - [ ] **Reasoning Audit**: Deterministically log all agent reasoning (inputs, constraints, confidence scores, and outputs).

## Phase 8: Risk & Capital Controls
- [ ] **Systemic Safety**:
  - [ ] **Capital Limits**: Enforce hard capital limits per trade, strategy, wallet, user, and globally for the system.
  - [ ] **Circuit Breakers**: Implement auto-disable for strategies exceeding a defined drawdown threshold.
  - [ ] **Exposure Sane Checks**: Validate every transaction for position sizing and total exposure sanity against the `RiskManagementEngine`.
  - [ ] **Human-in-the-Loop**: Require explicit human approval for trades exceeding a "High Risk" threshold.
