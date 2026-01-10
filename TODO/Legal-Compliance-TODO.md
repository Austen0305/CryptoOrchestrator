
# Legal & Compliance TODOs

## Phase 3: Data Privacy (GDPR/CCPA)
- [ ] **Data Rights**
  - [ ] Implement `POST /api/privacy/export` to generate a ZIP of all user data.
  - [ ] Implement `DELETE /api/privacy/erasure` for "Right to be Forgotten".
- [ ] **Consent**
  - [ ] Add granular Cookie Consent banner (Essential vs Analytics).


## Phase 4: Financial Compliance (2025-2026)
- [ ] **UK Tax Compliance (CARF 2026)**
  - [ ] **Mandatory Data Collection (Jan 1, 2026 Deadline)**:
    - [ ] Update Schema: `users` table must store:
      - [ ] **Tax Residency** (ISO 3166 code)
      - [ ] **TIN** (Tax Identification Number) for *all* jurisdictions of residence.
      - [ ] **Date of Birth** & **Place of Birth**.
  - [ ] **Reporting Engine (Internal/Free)**:
    - [ ] Generate XML/CSV reports strictly adhering to HMRC "Exchange of Information" specs.
    - [ ] Track & Report: Spot Trades, Staking Rewards, Airdrops, and **Wallet Transfers** (External vs Internal).
    - [ ] Flag "Stablecoin" transactions explicitly (Article 23 alignment).

- [ ] **US GENIUS Act Compliance (Enacted July 2025)**
  - [ ] **Stablecoin Restrictions**:
    - [ ] **Issuer Whitelist**: Only permit trading of stablecoins from issuers with:
      - [ ] Federal License (if > $10B issuance).
      - [ ] State Quailified License (if < $10B issuance).
    - [ ] **Algorithmics**: BLOCK all algorithmic stablecoins not meeting "Endogenous Collateral" rules.
  - [ ] **July 2026 Readiness**:
    - [ ] Prepare system for "Proof of Reserves" API ingestion (Auditor Oracle).

- [ ] **KYC/AML (Free Approach)**
  - [ ] **Self-Hosted Verification**:
    - [ ] Build internal "Admin Portal" for manual document upload and review (passport/selfie).
    - [ ] Use free sanctions lists (OFAC/UN) via public CSVs for name screening.
  - [ ] **Risk**: Manual process is unscalable, but free. Automate list checking with Python scripts.

## Phase 5: MiCA Alignment (EU)
- [ ] **Algorithmic Stablecoins**
  - [ ] **Prohibition**: Explicitly block trading pairs for non-compliant algorithmic stablecoins (Article 23).
- [ ] **Transparency**
  - [ ] Publish "Proof of Solvency" reports signed by external auditors (or cryptographic proof via **ZK-Merklized Sum Trees**).
  - [ ] Disclose all trading fees and "spread" mechanics clearly in the UI.

