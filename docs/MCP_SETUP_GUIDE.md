# MCP Integration Setup Guide

This guide explains how to configure Model Context Protocols (MCPs) to help finish the CryptoOrchestrator project.

## Overview

MCPs provide automated integrations with external services to streamline development, testing, and deployment. This project includes scripts and configurations for the following MCP integrations:

1. **GitHub MCP** - Release automation, CI/CD completion
2. **PostgreSQL/Database MCP** - Test database isolation, migrations
3. **Docker MCP** - Deployment automation, container builds
4. **Testing MCP** - E2E tests, coverage improvements
5. **Secrets Management MCP** - Secret rotation, secure storage
6. **Redis MCP** - Production setup, caching
7. **Monitoring MCP** - Sentry, Prometheus, Grafana
8. **Code Quality MCP** - Snyk, SonarQube, dependency scanning

## Prerequisites

### Required Tools

```bash
# Python dependencies (already in requirements.txt)
pip install -r requirements.txt

# Additional MCP-specific tools
pip install httpx boto3 hvac  # For secrets management
pip install sentry-sdk[fastapi]  # For error tracking

# Node.js dependencies (already in package.json)
npm install --legacy-peer-deps

# Docker (for deployment)
docker --version
docker-compose --version

# Playwright (for E2E tests)
npx playwright install
```

### Environment Variables

Create a `.env` file with the following:

```bash
# GitHub
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repo

# Docker
DOCKER_REGISTRY=ghcr.io
DOCKER_IMAGE_NAME=cryptoorchestrator

# Secrets Management (choose one)
# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# OR Vault
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your_vault_token

# Monitoring
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=development

# Redis
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cryptoorchestrator
TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/test_cryptoorchestrator
```

## MCP Configuration

### 1. GitHub MCP

#### Setup

1. Create a GitHub Personal Access Token:
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Create token with `repo`, `workflow`, and `write:packages` scopes
   - Save as `GITHUB_TOKEN` in `.env`

2. Configure repository secrets:
   ```bash
   # In GitHub repository settings > Secrets
   GITHUB_TOKEN=<your_token>
   DEPLOY_HOST=<production_server>
   DEPLOY_USER=<deploy_user>
   DEPLOY_SSH_KEY=<ssh_private_key>
   ```

#### Usage

```bash
# Create a new release
python scripts/github_release.py \
  --repo owner/repo \
  --bump patch \
  --notes "Bug fixes and improvements" \
  --push

# Automated via GitHub Actions
# Go to Actions > Release Automation > Run workflow
```

### 2. PostgreSQL/Database MCP

#### Setup

1. Install PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. Create test database:
   ```bash
   createdb test_cryptoorchestrator
   ```

3. Update `server_fastapi/tests/conftest_db.py` with your database URL

#### Usage

```bash
# Run tests with isolated database
pytest server_fastapi/tests/ -v

# Tests automatically use isolated test database
# Each test gets its own transaction that rolls back
```

### 3. Docker MCP

#### Setup

1. Install Docker and Docker Compose (if not already installed)

2. Build and test locally:
   ```bash
   # Build image
   ./scripts/docker_deploy.sh build
   
   # Or on Windows
   .\scripts\docker_deploy.ps1 build
   ```

#### Usage

```bash
# Build and scan
./scripts/docker_deploy.sh scan

# Build, push, and deploy
./scripts/docker_deploy.sh deploy

# Run migrations
./scripts/docker_deploy.sh migrate

# Health check
./scripts/docker_deploy.sh health

# Rollback
./scripts/docker_deploy.sh rollback
```

### 4. Testing MCP (Playwright)

#### Setup

```bash
# Install Playwright browsers
npx playwright install --with-deps

# Run E2E tests locally
npm run test:e2e

# Or with Playwright directly
npx playwright test
```

#### Configuration

E2E tests are configured in:
- `playwright.config.ts` - Main configuration
- `tests/e2e/global-setup.ts` - Test environment setup
- `tests/e2e/global-teardown.ts` - Cleanup
- `tests/e2e/app.spec.ts` - Test cases

### 5. Secrets Management MCP

#### Setup

Choose your provider:

**Option A: AWS Secrets Manager**
```bash
pip install boto3
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

**Option B: HashiCorp Vault**
```bash
pip install hvac
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=your_token
```

**Option C: Local (.env file)**
```bash
# No additional setup needed
# Secrets stored in .env file
```

#### Usage

```bash
# Generate a secret
python scripts/secrets_manager.py generate

