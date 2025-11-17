# Repository Transfer Guide

Complete guide for transferring CryptoOrchestrator repository to a new owner.

## Overview

This guide explains how to transfer ownership of the CryptoOrchestrator repository, including Stripe account, licensing system, and all associated services.

## Pre-Transfer Checklist

### Repository Preparation

- [x] Remove all sensitive files (.env, API keys, credentials)
- [x] Remove large binary files (database files, models)
- [x] Update .gitignore for all sensitive files
- [x] Create .env.example with placeholders
- [x] Clean git history of secrets (if needed)
- [x] Ensure all documentation is complete
- [x] Verify CI/CD is working
- [x] Run all tests and ensure they pass

### Documentation

- [x] README.md is complete and buyer-friendly
- [x] Installation guide created (docs/installation.md)
- [x] Deployment guide created (docs/deployment.md)
- [x] API documentation available (docs/api.md)
- [x] Architecture documentation complete (docs/architecture.md)
- [x] Licensing documentation complete (docs/licensing.md)

### Security

- [x] All secrets removed from codebase
- [x] .env files removed from git tracking
- [x] Database files removed from repository
- [x] No hardcoded API keys or passwords
- [x] All sensitive data moved to environment variables

## Transfer Process

### Step 1: Repository Transfer

#### GitHub Transfer

1. **Export Repository (if needed):**
   ```bash
   # Create a clean export
   git clone --mirror https://github.com/oldowner/CryptoOrchestrator.git
   cd CryptoOrchestrator.git
   
   # Remove sensitive files from history (if needed)
   # Use BFG Repo-Cleaner or git filter-branch
   
   # Create new repository on buyer's GitHub
   git remote set-url origin https://github.com/newowner/CryptoOrchestrator.git
   git push --mirror
   ```

2. **Transfer Repository:**
   - Go to repository Settings → General → Danger Zone
   - Click "Transfer ownership"
   - Enter new owner username
   - Confirm transfer

#### Alternative: Manual Export

```bash
# Create clean ZIP export (no .git folder)
git archive --format=zip --output=CryptoOrchestrator-clean.zip HEAD

# Or include git history
git clone https://github.com/oldowner/CryptoOrchestrator.git CryptoOrchestrator-transfer
cd CryptoOrchestrator-transfer
# Remove sensitive files
zip -r ../CryptoOrchestrator-transfer.zip .
```

### Step 2: Environment Setup

The buyer must set up their own environment:

1. **Clone Repository:**
   ```bash
   git clone https://github.com/newowner/CryptoOrchestrator.git
   cd CryptoOrchestrator
   ```

2. **Create .env File:**
   ```bash
   cp .env.example .env
   # Edit .env with buyer's own credentials
   ```

3. **Install Dependencies:**
   ```bash
   npm install --legacy-peer-deps
   pip install -r requirements.txt
   ```

4. **Set Up Database:**
   ```bash
   # For SQLite (development)
   # No setup needed, will be created automatically
   
   # For PostgreSQL (production)
   createdb cryptoorchestrator
   alembic upgrade head
   ```

5. **Start Services:**
   ```bash
   # Using Docker (recommended)
   docker-compose up -d
   
   # Or manually
   npm run dev:fastapi  # Backend
   npm run dev          # Frontend
   ```

### Step 3: Stripe Account Transfer

#### Option A: New Stripe Account (Recommended)

1. **Buyer Creates New Stripe Account:**
   - Sign up at https://stripe.com
   - Complete account verification
   - Get API keys from Dashboard

2. **Update Environment Variables:**
   ```env
   STRIPE_SECRET_KEY=sk_live_buyer_new_key
   STRIPE_PUBLISHABLE_KEY=pk_live_buyer_new_key
   STRIPE_WEBHOOK_SECRET=whsec_buyer_new_secret
   ```

3. **Configure Webhooks:**
   - In Stripe Dashboard → Webhooks
   - Add endpoint: `https://buyer-domain.com/api/payments/webhook`
   - Select events: `customer.subscription.*`, `invoice.payment.*`

4. **Update Price IDs (if using):**
   - Create new products and prices in buyer's Stripe account
   - Update `server_fastapi/services/payments/stripe_service.py` with new price IDs

#### Option B: Transfer Existing Stripe Account

1. **Contact Stripe Support:**
   - Email support@stripe.com
   - Request account transfer to buyer's email
   - Provide buyer's details

2. **Buyer Accepts Transfer:**
   - Buyer receives email from Stripe
   - Accepts transfer invitation
   - Completes account verification

3. **Update Credentials:**
   - Buyer logs into Stripe Dashboard
   - Retrieves API keys
   - Updates environment variables

### Step 4: Licensing System

The licensing system is self-contained and doesn't require external services.

