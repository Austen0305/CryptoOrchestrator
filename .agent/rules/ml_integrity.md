---
trigger: always_on
glob: "server_fastapi/services/ml/**/*"
description: Guardrails for ML inference and model usage.
---

# ML Integrity Rule

Ensure safety, performance, and auditability of AI/ML services.

## Performance & Resilience`r`n- **Graceful Degradation**: If inference latency exceeds the 50ms budget, the system MUST fallback to the rule-based `RiskManager` without interrupting the execution pipeline.
- **Latency Budget**: Inference must stay within defined thresholds (e.g., <50ms for trading signals).
- **Fallbacks**: Provide static or rule-based fallbacks if ML services fail or time out.

## Logic Guards
- **Sanity Checks**: ML-generated signals must pass through the RiskManager before execution.
- **Auditability**: Log model version and prediction confidence with every signal.

