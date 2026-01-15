---
name: Chaos Engineering
description: Mandatory workflow for simulating system-wide failures and financial resilience.
---

# Workflow: Chaos Engineering (Financial Resilience)

This workflow verifies that the system can survive extreme conditions without losing user funds or state integrity.

## 📋 Methodology

### 1. 🔍 Target Selection
- Identify critical paths:
  - Wallet balance reconciliation.
  - Trade execution pipeline.
  - Blockchain broadcast queue.

### 2. 🧪 Failure Injector
- **Network Level**: Inject 100ms-500ms jitter and 5% packet loss on the Redis/PostgreSQL paths.
- **Database Level**: Simulate a "Split-Brain" scenario in TimescaleDB.
- **Service Level**: Kill randomized `celery_worker` nodes during active batch processing.

### 3. 🛡️ Resilience Audit
- Verify that **Idempotency Keys** prevented duplicate trades.
- Verify that the `RiskManager` paused trading during the anomaly.
- Verify that all logs are consistent and the `AuditLogService` recorded the failure events.

### 4. 📝 Post-Mortem
- Document "Time to Recovery" (TTR).
- Recommend architectural hardening (e.g., adding circuit breakers or redundant nodes).

---

// turbo-all
