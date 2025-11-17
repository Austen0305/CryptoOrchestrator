# CryptoOrchestrator SaaS Setup Guide

Complete guide for setting up CryptoOrchestrator as a SaaS application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Database Migration](#database-migration)
5. [Stripe Configuration](#stripe-configuration)
6. [Production Deployment](#production-deployment)
7. [Environment Variables](#environment-variables)
8. [Testing](#testing)

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for production)
- Stripe account (for billing)

## Backend Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

See [Environment Variables](#environment-variables) for detailed configuration.

### 3. Initialize Database

```bash
# Run Alembic migrations
alembic upgrade head
```

### 4. Start Development Server

```bash
uvicorn server_fastapi.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup

### 1. Install Node.js Dependencies

```bash
cd client
npm install --legacy-peer-deps
```

### 2. Configure Environment Variables

Create `client/.env`:

```env
VITE_API_URL=http://localhost:8000/api
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Database Migration

### Initial Setup

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial SaaS schema"

# Apply migrations
alembic upgrade head
```

### Migration Files

- `alembic/versions/001_initial_saas_schema.py` - Initial users and subscriptions tables

## Stripe Configuration

### 1. Create Stripe Account

1. Sign up at [stripe.com](https://stripe.com)
2. Get your API keys from the Dashboard
3. Create Products and Prices for each subscription tier:
   - Free (price: $0)
   - Basic (monthly/yearly prices)
   - Pro (monthly/yearly prices)
   - Enterprise (monthly/yearly prices)

### 2. Configure Webhooks

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://yourdomain.com/api/billing/webhook`
3. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the webhook signing secret

### 3. Set Environment Variables

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_BASIC_YEARLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
```

## Production Deployment

### Using Docker Compose

1. Copy production environment file:

```bash
cp .env.prod.example .env.prod
```

2. Fill in production values in `.env.prod`

3. Deploy with Docker Compose:

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Manual Deployment

1. Set up PostgreSQL and Redis
2. Run migrations: `alembic upgrade head`
3. Start backend: `uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000`
4. Start Celery worker: `celery -A server_fastapi.celery_app worker --loglevel=info`
5. Start Celery beat: `celery -A server_fastapi.celery_app beat --loglevel=info`
6. Build and serve frontend: `npm run build && nginx -g 'daemon off;'`

## Environment Variables

### Required Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-key-min-32-chars

# Encryption
EXCHANGE_KEY_ENCRYPTION_KEY=your-32-char-encryption-key

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend URL
FRONTEND_URL=https://app.yourdomain.com
```

### Optional Variables

```env
# Email (for password reset, notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Testing

### Backend Tests

```bash
pytest server_fastapi/tests/
```

### Frontend Tests

```bash
cd client
npm test
```

### E2E Tests

```bash
npm run test:e2e
```

## Common Issues

### Database Connection Errors

- Ensure PostgreSQL is running
- Check `DATABASE_URL` format
- Verify database exists and user has permissions

### Stripe Webhook Failures

- Verify webhook secret matches
- Check endpoint is publicly accessible
- Review webhook event logs in Stripe Dashboard

### Celery Worker Not Starting

- Ensure Redis is running
- Check `CELERY_BROKER_URL` is correct
- Verify Redis password if required

## Next Steps

- [Architecture Documentation](./architecture.md)
- [API Documentation](./api.md)
- [Deployment Guide](./deployment.md)
- [Security Best Practices](./security.md)

