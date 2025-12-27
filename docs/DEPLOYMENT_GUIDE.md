# Production Deployment Guide

**Status**: Ready for Production Deployment  
**Last Updated**: December 12, 2025

## Pre-Deployment Checklist

### 1. Testnet Verification ✅
- [ ] Run testnet verification script
- [ ] Verify wallet operations on testnet
- [ ] Test DEX trading on testnet
- [ ] Verify 2FA flow
- [ ] Test withdrawal flow

**Commands:**
```bash
# Run all testnet tests
python scripts/testing/testnet_verification.py --network sepolia

# Run specific test
python scripts/testing/testnet_verification.py --network sepolia --test wallet
python scripts/testing/testnet_verification.py --network sepolia --test dex
python scripts/testing/testnet_verification.py --network sepolia --test 2fa
```

### 2. Performance Baseline ✅
- [ ] Set performance baseline
- [ ] Verify performance targets met
- [ ] Configure regression detection

**Commands:**
```bash
# Set baseline
python scripts/monitoring/set_performance_baseline.py

# Set baseline for specific endpoint
python scripts/monitoring/set_performance_baseline.py --endpoint /api/bots

# Force overwrite existing baseline
python scripts/monitoring/set_performance_baseline.py --force
```

### 3. Security Audit ✅
- [ ] Run security audit
- [ ] Fix any vulnerabilities
- [ ] Review audit report

**Commands:**
```bash
# Run all security checks
python scripts/security/security_audit.py

# Run specific check
python scripts/security/security_audit.py --check dependency
python scripts/security/security_audit.py --check code
python scripts/security/security_audit.py --check secrets
```

### 4. Load Testing ✅
- [ ] Run load tests
- [ ] Verify scalability
- [ ] Test under peak load

**Commands:**
```bash
# Run load test (default: 50 users, 60 seconds)
python scripts/testing/load_test.py

# Custom load test
python scripts/testing/load_test.py --users 100 --duration 120

# Test specific endpoint
python scripts/testing/load_test.py --endpoint /api/bots
```

### 5. Final Verification ✅
- [ ] All tests passing
- [ ] TypeScript: 0 errors
- [ ] Type coverage: ≥95%
- [ ] Documentation complete
- [ ] Infrastructure ready

## Deployment Environments

### Staging Environment

**Purpose**: Pre-production testing and validation

**Deployment Steps:**
1. Deploy to staging Kubernetes cluster
2. Run smoke tests
3. Verify all services healthy
4. Test critical user flows
5. Monitor for 24 hours

**Commands:**
```bash
# Deploy to staging
kubectl apply -f k8s/ --namespace staging

# Verify deployment
kubectl get pods -n staging
kubectl get services -n staging

# Check logs
kubectl logs -f deployment/backend -n staging
kubectl logs -f deployment/frontend -n staging
```

### Production Environment

**Purpose**: Live production deployment

**Deployment Steps:**
1. Final pre-deployment checks
2. Deploy to production
3. Run smoke tests
4. Monitor closely for first hour
5. Verify all systems operational

**Commands:**
```bash
# Deploy to production
kubectl apply -f k8s/ --namespace production

# Verify deployment
kubectl get pods -n production
kubectl get services -n production

# Monitor
kubectl logs -f deployment/backend -n production
```

## Deployment Methods

### Method 1: Kubernetes (Recommended)

**Prerequisites:**
- Kubernetes cluster configured
- kubectl configured
- Docker images built and pushed

**Steps:**
1. Build Docker images
2. Push to container registry
3. Update image tags in Kubernetes manifests
4. Apply manifests
5. Verify deployment

**Commands:**
```bash
# Build and push images
docker build -t your-registry/cryptoorchestrator-backend:latest -f Dockerfile.backend .
docker build -t your-registry/cryptoorchestrator-frontend:latest -f Dockerfile.frontend .
docker push your-registry/cryptoorchestrator-backend:latest
docker push your-registry/cryptoorchestrator-frontend:latest

# Deploy
kubectl apply -f k8s/
```

