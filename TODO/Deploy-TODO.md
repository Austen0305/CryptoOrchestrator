# Deployment & Operations TODOs

## Phase 4: Free-Tier Production Setup (Ops)
- [ ] **Google Cloud Run (API)**
  - [ ] **Config**: Set max-instances=1, memory=512MB (Free Tier limits).
  - [ ] **Secrets**: Inject `MASTER_KEY` and `DB_URL` as Environment Variables.
  - [ ] **Domain Mapping**: Map custom domain in Cloud Run settings.
- [ ] **Google Compute Engine (Bots)**
  - [ ] **Provisioning**: Terraform `e2-micro` instance in `us-central1`.
  - [ ] **Startup Script**: Auto-clone repo, install deps, start `bot_manager.py`.
  - [ ] **Persistence**: Mount 30GB Standard PD for logs/state.
- [ ] **Vercel (Frontend)**
  - [ ] **Build**: Configure `npm run build` output.
  - [ ] **Edge Config**: Set middleware to `us-east1` (closest to users).
  - [ ] **DNS**: Configure A records for root domain.
- [ ] **Supabase (Database)**
  - [ ] **Migration**: CI/CD pipeline runs `alembic upgrade head` on deploy.
  - [ ] **Backups**: Schedule nightly Logical Backups (pg_dump) to GCS.
- [ ] **Observability Pipeline**
  - [ ] **Agent**: Install Google Cloud Ops Agent on Compute Engine.
  - [ ] **Sentry**: Configure DSN in ENV for both backend and frontend.

## Phase 6: Advanced Production Strategies (2026)
  - [ ] **Canary Rollout**: Gradually shift 5% -> 100% traffic based on error rate.

## Phase 7: Deployment Safety & Verification
- [ ] **Build Determinism Verification**:
  - [ ] Add a pipeline step to verify that the produced build artifact hash matches the source state exactly.
- [ ] **Kill Switch Readiness**:
  - [ ] Verify that every deployment includes a tested and functional kill switch handler.

## Quality Gates (Pre-Deploy)
- [ ] **CI Pipeline**: GitHub Actions must pass:
  - [ ] `pytest` (Unit)
  - [ ] `snyk` (Security)
  - [ ] `black --check` (Formatting)
  - [ ] `mypy` (Type Safety)