# Get a secret
python scripts/secrets_manager.py get --key JWT_SECRET

# Set a secret
python scripts/secrets_manager.py set --key JWT_SECRET --value "new_secret"

# Rotate a secret
python scripts/secrets_manager.py rotate --key JWT_SECRET

# Rotate all secrets
python scripts/secrets_manager.py rotate --all

# Validate all required secrets
python scripts/secrets_manager.py validate
```

### 6. Redis MCP

#### Setup

```bash
# Install Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://github.com/microsoftarchive/redis/releases

# Start Redis
redis-server
```

#### Usage

```bash
# Test connection
python scripts/redis_setup.py test

# Setup cache keys
python scripts/redis_setup.py setup

# Clear cache
python scripts/redis_setup.py clear --pattern "market_data:*"

# Get statistics
python scripts/redis_setup.py stats
```

### 7. Monitoring MCP (Sentry)

#### Setup

1. Create Sentry account: https://sentry.io
2. Create a new project and get DSN
3. Add to `.env`:
   ```bash
   SENTRY_DSN=https://your-dsn@sentry.io/project-id
   ENVIRONMENT=production
   ```

4. Initialize in FastAPI app:
   ```python
   from server_fastapi.services.monitoring.sentry_integration import init_sentry
   
   init_sentry()
   ```

#### Usage

Sentry automatically captures:
- Unhandled exceptions
- Errors in FastAPI routes
- Database errors
- Redis connection issues

Manual tracking:
```python
from server_fastapi.services.monitoring.sentry_integration import (
    capture_exception, capture_message, sentry_user
)

try:
    # Your code
    pass
except Exception as e:
    capture_exception(e)

# Set user context
sentry_user(user_id="123", email="user@example.com")
```

### 8. Code Quality MCP

#### Setup

**Snyk:**
```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Scan
snyk test
snyk monitor
```

**SonarQube (optional):**
```bash
# Install SonarScanner
# See: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/

# Run scan
sonar-scanner
```

## GitHub Actions Integration

All MCPs are integrated into GitHub Actions workflows:

1. **`.github/workflows/ci.yml`** - Main CI/CD pipeline
2. **`.github/workflows/release.yml`** - Release automation
3. **`.github/workflows/deploy.yml`** - Deployment automation
4. **`.github/workflows/e2e-tests.yml`** - E2E test automation

### Secrets Configuration

Add these secrets in GitHub repository settings:

- `GITHUB_TOKEN` - Auto-generated
- `SNYK_TOKEN` - From https://snyk.io
- `CODECOV_TOKEN` - From https://codecov.io
- `DEPLOY_HOST` - Production server hostname
- `DEPLOY_USER` - SSH username
- `DEPLOY_SSH_KEY` - SSH private key
- `DATABASE_URL` - Production database URL
- `REDIS_URL` - Production Redis URL
- `SENTRY_DSN` - Sentry DSN

## Testing the Integrations

### Quick Test Script

```bash
# Test all MCP integrations
./scripts/test_mcp_integrations.sh

# Or on Windows
.\scripts\test_mcp_integrations.ps1
```

### Manual Testing

1. **GitHub MCP**: Run release script (dry run first)
2. **Database MCP**: Run pytest tests
3. **Docker MCP**: Build and scan image
4. **Testing MCP**: Run Playwright tests
5. **Secrets MCP**: Validate secrets
6. **Redis MCP**: Test connection
7. **Monitoring MCP**: Check Sentry dashboard
8. **Code Quality MCP**: Run Snyk scan

## Troubleshooting

### GitHub MCP Issues

- **Permission denied**: Check token has correct scopes
- **Release fails**: Verify repository name format (owner/repo)

### Database MCP Issues

- **Connection refused**: Check PostgreSQL is running
- **Test database exists**: Drop and recreate test database

### Docker MCP Issues

- **Build fails**: Check Dockerfile syntax
- **Push fails**: Verify registry credentials

### Redis MCP Issues

- **Connection refused**: Start Redis server
- **Permission denied**: Check Redis configuration

### Sentry MCP Issues

- **Events not appearing**: Verify DSN is correct
- **Too many events**: Adjust sampling rate in `sentry_integration.py`

## Next Steps

1. ✅ Configure all MCP integrations
2. ✅ Test locally before deploying
3. ✅ Set up GitHub Actions secrets
4. ✅ Run automated tests
5. ✅ Monitor Sentry for errors
6. ✅ Review security scans

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Playwright Documentation](https://playwright.dev/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Snyk Documentation](https://docs.snyk.io/)

