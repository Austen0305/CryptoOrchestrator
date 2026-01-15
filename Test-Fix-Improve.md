# Test-Fix-Improve: CryptoOrchestrator 2026/2027 Upgrade Path

**Status**: DRAFT (Awaiting Architect Approval)
**Date**: January 2026
**Target**: Full Regulatory Compliance (MiCA/GENIUS) & ISO 20022 Standards

This document serves as the master roadmap for aligning CryptoOrchestrator with 2026 regulatory standards and modernizing the technical stack. It results from a deep audit of the code, infrastructure, and compliance posture.

---

## 🔍 Executive Summary

The platform is currently **technically functional but regulatory non-compliant**. While the core trading logic works, it lacks the mandatory surveillance, reporting, and safety guardrails required for a 2026 CASP (Crypto-Asset Service Provider) license.

**Key Risks identified:**

1. **Regulatory**: Missing MiCA Article 16 (Market Abuse) surveillance and Article 92 (Reporting) schemas.
2. **Safety**: "Fail-Open" risks in trading services if RiskManager is unreachable.
3. **Security**: Use of mock signing concepts instead of production MPC (Threshold Signatures).
4. **Performance**: Critical bottlenecks in `IndicatorEngine` due to legacy Pandas usage (~150ms latency vs 50ms target).

## 🚨 Deep Scan & Test Findings (Jan 2026)

The following issues were confirmed via code inspection and verification script runs:

### 1. Critical Security Vulnerabilities

- **Public Cloud Run Access**: `terraform/gcp/main.tf` grants `roles/run.invoker` to `allUsers`. This exposes the financial backend to the public internet.
- **Hardcoded Database Credentials**: DB connection strings are constructed using variables in `main.tf` but injected as plain environment variables `DATABASE_URL`, visible in the Cloud Console.
- **Mock Signing**: `signer/src/lib.rs` uses `thread::sleep` to simulate signing. No actual private key operations occur.

### 2. Regulatory Implementation Gaps

- **Tax Reporting**: `Form8949Generator.py` hardcodes symbol to "Cryptocurrency" and lacks 1099-DA specific fields (e.g., Digital Asset Address, Sale Transaction ID).
- **Market Surveillance**: `SentinelService.detect_layering()` is a placeholder returning `None`. Spoofing detection is non-existent.

### 3. Technical Stability & Debt

- **React 19 Type Mismatch**: `client/package.json` installs `react@19.0.0` but uses `@types/react@18.3.3`. This causes TypeScript compilation errors in verification scripts.
- **Async Context Crash**: `AdvancedRiskManager` is used as an async context manager (`async with...`) in startup scripts, but the class does not define `__aenter__` or `__aexit__`, causing crashes.

### 4. Application Logic & Infrastructure Findings

- **Mobile Architecture**: Uses `axios` instead of `fetch` (bloat). Charts use `react-native-chart-kit` (JS-based, slow) instead of Skia-based solutions. missing `flash-list` for high-frequency orderbooks.
- **Electron Security**: `main.ts` does not implement a "Secure Enclave" pattern for key storage, relying on standard disk I/O.
- **Database Schema**: While many 2026 indexes exist, the `Trade` table lacks specific columns for `uti` (Unique Transaction Identifier) and `venue_reporting_id` required by ISO 20022.

### 5. Holistic Quality & DevOps Findings

- **Frontend "Split-Brain" Architecture**: The project contains both `panda.config.ts` and `tailwind.config.ts`. `index.css` uses Panda syntax (`token(...)`) but lacks the required Tailwind CSS variable definitions (`:root { --background: ... }`). This guarantees broken UI rendering.
- **CI/CD Gaps**: `.github/workflows/ci.yml` completely ignores **Mobile** and **Electron** builds. There is no automated testing for these critical platforms.
- **Tooling Logic Error**: `pyproject.toml` sets `requires-python = ">=3.12"` but configures MyPy to check for `python_version = "3.8"`. This invalidates type-checking for modern async features.
- **Design System Integrity**: `tailwind.config.ts` mixes HSL variables with hardcoded HEX codes (`#00d2ff`), breaking the dark/light mode switching capability.
- **DevEx & Observability**: `docker-compose.yml` uses hardcoded credentials (`crypto_pass`) and lacks the mandatory Observability Stack (Prometheus/Grafana/Jaeger) defined in `rules/observability_standards.md`.
- **Database Integrity**: Migration history contains multiple `merge_heads` scripts, indicating a fractured schema evolution. TimescaleDB extension is not explicitly enabled in the Docker composition, risking performance on time-series data.

