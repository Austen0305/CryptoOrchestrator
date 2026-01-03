---
description: Deployment patterns and best practices for CryptoOrchestrator
globs: ["docker-compose*.yml", "Dockerfile*", "k8s/**/*", "terraform/**/*", "*.toml", "Procfile", "render.yaml"]
alwaysApply: false
---

# Deployment Rules

## Environment Configuration

### Environment Variables
```bash
# ✅ Good: Use .env files for local development
# Never commit .env files to version control

# Required for production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production

# Optional
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
```

### Environment-Specific Settings
```python
# ✅ Good: Environment-based configuration
import os
from typing import Literal

ENVIRONMENT: Literal["development", "staging", "production"] = os.getenv(
    "ENVIRONMENT", "development"
)

# Development settings
if ENVIRONMENT == "development":
    DEBUG = True
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
    
# Production settings
elif ENVIRONMENT == "production":
    DEBUG = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    # Enforce HTTPS
    FORCE_HTTPS = True
```

## Docker Deployment

### Dockerfile Best Practices
```dockerfile
# ✅ Good: Multi-stage build for smaller images
FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY server_fastapi/ ./server_fastapi/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Set PATH for pip-installed packages
ENV PATH=/root/.local/bin:$PATH

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "server_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
# ✅ Good: Production-ready docker-compose
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/crypto_orchestrator
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=crypto_orchestrator
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Kubernetes Deployment

### Deployment Manifest
```yaml
# ✅ Good: Production-ready Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crypto-orchestrator-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crypto-orchestrator-backend
  template:
    metadata:
      labels:
        app: crypto-orchestrator-backend
    spec:
      containers:
      - name: backend
        image: your-registry/crypto-orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Database Migrations in Deployment

### Pre-Deployment Migration
```bash
# ✅ Good: Run migrations before deploying new code
# In CI/CD pipeline or deployment script

# 1. Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migrations
alembic upgrade head

# 3. Verify migration
alembic current

# 4. Deploy application
# (deployment steps)
```

### Migration Script
```python
# ✅ Good: Automated migration script
#!/usr/bin/env python3
"""Run database migrations before deployment."""
import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations."""
    alembic_cfg = Config("alembic.ini")
    
    # Set database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    # Convert async URL to sync for Alembic
    sync_url = database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    
    try:
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
```

## Health Checks

### Backend Health Check Endpoint
```python
# ✅ Good: Comprehensive health check
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verifies dependencies."""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
    }
    
    if all(checks.values()):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "checks": checks}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "checks": checks}
        )

async def check_database() -> bool:
    """Check database connectivity."""
    try:
        # Simple query to verify connection
        async with AsyncSession(engine) as session:
            await session.execute(sa.text("SELECT 1"))
        return True
    except Exception:
        return False

async def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        return await cache_service.is_available()
    except Exception:
        return False
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Secrets stored securely (not in code)
- [ ] Health checks implemented
- [ ] Logging configured
- [ ] Monitoring set up

### Deployment
- [ ] Backup database
- [ ] Run migrations
- [ ] Deploy application
- [ ] Verify health checks
- [ ] Test critical endpoints
- [ ] Monitor error rates
- [ ] Check logs for issues

### Post-Deployment
- [ ] Verify all services running
- [ ] Test user flows
- [ ] Monitor performance metrics
- [ ] Check error tracking
- [ ] Verify backups working
- [ ] Document any issues

## Rollback Procedures

### Application Rollback
```bash
# ✅ Good: Quick rollback procedure
# 1. Revert to previous deployment
kubectl rollout undo deployment/crypto-orchestrator-backend

# Or with Docker Compose
docker-compose down
docker-compose up -d --scale backend=3

# 2. Verify rollback
curl https://yourdomain.com/health
```

### Database Rollback
```bash
# ✅ Good: Database migration rollback
# Only if migration caused issues
alembic downgrade -1

# Verify rollback
alembic current
```

## Monitoring and Logging

### Structured Logging
```python
# ✅ Good: Structured logging for production
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

# Configure logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Metrics Collection
```python
# ✅ Good: Export metrics for monitoring
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")
```
