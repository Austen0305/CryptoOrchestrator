# Deployment and Operations Guide

## Infrastructure Setup

### Production Environment Requirements

#### System Requirements
- **Operating System**: Ubuntu 22.04 LTS or RHEL 8+
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB SSD minimum (NVMe recommended)
- **Network**: 100Mbps+ dedicated connection

#### Software Dependencies
- **Python**: 3.8+ with pip and virtualenv
- **Node.js**: 18+ with npm
- **Database**: PostgreSQL 13+ or SQLite (development only)
- **Redis**: 6.0+ for caching and session management
- **Nginx**: 1.20+ for reverse proxy
- **SSL/TLS**: Certbot for Let's Encrypt certificates

### Infrastructure Components

#### Application Server
```
FastAPI Backend (Python)
├── Gunicorn WSGI server
├── Uvicorn ASGI workers
├── Process manager (systemd)
└── Reverse proxy (Nginx)
```

#### Database Layer
```
PostgreSQL Cluster
├── Primary database server
├── Read replicas (optional)
├── Automated backups
└── Connection pooling (PgBouncer)
```

#### Caching Layer
```
Redis Cluster
├── Session storage
├── API response caching
├── Rate limiting data
└── Background job queues
```

#### Monitoring Stack
```
ELK Stack (Elasticsearch, Logstash, Kibana)
├── Centralized logging
├── Log analysis and visualization
├── Alert management
└── Performance monitoring
```

## Deployment Procedures

### Automated Deployment

#### CI/CD Pipeline Setup

##### GitHub Actions Workflow
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          npm install
      - name: Run tests
        run: |
          npm run test
          python -m pytest server_fastapi/tests/
      - name: Build application
        run: npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.PRODUCTION_KEY }}
          script: |
            cd /opt/cryptoorchestrator
            git pull origin main
            ./deploy.sh
```

#### Deployment Script (`deploy.sh`)
```bash
#!/bin/bash

# Deployment script for CryptoOrchestrator
set -e

