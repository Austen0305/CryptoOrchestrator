# Infrastructure Directory Map

Mapping for deployment, orchestration, and environment configuration.

## 🐳 Containerization

- **Optimized Backend:** [Dockerfile.optimized](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/Dockerfile.optimized)
- **Frontend Docker:** [Dockerfile.frontend](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/Dockerfile.frontend)
- **Compose (Prod):** [docker-compose.prod.yml](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/docker-compose.prod.yml)

## ☸️ Kubernetes (k8s/)

Located in [k8s/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/k8s/):
- **Deployments:** Service-specific manifests.
- **ConfigMaps:** Environment-agnostic configurations.
- **Ingress:** Traefik and Nginx routing rules.

## 🌍 Infrastructure as Code (IaC)

Located in [terraform/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/terraform/):
- **Modules:** Reusable cloud resources (GCP/AWS).
- **Environments:** Staging, Production, and Sandbox.

## 📊 Observability

- **Prometheus/Grafana:** [grafana/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/grafana/)
- **Logging:** [loki/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/loki/)
- **Tracing:** OpenTelemetry configurations.
