# Production Deployment Configuration Guide

## Environment Variables Setup

Create a `.env.production` file with these settings:

```env
# Application
NODE_ENV=production
PORT=8000
HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/cryptoorchestrator
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis (Required for distributed features)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_secure_password
REDIS_MAX_CONNECTIONS=50

# Security
JWT_SECRET=your_super_secret_jwt_key_change_this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
API_KEY_SECRET=your_api_key_encryption_secret

# Rate Limiting
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_STORAGE=redis

# Circuit Breaker
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
CIRCUIT_BREAKER_RESET_TIMEOUT=300

# Caching
CACHE_TTL_SECONDS=300
CACHE_WARMING_THRESHOLD=0.8
ENABLE_CACHE_WARMING=true

# Exchange APIs (Add your exchange credentials)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_API_SECRET=your_kraken_api_secret

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=300

# Arbitrage
ARBITRAGE_MIN_PROFIT_PERCENT=0.5
ARBITRAGE_MAX_POSITION_SIZE=10000
ARBITRAGE_SCAN_INTERVAL=5

# Backtesting
BACKTEST_MAX_SIMULATIONS=10000
BACKTEST_CACHE_RESULTS=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO

# Email/SMS Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# Payment Integration (For Marketplace)
STRIPE_API_KEY=sk_live_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Mobile Push Notifications
FCM_SERVER_KEY=your_firebase_server_key
APNS_KEY_ID=your_apple_push_key_id
APNS_TEAM_ID=your_apple_team_id
```

## Database Setup

### 1. Install PostgreSQL

```powershell
# Using Chocolatey
choco install postgresql

# Or download from https://www.postgresql.org/download/windows/
```

### 2. Create Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE cryptoorchestrator;

-- Create user
CREATE USER crypto_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE cryptoorchestrator TO crypto_user;
```

### 3. Run Migrations

```powershell
cd "c:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator"

# Install alembic if not already installed
pip install alembic

# Run migrations
npm run migrate
```

## Redis Setup

### 1. Install Redis on Windows

```powershell
# Using WSL (recommended)
wsl --install
wsl
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start

# Or use Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Or install native Windows port
choco install redis-64
```

### 2. Configure Redis

Edit `redis.conf`:

```conf
# Security
requirepass your_secure_password
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
bind 127.0.0.1
port 6379
```

### 3. Start Redis

```powershell
# WSL
sudo service redis-server start

# Docker
docker start redis

# Windows Service
redis-server --service-start
```

## SSL/TLS Configuration

### 1. Generate Certificates

```powershell
# Using OpenSSL
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt (production)
# Install certbot and follow instructions at https://certbot.eff.org/
```

### 2. Configure Uvicorn for HTTPS

Update `server_fastapi/main.py`:

```python
if __name__ == "__main__":
    uvicorn_config = {
        "app": app,
        "host": "0.0.0.0",
        "port": 8000,
        "ssl_keyfile": "./certs/key.pem",
        "ssl_certfile": "./certs/cert.pem",
        "workers": 4,  # Multiple workers for production
    }
    uvicorn.run(**uvicorn_config)
```

## Monitoring Setup

### 1. Install Prometheus (Optional)

```powershell
choco install prometheus

# Edit prometheus.yml
# Add:
#   - job_name: 'cryptoorchestrator'
#     static_configs:
#       - targets: ['localhost:9090']
```

### 2. Install Grafana (Optional)

```powershell
choco install grafana

# Start Grafana
grafana-server

# Access: http://localhost:3000
# Default login: admin/admin
```

### 3. Configure Logging

Update `server_fastapi/main.py` logging:

```python
import logging
from logging.handlers import RotatingFileHandler

