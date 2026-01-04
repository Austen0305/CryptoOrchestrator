# Google Cloud Platform (Cloud Run) Deployment Guide

**Date:** January 3, 2026  
**Status:** Ready to Deploy ✅

---

## Overview

This guide walks you through deploying CryptoOrchestrator to Google Cloud Platform using Cloud Run, Cloud SQL (PostgreSQL), and Cloud Memorystore (Redis).

**Why Cloud Run?**
- ✅ Serverless - no server management
- ✅ Auto-scaling (scale to zero)
- ✅ Pay per use (2M requests/month free)
- ✅ Built-in HTTPS and load balancing
- ✅ Fast cold starts (~1-2 seconds)

---

## Prerequisites

1. **Google Cloud Account**
   - Sign up: https://cloud.google.com/
   - Free tier: $300 credit for 90 days
   - Always free: 2M Cloud Run requests/month

2. **Google Cloud SDK**
   ```bash
   # Install gcloud CLI
   # macOS: brew install google-cloud-sdk
   # Windows: Download from https://cloud.google.com/sdk/docs/install
   
   # Authenticate
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Terraform** (optional, for infrastructure as code)
   ```bash
   # Install Terraform
   # macOS: brew install terraform
   # Windows: Download from https://www.terraform.io/downloads
   ```

---

## Quick Deploy (15 Minutes)

### Step 1: Create GCP Project

```bash
# Create project
gcloud projects create cryptoorchestrator --name="CryptoOrchestrator"

# Set as default
gcloud config set project cryptoorchestrator

# Enable billing (required for Cloud SQL and Redis)
# Go to: https://console.cloud.google.com/billing
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  compute.googleapis.com
```

### Step 3: Build and Push Container

```bash
# Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/cryptoorchestrator:latest -f Dockerfile.optimized .

# Configure Docker for GCR
gcloud auth configure-docker

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/cryptoorchestrator:latest
```

### Step 4: Create Cloud SQL Database

```bash
# Create PostgreSQL instance
gcloud sql instances create cryptoorchestrator-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create cryptoorchestrator \
  --instance=cryptoorchestrator-db

# Create user
gcloud sql users create crypto_user \
  --instance=cryptoorchestrator-db \
  --password=YOUR_SECURE_PASSWORD
```

### Step 5: Create Redis Instance

```bash
# Create Redis instance
gcloud redis instances create cryptoorchestrator-redis \
  --size=1 \
  --region=us-central1 \
  --tier=BASIC
```

### Step 6: Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy cryptoorchestrator-backend \
  --image=gcr.io/YOUR_PROJECT_ID/cryptoorchestrator:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=production,PORT=8000" \
  --set-secrets="JWT_SECRET=jwt-secret:latest,EXCHANGE_KEY_ENCRYPTION_KEY=encryption-key:latest" \
  --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:cryptoorchestrator-db \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10
```

### Step 7: Set Secrets

```bash
# Create JWT secret
echo -n "your-jwt-secret-here" | gcloud secrets create jwt-secret --data-file=-

# Create encryption key
echo -n "your-encryption-key-here" | gcloud secrets create encryption-key --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding jwt-secret \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 8: Configure Database Connection

Update Cloud Run service with database connection:

```bash
# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe cryptoorchestrator-db --format="value(connectionName)")

# Update service with connection
gcloud run services update cryptoorchestrator-backend \
  --region=us-central1 \
  --add-cloudsql-instances=$CONNECTION_NAME \
  --set-env-vars="DATABASE_URL=postgresql+asyncpg://crypto_user:YOUR_PASSWORD@/$CONNECTION_NAME?host=/cloudsql/$CONNECTION_NAME"
```

---

## Using Terraform (Recommended)

For infrastructure as code, use the Terraform configuration:

### 1. Configure Variables

Create `terraform/gcp/terraform.tfvars`:

```hcl
gcp_project_id = "your-project-id"
gcp_region     = "us-central1"
environment    = "production"

db_tier     = "db-f1-micro"
db_username = "crypto_user"
db_password = "your-secure-password"

redis_tier       = "BASIC"
redis_memory_size = 1

container_image = "gcr.io/your-project-id/cryptoorchestrator:latest"

jwt_secret                  = "your-jwt-secret"
exchange_key_encryption_key = "your-encryption-key"
```

### 2. Initialize and Deploy

```bash
cd terraform/gcp
terraform init
terraform plan
terraform apply
```

### 3. Get Service URL

```bash
terraform output cloud_run_service_url
```

---

## Environment Variables

### Required Variables

Set these in Cloud Run:

- `DATABASE_URL` - Cloud SQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - JWT signing secret (use Secret Manager)
- `EXCHANGE_KEY_ENCRYPTION_KEY` - Encryption key (use Secret Manager)
- `NODE_ENV=production`

### Optional Variables

- `LOG_LEVEL=INFO`
- `ENABLE_SENTRY=true` (if using Sentry)
- `SENTRY_DSN` (Sentry DSN)
- DEX aggregator API keys (0x, OKX, Rubic)
- Blockchain RPC URLs

### Setting Environment Variables

**Via gcloud CLI:**
```bash
gcloud run services update cryptoorchestrator-backend \
  --region=us-central1 \
  --set-env-vars="LOG_LEVEL=INFO,ENABLE_SENTRY=true"
