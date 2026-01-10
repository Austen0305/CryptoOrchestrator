
# Blockchain & DEX Execution TODOs

## Phase 3: Bridge & Basic Execution
- [x] **Transaction Service Bridge**
  - [x] Verify connectivity between `ExecutionService` and `TransactionService`.
  - [x] Ensure gas estimation and signing (with local keys) works.

## Phase 4: Advanced DeFi Integration & Resilience
- [ ] **Strict Chain Abstraction Layer**:
  - [ ] Implement a standardized `Simulate -> Estimate Gas -> Submit -> Confirm` pipeline.
  - [ ] **Failure Handling**: Robust logic for chain halts, RPC failures, and reorgs (depth 1-5 blocks).
  - [ ] **Reconciliation**: Automatically reconcile partial fills and handle delayed confirmations without state corruption.
- [ ] **DEX Aggregation & Protection**:
  - [ ] **Price Integrity**: Implement smart routing with strict slippage, gas, and MEV protection (Flashbots/CowSwap).
  - [ ] **Safety Bounds**: Reject any transaction where estimated gas > profit or slippage > max threshold.
- [ ] **Smart Contract Interaction**:
  - [ ] Integrate full ABI support for major protocols (Uniswap, Aave, Compound).
  - [ ] Add event listening for transaction confirmation and deep receipt parsing.
