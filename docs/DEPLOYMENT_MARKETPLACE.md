# Marketplace Deployment Guide

This guide covers deploying and configuring the Copy Trading Marketplace and Custom Indicator Marketplace features.

## Prerequisites

- Database migrations completed (`alembic upgrade head`)
- Redis running (for Celery tasks and caching)
- Environment variables configured
- Admin user created

## Initial Setup

### 1. Database Migrations

Ensure all marketplace migrations are applied:

```bash
# Run migrations
cd server_fastapi
alembic upgrade head

# Verify migrations
alembic current
```

Required migrations:
- `marketplace_models` - SignalProvider, SignalProviderRating, Payout models
- `indicator_models` - Indicator, IndicatorVersion, IndicatorPurchase models

### 2. Populate Indicator Library

Populate the pre-built indicator library (100+ indicators):

```bash
cd server_fastapi
python -m scripts.populate_indicator_library
```

This will create:
- 100+ technical indicators
- Pre-approved status
- Free indicators available to all users

### 3. Configure Background Jobs

Ensure Celery workers are running for marketplace automation:

```bash
# Start Celery worker
celery -A server_fastapi.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A server_fastapi.celery_app beat --loglevel=info
```

**Scheduled Tasks**:
- Daily metrics updates (2 AM UTC)
- Monthly payouts (1st of month, 3 AM UTC)
- Underperforming provider checks (4 AM UTC)
- Weekly verification (Sunday, 5 AM UTC)
- Daily suspicious provider flagging (6 AM UTC)

### 4. Environment Variables

Required environment variables for marketplaces:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# Redis (for Celery and caching)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Marketplace Configuration
MARKETPLACE_ENABLED=true
INDICATOR_MARKETPLACE_ENABLED=true

# Revenue Split (optional, defaults shown)
MARKETPLACE_REVENUE_SPLIT_PLATFORM=20  # 20% to platform
MARKETPLACE_REVENUE_SPLIT_PROVIDER=80  # 80% to provider
INDICATOR_REVENUE_SPLIT_PLATFORM=30     # 30% to platform
INDICATOR_REVENUE_SPLIT_DEVELOPER=70   # 70% to developer

# Security
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

## API Endpoints

### Copy Trading Marketplace

**Base Path**: `/api/marketplace`

- `POST /apply` - Apply as signal provider
- `GET /traders` - Browse signal providers (with filters)
- `GET /traders/{id}` - Get trader profile
- `POST /traders/{id}/rate` - Rate a trader
- `POST /traders/{id}/update-metrics` - Update metrics (admin)
- `POST /traders/{id}/verify` - Verify performance (admin)
- `POST /traders/verify-all` - Verify all providers (admin)
- `GET /traders/flagged` - Get flagged providers (admin)
- `GET /payouts/calculate` - Calculate payout
- `POST /payouts/create` - Create payout record

### Indicator Marketplace

**Base Path**: `/api/indicators`

- `GET /marketplace` - Browse indicators
- `GET /{id}` - Get indicator details
- `POST /` - Create indicator (developer)
- `POST /{id}/publish` - Publish indicator
- `POST /{id}/version` - Create new version
- `POST /{id}/purchase` - Purchase indicator
- `POST /{id}/rate` - Rate indicator
- `POST /{id}/execute` - Execute indicator
- `POST /volume-profile` - Calculate volume profile

## Testing

### Run Marketplace Tests

```bash
# Copy Trading Marketplace
pytest server_fastapi/tests/test_marketplace_service.py -v
pytest server_fastapi/tests/test_marketplace_routes.py -v

# Indicator Marketplace
pytest server_fastapi/tests/test_indicator_service.py -v
pytest server_fastapi/tests/test_indicator_execution_engine.py -v

# All marketplace tests
pytest server_fastapi/tests/test_marketplace*.py server_fastapi/tests/test_indicator*.py -v
```

### Manual Testing Checklist

**Copy Trading Marketplace**:
- [ ] Apply as signal provider
- [ ] Approve provider (admin)
- [ ] Browse marketplace with filters
- [ ] View trader profile
- [ ] Rate a trader
- [ ] Verify performance (admin)
- [ ] Calculate payout
- [ ] Create payout

**Indicator Marketplace**:
- [ ] Browse indicators
- [ ] View indicator details
- [ ] Purchase indicator
- [ ] Execute indicator
- [ ] Rate indicator
- [ ] Create custom indicator (developer)
- [ ] Publish indicator

## Monitoring

### Key Metrics to Monitor

1. **Marketplace Activity**:
   - Signal provider applications
   - Trader ratings and reviews
   - Payout calculations
   - Verification results

2. **Indicator Marketplace**:
   - Indicator purchases
   - Execution success rate
   - Developer earnings
   - Popular indicators

3. **Background Jobs**:
   - Metrics update success rate
   - Payout calculation accuracy
   - Verification completion
   - Flagged provider alerts

### Health Checks

```bash
# Check Celery workers
celery -A server_fastapi.celery_app inspect active

# Check scheduled tasks
celery -A server_fastapi.celery_app inspect scheduled

# Check API health
curl http://localhost:8000/healthz
```

## Troubleshooting

### Common Issues

**1. Indicators not executing**:
- Check execution engine logs
- Verify RestrictedPython is installed (optional)
- Check timeout settings
- Review code validation errors

**2. Metrics not updating**:
- Verify Celery workers are running
- Check task queue for errors
- Review trade data availability
- Verify database connections

**3. Payouts not calculating**:
- Check revenue data
- Verify follower/subscriber counts
- Review payout calculation logic
- Check for database errors

**4. Verification failures**:
- Review trade history availability
- Check discrepancy thresholds
- Verify metrics calculation
- Review flagged provider logs

## Production Deployment

### Docker Compose

```yaml
services:
  backend:
    # ... existing config
    environment:
      - MARKETPLACE_ENABLED=true
      - INDICATOR_MARKETPLACE_ENABLED=true
  
  celery-worker:
    # ... existing config
    command: celery -A server_fastapi.celery_app worker --loglevel=info
  
  celery-beat:
    # ... existing config
    command: celery -A server_fastapi.celery_app beat --loglevel=info
```

### Kubernetes

Ensure marketplace services are included in deployments:

```yaml
# k8s/backend-deployment.yaml
env:
  - name: MARKETPLACE_ENABLED
    value: "true"
  - name: INDICATOR_MARKETPLACE_ENABLED
    value: "true"
```

### Scaling Considerations

- **API Servers**: Scale based on marketplace traffic
- **Celery Workers**: Scale based on background job load
- **Database**: Monitor query performance, add indexes if needed
- **Redis**: Ensure sufficient memory for caching and task queues

## Security Considerations

1. **Indicator Execution**: Sandboxed environment with timeout limits
2. **Performance Verification**: Admin-only endpoints
3. **Revenue Calculations**: Audit logging for all payouts
4. **API Rate Limiting**: Applied to marketplace endpoints
5. **Input Validation**: All user inputs validated and sanitized

## Next Steps

1. Monitor marketplace activity
2. Review and approve signal provider applications
3. Monitor indicator execution performance
4. Review payout calculations
5. Set up alerts for underperforming providers
6. Configure email notifications (if implemented)

---

**Last Updated**: December 12, 2025  
**Version**: 1.0.0
