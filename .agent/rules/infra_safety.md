---
trigger: always_on
glob: ["infra/**/*"]
description: Standards for infrastructure resilience, security, and immutability.
---

# Infrastructure Safety Rules (2027)

## 🛡️ Immutable Infrastructure

- **IaC Sovereignty**: No manual changes to cloud resources. Every modification MUST be committed via Terraform modules in `infra/terraform/`.
- **State Isolation**: environments (Staging/Prod) MUST have separate Terraform state files with mandatory remote locking.

## ☸️ Kubernetes (k8s) Resilience

- **Resource Quotas**: Every pod MUST have `limits` and `requests` defined. No "unbounded" containers.
- **Self-Healing Probes**: All services MUST implement `livenessProbe` and `readinessProbe` with proper timeout logic.
- **Network Policies**: Implement strict "Deny-All" default policies. Explicitly whitelist communication between microservices.

## 🔐 Secret Management

- **External Secrets**: Secrets MUST NEVER be stored in k8s manifests or environment variables. Use `GCP Secret Manager` or `HashiCorp Vault`.
- **Secret Zero**: Automate secret rotation every 30 days using `secret_rotation.py`.

## 📈 Capacity & Scaling

- **Auto-Scaling**: Implement Horizontal Pod Autoscaler (HPA) for all trading-critical services based on CPU and request-per-second (RPS) metrics.

---

// See also: [chaos_engineering.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/workflows/chaos_engineering.md)
