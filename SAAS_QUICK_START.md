# CryptoOrchestrator SaaS - Quick Start Guide

## 🎯 Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Stripe account for billing
- Domain name (for production)

## ⚡ 5-Minute Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd Crypto-Orchestrator
```

### 2. Configure Environment
```bash
# Copy production environment template
cp .env.prod.example .env.prod

# Edit .env.prod with your values:
# - Database credentials
# - Redis password
# - JWT secrets (generate strong random strings)
# - Stripe keys
# - Domain names
```

### 3. Generate Secrets
```bash
# Generate JWT secrets (32+ characters)
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For JWT_REFRESH_SECRET
openssl rand -hex 32  # For EXCHANGE_KEY_ENCRYPTION_KEY

# Generate Redis password
openssl rand -hex 16
```

### 4. Stripe Setup
1. Create Stripe account at https://stripe.com
2. Get API keys from Dashboard
3. Create Products for each subscription tier:
   - Basic ($29/month, $290/year)
   - Pro ($99/month, $990/year)
   - Enterprise ($299/month, $2990/year)
4. Copy Price IDs to `.env.prod`
5. Create webhook endpoint: `https://yourdomain.com/api/billing/webhook`
6. Select events: `customer.subscription.*`, `invoice.payment_*`
7. Copy webhook secret to `.env.prod`

### 5. Deploy
```bash
# Start all services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 6. Verify Deployment
```bash
# Check backend health
curl http://localhost:8000/healthz

# Check frontend
curl http://localhost:5173
```

## 🔑 Initial Admin Account

1. Register through frontend at `/register`
2. Update user role to `admin` in database:
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
   ```
3. Access admin panel at `/api/admin`

## 📋 Post-Deployment Checklist

- [ ] Verify Stripe webhook is receiving events
- [ ] Test user registration and login
- [ ] Test subscription creation
- [ ] Verify email delivery (password reset)
- [ ] Test exchange API key encryption
- [ ] Verify Celery workers are running
- [ ] Check application logs for errors
- [ ] Set up SSL certificates (Traefik)
- [ ] Configure domain DNS
- [ ] Set up monitoring (Sentry)

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli -a <password> ping
```

### Celery Worker Issues
```bash
# Check worker logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker
```

### Frontend Not Loading
```bash
# Check frontend container
docker-compose ps frontend

# View logs
docker-compose logs frontend

# Rebuild if needed
docker-compose -f docker-compose.prod.yml build frontend
```

## 📞 Support

For detailed documentation:
- Setup: [docs/SAAS_SETUP.md](docs/SAAS_SETUP.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- API: [docs/api.md](docs/api.md)

## 🎉 You're Ready!

Your CryptoOrchestrator SaaS platform is now running. Start creating accounts, managing subscriptions, and running trading bots!

