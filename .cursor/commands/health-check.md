# Health Check

Verify all services are healthy and running correctly.

## Quick Health Check

Run comprehensive health check:
```bash
npm run health:check
```

Or use the advanced health check:
```bash
npm run health:advanced
```

## Individual Service Checks

### Backend Health

```bash
# Basic health check
curl http://localhost:8000/health

# Advanced health check
curl http://localhost:8000/health/advanced

# Or use npm script
npm run health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-30T12:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "web3": "available"
  }
}
```

### Frontend Health

```bash
# Check frontend is serving
curl http://localhost:5173

# Check in browser
# Open http://localhost:5173
```

### Database Health

```bash
# Check database connection and health
python scripts/utilities/database-health.py
```

**Checks**:
- Database connection
- Table existence
- Query performance
- Connection pool status

### Redis Health

```bash
# Check Redis connection
redis-cli ping

# Or check in code
# Redis health is included in backend health check
```

## Comprehensive Health Check

### All Services

```bash
# Check all services
npm run check:services
```

This checks:
- Backend API
- Frontend server
- Database connection
- Redis connection (if configured)
- Web3 services (if configured)

### Environment Validation

```bash
# Validate environment variables
npm run validate:env
```

**Checks**:
- Required variables present
- Variable formats correct
- Database URL valid
- API keys configured (if required)

## Health Check Endpoints

### Backend Endpoints

- **Basic**: `GET /health`
- **Advanced**: `GET /health/advanced`
- **Readiness**: `GET /health/ready`
- **Liveness**: `GET /health/live`

### Response Codes

- **200**: Healthy
- **503**: Unhealthy (service unavailable)
- **500**: Error

## Health Check Components

### Database Health

Checks:
- ✅ Connection successful
- ✅ Tables exist
- ✅ Queries execute
- ✅ Connection pool healthy

### Redis Health

Checks:
- ✅ Connection successful
- ✅ Commands execute
- ✅ Cache operations work

### Web3 Health

Checks:
- ✅ RPC connections work
- ✅ Blockchain accessible
- ✅ Transaction simulation works

### API Health

Checks:
- ✅ Routes respond
- ✅ Authentication works
- ✅ Rate limiting active

## Automated Health Monitoring

### Continuous Monitoring

```bash
# Monitor health for 60 seconds
npm run monitor:health:60s

# Or use Python script
python scripts/monitoring/health_monitor.py --duration 60
```

### Health Monitoring Service

For production, use health monitoring:
```bash
python scripts/monitoring/health_monitor.py --continuous
```

## Troubleshooting

### Service Unhealthy

1. **Check Logs**: Review service logs for errors
2. **Check Dependencies**: Verify dependencies are running
3. **Check Configuration**: Verify environment variables
4. **Check Resources**: Verify CPU/memory available
5. **Restart Service**: Try restarting the service

### Database Unhealthy

1. **Check Connection**: Verify DATABASE_URL is correct
2. **Check Database**: Verify PostgreSQL is running
3. **Check Migrations**: Run `alembic upgrade head`
4. **Check Permissions**: Verify database user permissions
5. **Check Logs**: Review database logs

### Redis Unhealthy

1. **Check Connection**: Verify REDIS_URL is correct
2. **Check Redis**: Verify Redis is running
3. **Check Network**: Verify network connectivity
4. **Check Configuration**: Verify Redis configuration
5. **Restart Redis**: Try restarting Redis

## Health Check Best Practices

1. **Regular Checks**: Run health checks regularly
2. **Monitor Continuously**: Use monitoring in production
3. **Alert on Failures**: Set up alerts for health failures
4. **Document Issues**: Document health check failures
5. **Automate Checks**: Automate health checks in CI/CD

## Summary

✅ **Quick Check**: `npm run health:check`  
✅ **Advanced Check**: `npm run health:advanced`  
✅ **All Services**: `npm run check:services`  
✅ **Environment**: `npm run validate:env`  
✅ **Continuous**: `npm run monitor:health:60s`

**Status**: All services should return "healthy" for normal operation.
