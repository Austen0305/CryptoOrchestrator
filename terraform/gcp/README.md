# Google Cloud Platform Deployment

This directory contains Terraform configurations for deploying CryptoOrchestrator to Google Cloud Platform using Cloud Run.

## Prerequisites

1. **Google Cloud SDK** installed and configured
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Terraform** >= 1.0 installed
   ```bash
   terraform version
   ```

3. **GCP Project** with billing enabled
   - Create project: https://console.cloud.google.com/
   - Enable billing
   - Enable required APIs (see below)

## Required APIs

Enable the following APIs in your GCP project:

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

## Quick Start

### 1. Configure Variables

Create `terraform.tfvars`:

```hcl
gcp_project_id = "your-project-id"
gcp_region     = "us-central1"
environment    = "production"

# Database
db_tier              = "db-f1-micro"  # Free tier
db_username          = "crypto_user"
db_password          = "your-secure-password"

# Redis
redis_tier       = "BASIC"
redis_memory_size = 1

# Cloud Run
container_image = "gcr.io/your-project-id/cryptoorchestrator:latest"
cloud_run_min_instances = "0"  # Scale to zero
cloud_run_max_instances = "10"

# Security (generate secure values)
jwt_secret                  = "your-jwt-secret-here"
exchange_key_encryption_key = "your-encryption-key-here"

# Additional environment variables
additional_env_vars = {
  NODE_ENV = "production"
  LOG_LEVEL = "INFO"
  # Add other vars as needed
}
```

### 2. Initialize Terraform

```bash
cd terraform/gcp
terraform init
```

### 3. Plan Deployment

```bash
terraform plan
```

### 4. Deploy

```bash
terraform apply
```

### 5. Get Service URL

```bash
terraform output cloud_run_service_url
```

## Building and Pushing Container Image

### Build Docker Image

```bash
docker build -t gcr.io/YOUR_PROJECT_ID/cryptoorchestrator:latest -f Dockerfile.optimized .
```

### Push to GCR

```bash
gcloud auth configure-docker
docker push gcr.io/YOUR_PROJECT_ID/cryptoorchestrator:latest
```

## Environment Variables

Set sensitive environment variables via Secret Manager:

```bash
# JWT Secret
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret --data-file=-

# Encryption Key
echo -n "your-encryption-key" | gcloud secrets create encryption-key --data-file=-
```

Or use Terraform variables (stored in tfvars, not committed).

## Database Migrations

Migrations run automatically on Cloud Run startup, or manually:

```bash
# Get service URL
SERVICE_URL=$(terraform output -raw cloud_run_service_url)

# Trigger migration endpoint (if configured)
curl -X POST $SERVICE_URL/api/admin/migrate
```

## Cost Estimation

**Free Tier (Always Free):**
- Cloud Run: 2 million requests/month
- Cloud SQL: db-f1-micro (shared-core)
- Cloud Memorystore: Not in free tier (use Upstash Redis instead)

**Estimated Monthly Cost (Low Traffic):**
- Cloud Run: $0 (within free tier)
- Cloud SQL: $0 (db-f1-micro)
- Cloud Memorystore: ~$30/month (1GB)
- VPC Connector: ~$10/month
- **Total: ~$40/month** (or $0 if using external Redis)

## Scaling

Cloud Run automatically scales based on traffic:
- **Min Instances:** 0 (scale to zero) or 1+ (always warm)
- **Max Instances:** 10 (default, increase for high traffic)
- **Concurrency:** 80 requests per instance (default)

## Monitoring

View logs:
```bash
gcloud run services logs read cryptoorchestrator-backend --region=us-central1
```

View metrics:
- Go to Cloud Console → Cloud Run → Metrics

## Troubleshooting

### Service Won't Start

1. Check logs: `gcloud run services logs read`
2. Verify database connection (check connection name)
3. Verify Redis connection (check VPC connector)
4. Check environment variables

### Database Connection Issues

1. Verify VPC connector is working
2. Check Cloud SQL connection name
3. Verify service account has `cloudsql.client` role

### High Costs

1. Set `cloud_run_min_instances = "0"` to scale to zero
2. Use external Redis (Upstash) instead of Cloud Memorystore
3. Monitor usage in Cloud Console

## Cleanup

```bash
terraform destroy
```

**Warning:** This will delete all resources including databases. Backup first!

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud Memorystore Documentation](https://cloud.google.com/memorystore/docs/redis)
