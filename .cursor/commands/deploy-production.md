# Deploy to Production

Deploy CryptoOrchestrator to production environment.

## Pre-Deployment Checklist

**CRITICAL**: Complete all checks before production deployment.

### 1. All Tests Pass
```bash
npm run test:pre-deploy
```

This runs:
- All test suites (backend, frontend, E2E)
- Infrastructure tests
- Security tests
- Load tests

### 2. Code Quality Checks
```bash
npm run check:quality
npm run audit:security
```

### 3. Build Verification
```bash
npm run build
npm run verify:build
```

### 4. Environment Variables
- ✅ Verify production `.env` file
- ✅ Check all required variables are set
- ✅ Verify API keys and secrets
- ✅ Check database connection strings
- ✅ Verify RPC provider URLs
- ✅ Check JWT secrets are strong

### 5. Database Migrations
```bash
# Review migrations
alembic history

# Test migrations on staging first
alembic upgrade head
```

### 6. Security Audit
```bash
npm run audit:security
```

Check for:
- npm vulnerabilities
- Python package vulnerabilities
- Security best practices

## Deployment Steps

### Option 1: Railway (Recommended)

```bash
# Deploy to Railway
railway up --environment production
```

### Option 2: Docker Compose

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Option 3: Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/production/

# Verify deployment
kubectl rollout status deployment/cryptoorchestrator -n production
```

### Option 4: Vercel (Frontend) + Railway (Backend)

**Frontend**:
```bash
vercel --prod
```

**Backend**:
```bash
railway up --environment production
```

## Post-Deployment Verification

### 1. Health Checks

```bash
# Check backend health
curl https://api.yourdomain.com/health

# Check frontend
curl https://yourdomain.com
```

### 2. Service Verification

```bash
# Verify all services are running
npm run check:services

# Verify features
npm run verify:features
```

### 3. Database Verification

```bash
# Check database connection
python scripts/utilities/database-health.py

# Verify migrations applied
alembic current
```

### 4. Monitoring

Monitor:
- Application logs
- Error rates
- Performance metrics
- Database connections
- API response times

## Rollback Procedure

If deployment fails:

### Docker Compose
```bash
docker-compose -f docker-compose.prod.yml rollback
```

### Kubernetes
```bash
kubectl rollout undo deployment/cryptoorchestrator -n production
```

### Database
```bash
# Rollback last migration if needed
alembic downgrade -1
```

## Production Best Practices

1. **Always Test on Staging First**: Never deploy directly to production
2. **Use Blue-Green Deployment**: Zero-downtime deployments
3. **Monitor Closely**: Watch logs and metrics for first hour
4. **Have Rollback Plan**: Know how to rollback before deploying
5. **Backup Database**: Always backup before major deployments
6. **Verify Health**: Check all health endpoints after deployment
7. **Test Critical Paths**: Test login, trading, wallet operations

## Security Checklist

- [ ] All secrets are in environment variables (not in code)
- [ ] HTTPS is enforced
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] Security headers are set
- [ ] Database is not publicly accessible
- [ ] API keys are rotated regularly
- [ ] Logging doesn't expose sensitive data

## Troubleshooting

### Deployment Fails

1. **Check Logs**: Review deployment logs
2. **Check Environment**: Verify environment variables
3. **Check Resources**: Verify CPU/memory limits
4. **Check Database**: Verify database connection
5. **Check Services**: Verify all services are healthy

### Services Not Starting

1. **Check Logs**: Review service logs
2. **Check Dependencies**: Verify all dependencies installed
3. **Check Configuration**: Verify configuration files
4. **Check Ports**: Verify ports are available
5. **Check Database**: Verify database is accessible

### Performance Issues

1. **Check Metrics**: Review performance metrics
2. **Check Database**: Verify database performance
3. **Check Cache**: Verify Redis cache is working
4. **Check Resources**: Verify resource limits
5. **Check Logs**: Review error logs

## Monitoring

After deployment, monitor:
- **Application Logs**: Error rates, warnings
- **Performance Metrics**: Response times, throughput
- **Database Metrics**: Query performance, connections
- **Infrastructure**: CPU, memory, disk usage
- **User Activity**: Active users, API usage

## Summary

✅ **Pre-Deployment**: Complete all checks  
✅ **Deployment**: Use appropriate method  
✅ **Post-Deployment**: Verify everything works  
✅ **Monitoring**: Watch closely for issues  
✅ **Rollback**: Have plan ready

**Remember**: Production deployments are critical - take your time and verify everything!
