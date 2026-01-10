# Master TODO List - CryptoOrchestrator

## Phase 1: Codebase Audit & Architecture Planning
- [x] **Audit Risk Management Engine**
    - [x] `server_fastapi/services/risk/risk_management_engine.py`: Identified mock data usage.
    - [x] Verify `should_stop_trading` implementation logic against real-money constraints.
- [x] **Audit Main Entry Point**
    - [x] `server_fastapi/main.py`: Refactor monolithic structure into modular routers and lifespan handlers.
    - [x] Verify middleware ordering and configuration.
- [x] **Audit Transaction Safety**
    - [x] Verify `RealMoneyTransactionManager` usage across all financial endpoints.
    - [x] Enforce idempotency keys on all POST/PUT requests in `server_fastapi/routes`.
- [x] **Audit Validation Layer**
    - [x] Enforce `validation_2026.py` usage in all Pydantic models.
    - [x] Add explicit EIP-55 checksum validation for all address inputs.
- [x] **Populate Architecture TODOs**
    - [x] Complete `Architecture-TODO.md` with Trust Model and Failure Domains.

## Phase 2: Architecture & Trust Model
- [x] Refine `Architecture-TODO.md`.
- [x] Define explicit Trust Boundaries (User vs Server vs Blockchain).
- [x] Document Failure Domains and recovery strategies.

## Phase 3: Frontend Execution
- [ ] See `Frontend-TODO.md`.

## Phase 4: Backend Execution
- [ ] See `Backend-TODO.md`.

## Phase 5: Blockchain & DEX Execution
- [ ] See `Blockchain-TODO.md`.

## Phase 6: ML / Strategy Engine
- [ ] See `ML-TODO.md`.

## Phase 7: Security Hardening
- [ ] See `Security-TODO.md`.

## Phase 8: Infra & DevOps
- [ ] See `Infra-DevOps-TODO.md`.

## Phase 9: Product & Monetization
- [ ] See `Product-TODO.md`.

## Phase 10: Analytics & Observability
- [ ] See `Analytics-TODO.md`.

## Phase 11: Legal & Compliance
- [ ] See `Legal-Compliance-TODO.md`.

## Phase 12: Launch Readiness
- [ ] See `Launch-TODO.md`.

## Phase 13: Post-Launch Evolution
- [ ] See `Post-Launch-TODO.md`.