1. **Generate New License Secret:**
   ```python
   import secrets
   license_secret = secrets.token_hex(32)
   print(license_secret)
   ```

2. **Update Environment Variable:**
   ```env
   LICENSE_SECRET_KEY=<generated_secret>
   ```

3. **Existing Licenses:**
   - If buyer wants to honor existing licenses, export license database
   - If starting fresh, existing licenses will not validate
   - Buyer can generate new licenses through admin API

### Step 5: Domain & SSL (if applicable)

If the buyer wants to use the existing domain:

1. **Transfer Domain:**
   - Initiate domain transfer at registrar
   - Buyer accepts transfer
   - Update nameservers if needed

2. **Update SSL Certificates:**
   ```bash
   # Using Let's Encrypt
   certbot certonly --standalone -d buyer-domain.com
   
   # Update docker-compose.yml or nginx config with new certs
   ```

3. **Update CORS Settings:**
   - Update `ALLOWED_ORIGINS` in .env
   - Update CORS middleware in `server_fastapi/main.py`

### Step 6: Database Migration (if applicable)

If buyer wants to migrate existing data:

1. **Export Database:**
   ```bash
   # PostgreSQL
   pg_dump -U crypto_user cryptoorchestrator > database_backup.sql
   
   # SQLite
   sqlite3 crypto_orchestrator.db .dump > database_backup.sql
   ```

2. **Transfer Database:**
   - Send encrypted backup to buyer
   - Or provide database access for direct export

3. **Import Database:**
   ```bash
   # PostgreSQL
   psql -U crypto_user cryptoorchestrator < database_backup.sql
   
   # SQLite
   sqlite3 crypto_orchestrator.db < database_backup.sql
   ```

4. **Update Secrets:**
   - Reset all user passwords
   - Regenerate JWT secrets
   - Update exchange API keys
   - Invalidate old licenses

## Post-Transfer Verification

### Functionality Tests

```bash
# Health check
curl http://localhost:8000/healthz

# API endpoints
curl http://localhost:8000/api/status

# Authentication
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Database connection
python scripts/check_db.py
```

### Security Audit

1. **Verify No Secrets in Code:**
   ```bash
   grep -r "password\|secret\|api_key" --exclude-dir=node_modules --exclude="*.example" .
   ```

2. **Check .env is Ignored:**
   ```bash
   git check-ignore .env
   ```

3. **Verify SSL/HTTPS:**
   - Test all endpoints over HTTPS
   - Verify certificate validity

## Buyer Checklist

After receiving the repository, the buyer should:

- [ ] Review all documentation
- [ ] Set up development environment
- [ ] Create production environment variables
- [ ] Set up Stripe account (new or transfer)
- [ ] Configure domain and SSL
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Configure monitoring and logging
- [ ] Set up database backups
- [ ] Test all functionality
- [ ] Review and update security settings
- [ ] Generate new license secret key
- [ ] Update contact information in codebase
- [ ] Update repository description and links
- [ ] Set up support channels

## Ongoing Maintenance

### Regular Tasks

1. **Security Updates:**
   ```bash
   # Update dependencies
   npm audit fix
   pip install --upgrade -r requirements.txt
   ```

2. **Database Backups:**
   ```bash
   # Automated backup script
   ./scripts/backup_db.sh
   ```

3. **Monitor Logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Update Documentation:**
   - Keep README.md current
   - Update API docs when endpoints change
   - Maintain changelog

## Support Resources

### Documentation

- **Installation:** [docs/installation.md](docs/installation.md)
- **Deployment:** [docs/deployment.md](docs/deployment.md)
- **API Reference:** [docs/api.md](docs/api.md)
- **Architecture:** [docs/architecture.md](docs/architecture.md)
- **Licensing:** [docs/licensing.md](docs/licensing.md)

### Troubleshooting

- **Common Issues:** [docs/troubleshooting/common_issues.md](docs/troubleshooting/common_issues.md)
- **FAQ:** [docs/troubleshooting/faq.md](docs/troubleshooting/faq.md)

### External Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **React Docs:** https://react.dev
- **Stripe Docs:** https://stripe.com/docs
- **Docker Docs:** https://docs.docker.com

## Important Notes

1. **Secrets:** Never commit .env files or secrets to the repository
2. **Database:** Start fresh or securely migrate existing data
3. **Licenses:** Existing licenses may not work with new secret key
4. **Stripe:** Must set up new account or transfer existing one
5. **Domain:** Update DNS and SSL certificates for production

## Contact

For questions about the transfer process:
- Review all documentation first
- Check troubleshooting guides
- Open an issue on GitHub (if repository access allows)

---

**Last Updated:** 2025-01-15  
**Repository Version:** 1.0.0  
**Transfer Status:** Ready for Transfer

