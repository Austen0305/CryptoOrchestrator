
# Analytics & Observability TODOs

## Phase 3: Technical Metrics
- [ ] **Application Performance (Free)**
  - [ ] **Sentry (Free Tier)**:
    - [ ] Instrument API for error tracking (Free tier limit is generous for side projects).
    - [ ] Set up performance monitoring (limited span retention).
- [ ] **System Health**
  - [ ] Monitor Redis queue depth and worker utilization.

## Phase 4: Business Intelligence
- [ ] **Trading Analytics (Free Stack)**
  - [ ] **PostHog (Free Tier)**:
    - [ ] **Events**: Track "Trade Executed", "Signal Generated" as custom events (Limit 1M/mo).
    - [ ] **Dashboards**: Build "Profit/Loss" and "Volume" dashboards in PostHog.
  - [ ] **Google Analytics 4**: Use for basic web traffic/user acquisition data (Free).
- [ ] **User Behavior**
  - [ ] Track user funnel (Signup -> Deposit -> First Trade).
  - [ ] Analyze retention cohorts.

## Phase 5: Reporting
- [ ] **Automated Reports**
  - [ ] **Admin Dashboard**: System-wide financial health (Total AUM, Net Exposure).
  - [ ] **Advanced PnL (2026 Standard)**:
    - [ ] **Slippage Attribution**: Calculate `Implementation Shortfall` (Arrival Price vs Executed Price).
    - [ ] **Real-time Attribution**: Decompose PnL into Alpha (Strategy) vs Beta (Market) vs Cost (Fees/Slippage).

## Phase 6: Audit & Full Traceability
- [ ] **Immutable Audit Trails**:
  - [ ] Enforce append-only storage for all financial logs; verify integrity using cryptographic hashes or ZK-proofs.
- [ ] **Full Lineage Verification**:
  - [ ] Implement a trace utility to prove the entire lineage of every trade: `User -> Strategy -> Model -> Simulation -> Execution -> Chain TX`.
  - [ ] **Anomaly Alerting**: Set up automatic alerts for P99 latency spikes in critical trading paths (>100ms).
