---
trigger: always_on
glob: ["server_fastapi/**/*"]
description: Mandatory standards for ML model integrity, safety, and adversarial robustness.
---

# ML Integrity & AI Safety Standards

AI and ML services in CryptoOrchestrator must be deterministic, auditable, and resilient to adversarial attacks.

## 🛡️ Safety Circuit Breakers

- **Fallbacks**: If ML inference latency exceeds 50ms or confidence falls below 75%, the system **MUST** fallback to the rule-based `RiskManager`.
- **Sanity Checks**: Every ML-generated signal **MUST** pass through a hard-coded "Sanity Filter" (e.g., checking if the proposed trade size is >10% of total wallet balance).

## 🕵️ Adversarial Robustness

- **Adversarial Testing**: All models must undergo periodic adversarial testing (FGSM, PGD) to ensure resilience against "Market Noise" attacks.
- **Data Provenance**: All training data sources must be cryptographically signed and tracked via the `AuditLogService`.

## 📜 Auditability & Governance

- **Model Versioning**: Every inference output must be logged with:
  - `model_version`
  - `inference_latency`
  - `confidence_score`
  - `input_snapshot_hash`
- **Bias Monitoring**: Implement real-time monitoring for execution bias across different asset classes.

## 🚀 Performance

- **Quantization**: High-frequency models must use INT8/FP16 quantization to meet the 50ms p99 budget.
- **Edge Inference**: Preference for on-node inference to minimize network-induced jitter.