```

**Via Secret Manager (for sensitive values):**
```bash
# Create secret
echo -n "secret-value" | gcloud secrets create secret-name --data-file=-

# Use in Cloud Run
gcloud run services update cryptoorchestrator-backend \
  --region=us-central1 \
  --set-secrets="ENV_VAR_NAME=secret-name:latest"
```

---

## Database Migrations

Migrations run automatically on startup, or trigger manually:

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe cryptoorchestrator-backend \
  --region=us-central1 \
  --format="value(status.url)")

# Run migrations
curl -X POST $SERVICE_URL/api/admin/migrate
```

Or connect directly:

```bash
# Connect to database
gcloud sql connect cryptoorchestrator-db --user=crypto_user

# Run migrations
alembic upgrade head
```

---

## Monitoring & Logs

### View Logs

```bash
# Stream logs
gcloud run services logs tail cryptoorchestrator-backend --region=us-central1

# View recent logs
gcloud run services logs read cryptoorchestrator-backend --region=us-central1 --limit=50
```

### View Metrics

1. Go to Cloud Console
2. Navigate to Cloud Run → cryptoorchestrator-backend
3. Click "Metrics" tab

### Health Checks

```bash
# Check health
curl https://YOUR_SERVICE_URL/healthz

# Advanced health check
curl https://YOUR_SERVICE_URL/health
```

---

## Scaling Configuration

### Auto-Scaling

Cloud Run automatically scales based on traffic:

- **Min Instances:** 0 (scale to zero) or 1+ (always warm)
- **Max Instances:** 10 (default, increase for high traffic)
- **Concurrency:** 80 requests per instance (default)

### Update Scaling

```bash
gcloud run services update cryptoorchestrator-backend \
  --region=us-central1 \
  --min-instances=1 \
  --max-instances=20 \
  --concurrency=100
```

---

## Cost Optimization

### Free Tier Limits

- **Cloud Run:** 2 million requests/month
- **Cloud SQL:** db-f1-micro (shared-core, 0.6GB RAM)
- **Cloud Memorystore:** Not in free tier (~$30/month for 1GB)

### Cost-Saving Tips

1. **Use External Redis:** Use Upstash Redis (free tier) instead of Cloud Memorystore
2. **Scale to Zero:** Set `min-instances=0` (adds cold start delay)
3. **Use Smaller Instance:** Start with db-f1-micro, upgrade when needed
4. **Monitor Usage:** Set up billing alerts

### Estimated Monthly Cost

**Low Traffic (< 100K requests/month):**
- Cloud Run: $0 (free tier)
- Cloud SQL: $0 (db-f1-micro)
- Cloud Memorystore: ~$30/month
- **Total: ~$30/month**

**Medium Traffic (1M requests/month):**
- Cloud Run: ~$10/month
- Cloud SQL: ~$25/month (db-n1-standard-1)
- Cloud Memorystore: ~$30/month
- **Total: ~$65/month**

---

## Troubleshooting

### Service Won't Start

1. **Check Logs:**
   ```bash
   gcloud run services logs read cryptoorchestrator-backend --region=us-central1
   ```

2. **Verify Database Connection:**
   - Check connection name format
   - Verify service account has `cloudsql.client` role
   - Test connection manually

3. **Verify Environment Variables:**
   ```bash
   gcloud run services describe cryptoorchestrator-backend \
     --region=us-central1 \
     --format="value(spec.template.spec.containers[0].env)"
   ```

### Database Connection Issues

1. **Verify VPC Connector:**
   ```bash
   gcloud compute networks vpc-access connectors list
   ```

2. **Check Cloud SQL Connection:**
   ```bash
   gcloud sql instances describe cryptoorchestrator-db
   ```

3. **Test Connection:**
   ```bash
   gcloud sql connect cryptoorchestrator-db --user=crypto_user
   ```

### High Latency

1. **Increase Min Instances:** Prevents cold starts
   ```bash
   gcloud run services update cryptoorchestrator-backend \
     --region=us-central1 \
     --min-instances=1
   ```

2. **Increase Memory/CPU:**
   ```bash
   gcloud run services update cryptoorchestrator-backend \
     --region=us-central1 \
     --memory=4Gi \
     --cpu=4
   ```

### High Costs

1. **Scale to Zero:** Set `min-instances=0`
2. **Use External Redis:** Replace Cloud Memorystore with Upstash
3. **Monitor Usage:** Set up billing alerts
4. **Optimize Database:** Use smaller instance tier

---

## Security Best Practices

1. **Use Secret Manager:** Store all secrets in Secret Manager, not environment variables
2. **Enable VPC:** Use VPC connector for private database access
3. **Restrict Access:** Use IAM to restrict who can access services
4. **Enable Audit Logs:** Monitor access and changes
5. **Use HTTPS:** Cloud Run provides HTTPS by default

---

## Next Steps

1. **Set up CI/CD:** Use Cloud Build for automated deployments
2. **Configure Monitoring:** Set up alerts and dashboards
3. **Set up Backups:** Configure automated database backups
4. **Configure CDN:** Use Cloud CDN for static assets
5. **Set up Load Balancing:** For high availability

---

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)

---

**Status:** ✅ Ready to Deploy  
**Last Updated:** January 3, 2026
