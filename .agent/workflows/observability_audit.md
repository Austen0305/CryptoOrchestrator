---
description: Triggerable check for tracing coverage and alert health.
---

# Observability Audit Workflow

1. **Instrumentation Check**
   - Verify OpenTelemetry middleware is active on all FastAPI routers.
   - Check Celery worker instrumentation.

2. **Metric Validation**
   - Verify Prometheus metrics are being scraped.
   - Validate Grafana dashboard connectivity.

3. **Alert Verification**
   - Perform a "Dry Run" of critical alerts (e.g., Error Rate Spike).
