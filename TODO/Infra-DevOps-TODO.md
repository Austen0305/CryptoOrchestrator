
# Infrastructure & DevOps TODOs

## Phase 3: Containerization & Local Dev
- [ ] **Dockerization (2026 Standards)**
  - [ ] **Optimization**: Refactor `Dockerfile` for backend to use 2026 best practices (uv/pdm for fast installs, distroless images).
  - [ ] **Frontend**: Create `Dockerfile` using NGINX unprivileged (security best practice).
  - [ ] Refine `docker-compose.yml` for full stack local dev (App, DB, Redis).

## Phase 4: CI/CD Pipeline
- [ ] **GitHub Actions**
  - [ ] Pipeline: "Lint & Test" on every PR.
  - [ ] Pipeline: "Build & Push" to registry on merge to main.
  - [ ] Pipeline: "Security Scan" (Trivy/Snyk) on schedule.

## Phase 5: Production Deployment (GCP)
## Phase 5: Production Deployment (Free Tier GCP)
- [ ] **Terraform (GCP & Supabase)**
  - [ ] **State**: Store Terraform state in a free GCS bucket (Encryption disabled to save KMS cost, secure via ACL).
  - [ ] **Compute (Terraform Resource Definitions)**:
    - [ ] `google_cloud_run_service`: Hardcode `max_scale = 1` and `memory = "512Mi"` to enforce Free Tier.
    - [ ] `google_compute_instance`: Define `manchine_type = "e2-micro"` validation rule.
  - [ ] **Networking**: Define `google_compute_network` (Default VPC) in code.
- [ ] **Observability (Free)**
  - [ ] **Logging**: Cloud Logging (Free 50GB/mo).
  - [ ] **Application Monitoring**: PostHog (Client-side) + Sentry (Free Tier) for Backend Errors.

## Phase 6: Disaster Recovery
- [ ] **Database Backups (Supabase)**
  - [ ] **Daily Backups**: Supabase Free Tier includes basic database backups.
  - [ ] **Manual Dump**: Cron job on `e2-micro` to run `pg_dump` and upload to GCS (Free Tier storage class) for redundancy.

## Phase 7: Environment & Build Integrity
- [ ] **Environment Parity**:
  - [ ] Enforce strict configuration parity between Dev, Staging, and Production environments (via terraform/k8s).
- [ ] **Deterministic Builds**:
  - [ ] Implement and verify deterministic build pipelines for both backend (uv/docker) and frontend (vite/docker).
- [ ] **Global Kill Switch**:
  - [ ] Implement a system-wide "Global Kill Switch" that can be triggered locally or via CLI to halt all execution immediately.
  - [ ] **Verification**: Conduct quarterly drills to test the kill switch in a non-production (staging) environment.