echo "Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="cryptoorchestrator"
APP_DIR="/opt/$APP_NAME"
BACKUP_DIR="/opt/backups"
VENV_DIR="$APP_DIR/venv"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Create backup
create_backup() {
    log "Creating backup..."
    TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
    BACKUP_FILE="$BACKUP_DIR/${APP_NAME}_$TIMESTAMP.tar.gz"

    mkdir -p "$BACKUP_DIR"
    tar -czf "$BACKUP_FILE" -C "$APP_DIR" . --exclude='logs/*' --exclude='*.log'

    # Keep only last 7 backups
    ls -t "$BACKUP_DIR"/*.tar.gz | tail -n +8 | xargs -r rm

    log "Backup created: $BACKUP_FILE"
}

# Stop services
stop_services() {
    log "Stopping services..."
    sudo systemctl stop cryptoorchestrator-api || true
    sudo systemctl stop cryptoorchestrator-worker || true
}

# Start services
start_services() {
    log "Starting services..."
    sudo systemctl start cryptoorchestrator-api
    sudo systemctl start cryptoorchestrator-worker

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log "Services are healthy"
            break
        fi
        sleep 2
    done

    if [ $i -eq 30 ]; then
        error "Services failed to start properly"
        exit 1
    fi
}

# Main deployment process
main() {
    log "Starting deployment of $APP_NAME"

    # Pre-deployment checks
    if [ ! -d "$APP_DIR" ]; then
        error "Application directory $APP_DIR does not exist"
        exit 1
    fi

    cd "$APP_DIR"

    # Create backup
    create_backup

    # Stop services
    stop_services

    # Update code
    log "Updating code..."
    git fetch origin
    git reset --hard origin/main

    # Update Python dependencies
    log "Updating Python dependencies..."
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt --upgrade

    # Update Node.js dependencies
    log "Updating Node.js dependencies..."
    npm ci

    # Build application
    log "Building application..."
    npm run build

    # Run database migrations
    log "Running database migrations..."
    python manage.py migrate

    # Collect static files
    log "Collecting static files..."
    python manage.py collectstatic --noinput

    # Start services
    start_services

    # Run health checks
    log "Running final health checks..."
    if curl -f http://localhost:8000/health | grep -q "healthy"; then
        log "Deployment completed successfully!"
    else
        error "Health check failed"
        exit 1
    fi

    # Clean up old backups (keep last 7 days)
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
}

# Error handling
trap 'error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
```

### Manual Deployment

#### Initial Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql redis nginx certbot

# Create application user
sudo useradd -m -s /bin/bash cryptoorchestrator

# Create application directory
sudo mkdir -p /opt/cryptoorchestrator
sudo chown cryptoorchestrator:cryptoorchestrator /opt/cryptoorchestrator

# Set up Python virtual environment
sudo -u cryptoorchestrator python3 -m venv /opt/cryptoorchestrator/venv
```

#### Application Deployment
```bash
# Clone repository
sudo -u cryptoorchestrator git clone https://github.com/yourorg/cryptoorchestrator.git /opt/cryptoorchestrator/app

# Install Python dependencies
sudo -u cryptoorchestrator bash -c "source /opt/cryptoorchestrator/venv/bin/activate && pip install -r /opt/cryptoorchestrator/app/requirements.txt"

# Install Node.js dependencies
sudo -u cryptoorchestrator bash -c "cd /opt/cryptoorchestrator/app && npm install"

# Build application
sudo -u cryptoorchestrator bash -c "cd /opt/cryptoorchestrator/app && npm run build"

# Set up environment variables
sudo -u cryptoorchestrator cp /opt/cryptoorchestrator/app/.env.example /opt/cryptoorchestrator/app/.env
# Edit .env file with production values
```

#### Systemd Service Configuration

##### API Service (`/etc/systemd/system/cryptoorchestrator-api.service`)
```ini
[Unit]
Description=CryptoOrchestrator API Server
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=cryptoorchestrator
Group=cryptoorchestrator
WorkingDirectory=/opt/cryptoorchestrator/app
Environment=PATH=/opt/cryptoorchestrator/venv/bin
ExecStart=/opt/cryptoorchestrator/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /opt/cryptoorchestrator/logs/access.log \
    --error-logfile /opt/cryptoorchestrator/logs/error.log
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

##### Worker Service (`/etc/systemd/system/cryptoorchestrator-worker.service`)
```ini
[Unit]
Description=CryptoOrchestrator Background Worker
After=network.target redis.service

[Service]
Type=exec
User=cryptoorchestrator
Group=cryptoorchestrator
WorkingDirectory=/opt/cryptoorchestrator/app
Environment=PATH=/opt/cryptoorchestrator/venv/bin
ExecStart=/opt/cryptoorchestrator/venv/bin/python worker.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration (`/etc/nginx/sites-available/cryptoorchestrator`)
```nginx
upstream cryptoorchestrator_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header Referrer-Policy strict-origin-when-cross-origin;

    # API endpoints
    location /api/ {
        proxy_pass http://cryptoorchestrator_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api burst=10 nodelay;

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With";
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://cryptoorchestrator_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/cryptoorchestrator/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check (internal)
    location /health {
        proxy_pass http://cryptoorchestrator_api;
        access_log off;
    }

    # Default location - serve React app
    location / {
        try_files $uri $uri/ /index.html;
        root /opt/cryptoorchestrator/app/dist;
        index index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### Database Configuration

#### PostgreSQL Setup
```sql
-- Create database and user
CREATE DATABASE cryptoorchestrator;
CREATE USER cryptobot WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE cryptoorchestrator TO cryptobot;

-- Create extensions
\c cryptoorchestrator;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set up schema
-- (Run migrations from application)
```

#### Redis Configuration (`/etc/redis/redis.conf`)
```ini
# Basic configuration
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300

# Security
protected-mode yes
requirepass your_secure_redis_password

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis.log
```

### Monitoring and Logging Setup

#### ELK Stack Configuration

##### Logstash Configuration (`/etc/logstash/conf.d/cryptoorchestrator.conf`)
```ruby
input {
  file {
    path => "/opt/cryptoorchestrator/logs/*.log"
    start_position => "beginning"
    sincedb_path => "/var/lib/logstash/sincedb"
  }
}

filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:logger} - %{GREEDYDATA:message}" }
  }

  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "cryptoorchestrator-%{+YYYY.MM.dd}"
  }
}
```

##### Kibana Dashboard Setup
1. Import provided dashboard configurations
2. Set up index patterns for log data
3. Configure alerts and visualizations

#### Prometheus Monitoring

##### Prometheus Configuration (`/etc/prometheus/prometheus.yml`)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'cryptoorchestrator'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

##### Grafana Dashboards
- Application performance metrics
- System resource monitoring
- Business metrics (trading volume, user activity)
- Error rates and alerting

### Backup and Recovery

#### Automated Backup Script (`/opt/cryptoorchestrator/backup.sh`)
```bash
#!/bin/bash

# Backup script for CryptoOrchestrator
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
log "Creating database backup..."
pg_dump -U cryptobot -h localhost cryptoorchestrator > "$BACKUP_DIR/db_$DATE.sql"

# Application files backup
log "Creating application backup..."
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" \
    --exclude='logs/*' \
    --exclude='*.log' \
    --exclude='node_modules' \
    /opt/cryptoorchestrator/app

# Redis backup (if using persistence)
# redis-cli --rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Encrypt backups
log "Encrypting backups..."
gpg --encrypt --recipient backup@cryptoorchestrator.com "$BACKUP_DIR/db_$DATE.sql"
gpg --encrypt --recipient backup@cryptoorchestrator.com "$BACKUP_DIR/app_$DATE.tar.gz"

# Remove unencrypted files
rm "$BACKUP_DIR/db_$DATE.sql" "$BACKUP_DIR/app_$DATE.tar.gz"

# Upload to remote storage (optional)
# aws s3 cp "$BACKUP_DIR/" s3://cryptoorchestrator-backups/ --recursive

# Cleanup old backups
find "$BACKUP_DIR" -name "*.gpg" -mtime +$RETENTION_DAYS -delete

log "Backup completed: $DATE"
```

#### Recovery Procedures

##### Database Recovery
```bash
# Stop application
sudo systemctl stop cryptoorchestrator-api

# Restore database
pg_restore -U cryptobot -h localhost -d cryptoorchestrator /path/to/backup.sql

# Restart application
sudo systemctl start cryptoorchestrator-api
```

##### Application Recovery
```bash
# Extract backup
tar -xzf /path/to/app_backup.tar.gz -C /opt/cryptoorchestrator/

# Restore dependencies
cd /opt/cryptoorchestrator/app
source ../venv/bin/activate
pip install -r requirements.txt
npm install

# Restart services
sudo systemctl restart cryptoorchestrator-api
```

### Security Hardening

#### Server Hardening
```bash
# Disable root login
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Use fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

#### Application Security
- Regular dependency updates
- Security scanning in CI/CD pipeline
- Log monitoring and alerting
- Regular security audits

### Performance Optimization

#### Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_trades_user_id ON trades(user_id);
CREATE INDEX CONCURRENTLY idx_trades_symbol ON trades(symbol);
CREATE INDEX CONCURRENTLY idx_trades_timestamp ON trades(timestamp);

-- Analyze tables for query optimization
ANALYZE trades;
ANALYZE users;
ANALYZE portfolios;
```

#### Application Optimization
- Gunicorn worker tuning based on CPU cores
- Redis connection pooling
- Database connection pooling with SQLAlchemy
- Static file caching and compression
- CDN integration for global performance

### Scaling Procedures

#### Horizontal Scaling
- Load balancer configuration (nginx upstream)
- Session storage in Redis
- Database read replicas
- Microservices architecture preparation

#### Vertical Scaling
- Memory and CPU monitoring
- Performance bottleneck identification
- Resource allocation adjustments

### Maintenance Procedures

#### Regular Maintenance Tasks
- **Daily**: Log rotation and cleanup
- **Weekly**: Security updates and patches
- **Monthly**: Performance optimization and monitoring review
- **Quarterly**: Security audits and compliance checks

#### Emergency Maintenance
- Service degradation procedures
- Database maintenance windows
- Zero-downtime deployment procedures

### Compliance and Auditing

#### Audit Logging
- All user actions logged with timestamps
- Sensitive operations require additional authorization
- Log integrity protection with hash chaining
- Regular log reviews and analysis

#### Compliance Monitoring
- GDPR compliance monitoring
- Financial regulation adherence
- Security control effectiveness
- Incident response capability testing

---

This deployment guide provides comprehensive procedures for setting up and maintaining a production CryptoOrchestrator environment. Regular updates and testing are essential for maintaining system reliability and security.