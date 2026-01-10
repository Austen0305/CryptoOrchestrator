
# Blockchain & DEX Execution TODOs

## Phase 3: Bridge & Basic Execution
- [x] **Transaction Service Bridge**
  - [x] Verify connectivity between `ExecutionService` and `TransactionService`.
  - [x] Ensure gas estimation and signing (with local keys) works.

## Phase 4: Advanced DeFi Integration
- [ ] **DEX Aggregation**
  - [ ] Implement smart routing (1inch or internal logic) to find best prices.
  - [ ] Add slippage protection and deadline management.
- [ ] **Smart Contract Interaction**
  - [ ] Integrate full ABI support for major protocols (Uniswap, Aave, Compound).
  - [ ] Add event listening for transaction confirmation and receipt parsing.
- [ ] **MEV Protection**
  - [ ] Fully enable and test Flashbots / MEV-Blocker integration.