### Method 2: Docker Compose

**Prerequisites:**
- Docker and Docker Compose installed
- Production environment variables set

**Steps:**
1. Set environment variables
2. Start services
3. Verify health

**Commands:**
```bash
# Set environment variables
cp .env.example .env.prod
# Edit .env.prod with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Method 3: Terraform (AWS)

**Prerequisites:**
- AWS account configured
- Terraform installed
- AWS credentials configured

**Steps:**
1. Initialize Terraform
2. Review plan
3. Apply infrastructure
4. Deploy application

**Commands:**
```bash
cd terraform/aws

# Initialize
terraform init

# Review plan
terraform plan

# Apply
terraform apply

# Get outputs
terraform output
```

## Post-Deployment Verification

### 1. Health Checks
```bash
# Check backend health
curl https://api.yourdomain.com/api/health

# Check frontend
curl https://yourdomain.com

# Check database
kubectl exec -it postgres-0 -n production -- psql -U postgres -c "SELECT 1"
```

### 2. Smoke Tests
```bash
# Run smoke tests
pytest tests/smoke/ -v

# Test critical endpoints
curl https://api.yourdomain.com/api/bots
curl https://api.yourdomain.com/api/portfolio
```

### 3. Monitoring
- [ ] Check application logs
- [ ] Verify metrics collection
- [ ] Check error rates
- [ ] Monitor response times
- [ ] Verify database connections

### 4. Performance Monitoring
```bash
# Compare with baseline
python scripts/monitoring/monitor_performance.py --compare

# Monitor in real-time
python scripts/monitoring/monitor_performance.py --watch
```

## Rollback Procedures

### Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/backend -n production
kubectl rollout undo deployment/frontend -n production

# Check rollback status
kubectl rollout status deployment/backend -n production
```

### Docker Compose Rollback
```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Start previous version
docker-compose -f docker-compose.prod.yml up -d --scale backend=0
# Then start previous version
```

## Monitoring & Alerts

### Key Metrics to Monitor
- API response times (p50, p95, p99)
- Error rates
- Database query performance
- Cache hit rates
- Memory and CPU usage
- Request throughput

### Alert Thresholds
- Response time > 2s (p95)
- Error rate > 1%
- Database query time > 500ms (p95)
- Memory usage > 80%
- CPU usage > 80%

## Disaster Recovery

### Backup Verification
```bash
# Verify backups
python scripts/backup_database.py --verify

# Test restore
python scripts/restore_database.py --test
```

### Recovery Procedures
See `docs/DISASTER_RECOVERY.md` for complete recovery procedures.

## Support & Troubleshooting

### Common Issues

**Issue**: Services not starting
- Check logs: `kubectl logs -f deployment/backend -n production`
- Verify environment variables
- Check resource limits

**Issue**: Database connection errors
- Verify database credentials
- Check network connectivity
- Verify connection pool settings

**Issue**: High response times
- Check database query performance
- Verify cache is working
- Check for N+1 queries

### Getting Help
- Check logs: `kubectl logs -f deployment/backend -n production`
- Review monitoring dashboards
- Check error tracking (Sentry)
- Review documentation

## Deployment Checklist Summary

- [ ] Testnet verification complete
- [ ] Performance baseline set
- [ ] Security audit passed
- [ ] Load testing complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Infrastructure ready
- [ ] Monitoring configured
- [ ] Backups verified
- [ ] Rollback plan ready
- [ ] Team notified
- [ ] Deployment scheduled

## Next Steps After Deployment

1. **Monitor Closely** (First 24 hours)
   - Watch error rates
   - Monitor response times
   - Check system resources

2. **Gather Feedback**
   - Collect user feedback
   - Monitor support tickets
   - Review analytics

3. **Optimize**
   - Identify bottlenecks
   - Optimize slow queries
   - Improve caching

4. **Iterate**
   - Plan next improvements
   - Address issues
   - Enhance features

---

**Status**: Ready for Production Deployment  
**Last Verified**: December 12, 2025
