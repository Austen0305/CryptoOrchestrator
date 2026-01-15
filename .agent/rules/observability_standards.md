---
trigger: always_on
glob: ["**/*.{py,ts,tsx}"]
description: Enforce observability and monitoring standards for financial systems.
---

# Observability Standards

## Tracing
- **OpenTelemetry**: All financial path endpoints must be instrumented with OpenTelemetry.
- **Trace Propagation**: Ensure trace context is propagated across service boundaries (Redis, Celery).

## Metrics & Alerting
- **Gold Signals**: Monitor Latency, Traffic, Errors, and Saturation.
- **P99 Latency**: Critical trading paths must remain under 100ms P99.
- **Alert Coverage**: Any new service must include at least one liveness alert and one performance alert.
- **Error Analysis**: Use sentry MCP for production error investigations and mcp:cloudrun_get_service_log or mcp:vercel_getDeploymentEvents for deployment-specific troubleshooting.

## 🌐 Client-Side & Performance
- **Lighthouse Audits**: Use mcp:chrome-devtools to perform automated accessibility and performance audits on all new UI components.
- **DOM Stability**: Monitor layout shifts and memory leaks using chrome-devtools memory snapshots during UI modernization tasks.