### 6. Advanced Architecture & Future-Proofing Findings

- **Signer "Security Theater"**: `signer/Cargo.toml` only includes `k256` (single-key ECDSA). It completely lacks the required Threshold Signature Scheme (TSS) libraries (`multi-party-ecdsa` or `frost-dalek`) mandated by the Security Standards. This is a critical failure of the "MPC" requirement.
- **ML Fragility**: The `ml/` directory contains sophisticated models (`transformer_engine.py`) but **zero** adversarial defenses. A `grep` for "adversarial" returned no results, meaning the system is vulnerable to gradient-based attacks on market data.
- **Frontend Architecture Mismatch**: The project uses standard Vite SPA (`@vitejs/plugin-react`). This makes the "React 19 Server Components" requirement impossible to fulfill without a migration to Next.js or Waku. The current architecture exposes all logic to the client side.

---

## 📋 Detailed Audit Findings

### 1. Regulatory & Compliance (MiCA / GENIUS Act)

| Component | Finding | Context / Requirement | Severity |
| :--- | :--- | :--- | :--- |
| **Market Abuse (Art. 16)** | `SentinelService` only checks for simple wash trading. No spoofing/layering detection. | **MiCA Art. 16**: Requires effective systems to detect and report market abuse. Non-compliance = License Revocation. | **CRITICAL** |
| **Reporting (ISO 20022)** | `AuditLogService` uses arbitrary JSON. No alignment with `auth.*` schemas. | **MiCA RTS 2026**: Transaction reports to competent authorities must use ISO 20022 semantic models. | **HIGH** |
| **Stablecoins (Art. 19)** | No logic to distinguish "Permitted Payment Stablecoins" (PPSIs). | **GENIUS Act / MiCA**: Trading unauthorized stablecoins is strictly prohibited. Need whitelist filter in `validation_2026.py`. | **CRITICAL** |
| **Tax (IRS 1099-DA)** | `Form8949Generator.py` is hardcoded. Lacks basis tracking. | **IRS 2026**: Brokers must report gross proceeds AND cost basis on Form 1099-DA. | **CRITICAL** |
| **Travel Rule** | No logic for FinCEN >$3k threshold or counterparty data collection. | **FinCEN Rule**: Mandatory PII transmission for transfers >$3k. | **CRITICAL** |

### 2. Architecture & Performance

| Component | Finding | Context / Requirement | Severity |
| :--- | :--- | :--- | :--- |
| **Risk Manager** | `AdvancedRiskManager` lacks `__aenter__`/`__aexit__` protocol. | Causes startup crashes and prevents proper async resource cleanup. | **BLOCKER** |
| **Data Engine** | `IndicatorExecutionEngine` uses `pandas` loops & `RestrictedPython`. | **Latency**: `iterrows()` is O(N). **Requirement**: Move to Polars for SIMD vectorization (<10ms). | **HIGH** |
| **Event Bus** | `datetime.now()` default in `events.py` implies static import time. | **Auditability**: Events are timestamped at server start, not occurrence. Destroys audit sequence. | **HIGH** |
| **Dependencies** | `axios` usage in frontend despite `fetch` standardization. | **Tech Debt**: Increases bundle size and fragmentation. Standardize on Native Fetch. | **MEDIUM** |

### 3. Security & Cryptography

| Component | Finding | Context / Requirement | Severity |
| :--- | :--- | :--- | :--- |
| **Signing** | `signer/src/lib.rs` uses `thread::sleep` mocks. | **False Security**: Current signer is a placeholder. Needs real `ethers-rs` / KMIP integration. | **CRITICAL** |
| **Secrets** | `terraform/gcp/main.tf` has hardcoded `DATABASE_URL`. | **Secret Management**: Plaintext secrets in IaC are a guaranteed breach. Use GCP Secret Manager. | **CRITICAL** |
| **MPC Wallets** | `mpc_service.py` uses `hashlib` mocks. No TSS/sharding. | **Custody Risk**: Single-point-of-failure for keys. Need GG20/FROST (Threshold-ECDSA). | **CRITICAL** |
| **Infrastructure** | Cloud Run allowed `allUsers` (Public). | **Access Control**: Backend must be behind IAP (Identity-Aware Proxy) or strictly internal. | **CRITICAL** |

