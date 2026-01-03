# Deploy to Staging

Deploy CryptoOrchestrator to staging environment.

## Pre-Deployment Checklist

Before deploying, ensure:

1. **All Tests Pass**
   ```bash
   npm run test:pre-deploy
   ```

2. **Code Quality Checks**
   ```bash
   npm run check:quality
   npm run audit:security
   ```

3. **Build Successfully**
   ```bash
   npm run build
   ```

4. **Environment Variables**
   - Verify staging `.env` file
   - Check all required variables are set
   - Verify API keys and secrets

## Deployment Steps

### Option 1: Railway (Recommended for Staging)

```bash
# Deploy to Railway
railway up
```

### Option 2: Docker Compose

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml --env-file .env.staging up -d
```

### Option 3: Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/staging/
```

## Post-Deployment Verification

1. **Health Check**
   ```bash
   curl https://staging.yourdomain.com/health
   ```

2. **Service Verification**
   ```bash
   npm run verify:features
   ```

3. **Database Migrations**
   ```bash
   # Run migrations on staging
   alembic upgrade head
   ```

## Rollback Procedure

If deployment fails:

1. **Docker Compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml rollback
   ```

2. **Kubernetes:**
   ```bash
   kubectl rollout undo deployment/cryptoorchestrator -n staging
   ```

3. **Database:**
   ```bash
   alembic downgrade -1
   ```

## Monitoring

After deployment, monitor:
- Application logs
- Error rates
- Performance metrics
- Database connections

## Troubleshooting

If deployment fails:
1. Check deployment logs
2. Verify environment variables
3. Check service health endpoints
4. Review database connection
5. Check resource limits (CPU/memory)