# Production logging
handler = RotatingFileHandler(
    'logs/production.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(handler)
```

## Reverse Proxy Setup (Nginx)

### 1. Install Nginx

```powershell
choco install nginx
```

### 2. Configure Nginx

Create `/etc/nginx/sites-available/cryptoorchestrator`:

```nginx
upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # API requests
    location /api/ {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        root /var/www/cryptoorchestrator/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## Backup Strategy

### 1. Database Backups

```powershell
# Create backup script: scripts/backup_db.ps1
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "backups/db_backup_$timestamp.sql"

pg_dump -U crypto_user cryptoorchestrator > $backupFile

# Compress
Compress-Archive -Path $backupFile -DestinationPath "$backupFile.zip"
Remove-Item $backupFile

# Upload to cloud storage (optional)
# aws s3 cp "$backupFile.zip" s3://your-bucket/backups/
```

### 2. Schedule Backups

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument '-File C:\path\to\backup_db.ps1'
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "CryptoOrchestratorBackup" -Action $action -Trigger $trigger
```

## Performance Optimization

### 1. Database Indexing

```sql
-- Add indexes for common queries
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_bots_status ON bots(status);
CREATE INDEX idx_portfolio_user_id ON portfolio(user_id);
```

### 2. Redis Configuration

```conf
# Optimize for performance
maxmemory-policy allkeys-lru
tcp-backlog 511
tcp-keepalive 300
```

### 3. Uvicorn Workers

```python
# Use multiple workers in production
uvicorn_config = {
    "workers": 4,  # Number of CPU cores
    "worker_class": "uvicorn.workers.UvicornWorker",
}
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong JWT secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Enable audit logging
- [ ] Implement API key rotation
- [ ] Use environment variables (never commit secrets)
- [ ] Enable database encryption
- [ ] Configure Redis authentication
- [ ] Set up intrusion detection
- [ ] Regular backups
- [ ] Disaster recovery plan

## Deployment Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Configure production database
- [ ] Set up Redis
- [ ] Generate SSL certificates
- [ ] Configure Nginx reverse proxy
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Test all endpoints
- [ ] Run integration tests
- [ ] Configure CI/CD pipeline
- [ ] Set up alerts and notifications
- [ ] Document deployment process
- [ ] Train operations team
- [ ] Create runbook for common issues

## Scaling Considerations

### Horizontal Scaling

```nginx
# Load balancer configuration
upstream fastapi_cluster {
    least_conn;
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    server 192.168.1.12:8000;
}
```

### Database Replication

```sql
-- Set up read replicas for scaling reads
-- Configure master-slave replication
-- Use connection pooling
```

### Redis Cluster

```conf
# Redis cluster mode for high availability
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
```

## Monitoring Endpoints

- Health: `GET /api/health`
- Metrics: `GET /api/metrics/monitoring/metrics`
- Circuit Breakers: `GET /api/circuit-breaker/metrics`
- Cache Stats: `GET /api/cache/stats`
- Arbitrage Stats: `GET /api/arbitrage/stats`
- Marketplace Stats: `GET /api/marketplace/stats`

## Troubleshooting

### Common Issues

**Database Connection Refused**
```powershell
# Check PostgreSQL is running
Get-Service postgresql*
# Restart if needed
Restart-Service postgresql-x64-14
```

**Redis Connection Failed**
```powershell
# Check Redis is running
docker ps | grep redis
# Test connection
redis-cli ping
```

**High Memory Usage**
```powershell
# Monitor with
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10
# Adjust worker count in uvicorn config
```

**Slow API Responses**
- Check database query performance
- Review circuit breaker status
- Monitor Redis hit rates
- Check network latency

## Support

For production issues, check:
1. Application logs: `logs/production.log`
2. System metrics: `http://localhost:8000/api/metrics/monitoring/metrics`
3. Database logs: PostgreSQL log directory
4. Redis logs: `/var/log/redis/redis-server.log`

## Next Steps

1. Run test script: `.\scripts\test_features.ps1`
2. Configure environment variables
3. Set up database and Redis
4. Run integration tests
5. Deploy to staging environment
6. Perform load testing
7. Deploy to production
8. Monitor for 24 hours
9. Set up automated alerts
10. Document any issues and resolutions
