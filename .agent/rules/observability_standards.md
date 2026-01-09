Priority: HIGH
Scope: FULL
Overrides: NONE

---
trigger: always_on
glob: "server_fastapi/**/*"
description: Standards for observability and metrics.
---

# Observability Standards

## Tracing
- **OpenTelemetry**: All financial path endpoints must be instrumented with OpenTelemetry.
- **Trace Propagation**: Ensure trace context is propagated across service boundaries (Redis, Celery).

## Metrics & Alerting
- **Gold Signals**: Monitor Latency, Traffic, Errors, and Saturation.
- **P99 Latency**: Critical trading paths must remain under 100ms P99.
- **Alert Coverage**: Any new service must include at least one liveness alert and one performance alert.`r`n- **Error Analysis**: Use `sentry` MCP for all production error investigations and trace detailed root causes.