---

## 🛠️ The Rebuild Roadmap

### Phase 1: Foundation & Safety (Immediate / Week 1)

*Goal: Fix critical blockers and close "Fail-Open" security gaps.*

1. **Fix `AdvancedRiskManager` Protocol** (`server_fastapi/core/risk_manager.py`)
   - Implement `__aenter__` and `__aexit__` to ensure the risk engine initializes/teardowns correctly.
2. **Secret Hardening** (`infra/terraform/`)
   - Migrate `DATABASE_URL` and `JWT_SECRET` to GCP Secret Manager.
   - Update Terraform to inject secrets as mounted volumes or env vars from SecretSource.
   - **Remove `allUsers` IAM binding** from Cloud Run services.
3. **Fail-Closed Trading** (`DEXTradingService.py`)
   - Wrap trade execution in a mandatory Risk Check block. If Risk Service is down, Trade **MUST** fail.
   - Remove any `try/except` that defaults to "allow" on risk check failure.
4. **Startup Verification Fix** (`scripts/verification/`)
   - Update verify scripts to properly mock `AsyncSession` for service instantiation.

### Phase 2: Regulatory Core (Week 2-3)

*Goal: Implement mandatory reporting and surveillance for MiCA/USA compliance.*

- [x] **ISO 20022 Data Mapper** (`server_fastapi/schemas/iso20022.py`)
  - Verified Pydantic models for MiCA-compliant transaction reports.
- [x] **Sentinel Upgrade: Spoofing** (`server_fastapi/services/sentinel_service.py`)
  - Implemented "Windowed Imbalance" (Layering) and "Spoofing" detection (Life < 5s).
- [x] **Travel Rule Service** (`server_fastapi/middleware/regulatory_filter.py`)
  - Enforced IVMS-101 payload structure for transfers.
- [x] **IRS 1099-DA Engine** (`server_fastapi/services/tax_calculation_service.py`)
  - Added digital asset address and transaction hash tracking for 2026 reporting.
  - Updated Form 8949 Generator to include new columns.

### Phase 3: High-Performance Rebuild (Week 4-6)

*Goal: Achieve <50ms decision latency using Rust and Polars.*

1. **Polars Transition** (`analytics.py`, `volume_profile.py`)
   - Replace `pandas.DataFrame.apply` with `polars.Expr`.
   - Use `lazy()` execution graphs for complex indicator chains.
2. **Event Bus Refactor** (`core/events.py`)
   - Fix timestamp bug: Use `default_factory=datetime.now` (not `default=datetime.now()`).
   - Ensure all events carry `correlation_id` and `causation_id` for OTEL tracing.
3. **Frontend Modernization** (`client/src/`)
   - Migrate Data Grids to `TanStack Table` (virtualized).
   - Implement `useActionState` (React 19) for all trade forms to handle pending/error states natively.
4. **Mobile List Optimization** (`mobile/src/`)
   - Replace `FlatList` with `@shopify/flash-list` for Orderbook/Trade History.

### Phase 4: Advanced Security (Week 7+)

*Goal: Production-grade custody and Zero-Knowledge audits.*

1. **MPC Signer Integration** (`signer/`)
   - Replace mock Rust signer with `ethers-rs` + `k256` implementation.
   - (Optional) Integrate a TSS library (e.g., `zenroom` or `multi-party-ecdsa`) if implementing full sharding.
2. **Zero-Knowledge Proofs** (`zkp_service.py`)
   - Implement a simple circuit (Halo2/SnarkJS) to prove "Solvency" (Assets > Liabilities) without revealing total user funds.
3. **Chaos Engineering** (`scripts/testing/chaos/`)
   - Implement `NetworkPartition` and `PodKill` scenarios to verify system resilience.
   - Verify that `RiskManager` halts trading during partition.

---

### ✅ Definition of Done (DoD)

- [ ] All "Critical" findings in Audit Part 1 resolved.
- [ ] Verification script `check:all` passes with 0 failures.
- [ ] `SentinelService` detects simulated Spoofing attack.
- [ ] Trade latency P99 < 50ms verified by OTEL.
- [ ] No plaintext secrets in Git or Terraform state.
