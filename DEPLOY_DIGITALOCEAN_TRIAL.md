# 🚀 **Deploy to DigitalOcean - $200 Free Trial**

**Best For:** Simple deployment, predictable pricing  
**Credits:** $200  
**Duration:** 60 days  
**Your App:** ✅ Can run optimized 2-3GB image  

---

## 📋 **What You Get**

```yaml
Free Trial Credits: $200
Duration: 60 days
Estimated Monthly Cost: ~$66
Free Testing Period: ~3 months

What You Can Run:
  - Droplet (VM): 4GB RAM, 2 vCPU, 80GB SSD ($36/month)
  - Managed PostgreSQL: 1GB RAM, 10GB storage ($15/month)
  - Managed Redis: 1GB RAM ($15/month)
  
Or Simpler:
  - Single 4GB Droplet with Docker Compose: $36/month
  - Duration: ~5.5 months with $200 credits
```

---

## 🎯 **OPTION 1: Simple Single Droplet (Recommended)**

### **Step 1: Sign Up for DigitalOcean**

1. Go to: https://www.digitalocean.com/
2. Click **"Sign Up"** or use this link for $200 credit:
   - https://try.digitalocean.com/freetrialoffer/
3. Create account with email
4. Verify email
5. Add payment method (⚠️ Required, but won't charge during trial)
6. $200 credit applied automatically

**Time:** 5 minutes

---

### **Step 2: Create a Droplet**

1. Click **"Create"** → **"Droplets"**

**Configure Droplet:**

```yaml
Choose an image:
  Distribution: Ubuntu 22.04 LTS

Choose Size:
  Droplet Type: Basic
  CPU Options: Regular (SSD)
  Size: 4GB / 2 CPUs / 80GB SSD / 4TB transfer
  Price: $36/month

Choose Datacenter Region:
  - New York 1 (closest to East Coast)
  - San Francisco 3 (closest to West Coast)
  - Amsterdam 3 (closest to Europe)

Authentication:
  ✅ SSH keys (recommended) OR
  ✅ Password (simpler)

Hostname:
  cryptoorchestrator
```

2. Click **"Create Droplet"**
3. Wait 1-2 minutes for droplet to be ready

**Note your Droplet's IP address** (shown in dashboard)

**Time:** 3 minutes

---

### **Step 3: Connect to Your Droplet**

**If using SSH key:**
```bash
ssh root@YOUR_DROPLET_IP
```

**If using password:**
- Check your email for root password
- Connect via web console in DigitalOcean dashboard
- Or: `ssh root@YOUR_DROPLET_IP` (enter password when prompted)

**Time:** 1 minute

---

### **Step 4: Initial Server Setup**

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install git
apt install git -y

# Verify installations
docker --version
docker-compose --version
git --version
```

**Time:** 5 minutes

---

### **Step 5: Configure Firewall**

```bash
# Install and configure UFW firewall
apt install ufw -y

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow your backend port
ufw allow 8000/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8000/tcp                   ALLOW       Anywhere
```

**Time:** 2 minutes

---

### **Step 6: Clone Repository**

```bash
# Clone your repository
cd /root
git clone https://github.com/Austen0305/CryptoOrchestrator.git
cd CryptoOrchestrator
```

**Time:** 2 minutes

---

### **Step 7: Create Environment Configuration**

```bash
# Create .env file
nano .env
```

Paste this configuration:

```bash
# Database
DATABASE_URL=postgresql://cryptouser:CHANGE_THIS_PASSWORD@postgres:5432/cryptodb
POSTGRES_USER=cryptouser
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=cryptodb

# Redis
REDIS_URL=redis://redis:6379/0

# Security - GENERATE NEW KEYS!
SECRET_KEY=GENERATE_NEW_64_CHAR_KEY
JWT_SECRET_KEY=GENERATE_NEW_JWT_SECRET

# App Configuration
ENVIRONMENT=production
BACKEND_URL=http://YOUR_DROPLET_IP:8000
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://your-frontend.vercel.app

# Optional Services
STRIPE_SECRET_KEY=your_stripe_key_if_needed
TWILIO_ACCOUNT_SID=your_twilio_sid_if_needed
TWILIO_AUTH_TOKEN=your_twilio_token_if_needed
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY (64 char hex)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate DB Password
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

Copy the generated keys and replace the placeholders in .env

Save: `Ctrl+X`, `Y`, `Enter`

**Time:** 5 minutes

---

### **Step 8: Create Docker Compose Configuration**

```bash
# Create production docker-compose file
nano docker-compose.deploy.yml
```

Paste this:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: crypto-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: crypto-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    container_name: crypto-backend
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    container_name: crypto-celery-worker
    command: celery -A server_fastapi.celery_app worker --loglevel=info
    env_file: .env
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    container_name: crypto-celery-beat
    command: celery -A server_fastapi.celery_app beat --loglevel=info
    env_file: .env
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

Save: `Ctrl+X`, `Y`, `Enter`

**Time:** 3 minutes

---

### **Step 9: Build and Deploy**

```bash
# Build the optimized Docker image
export DOCKER_BUILDKIT=1
docker-compose -f docker-compose.deploy.yml build --no-cache

# Start all services
docker-compose -f docker-compose.deploy.yml up -d

# Check status
docker-compose -f docker-compose.deploy.yml ps

# View logs
docker-compose -f docker-compose.deploy.yml logs -f backend
```

**Time:** 10-15 minutes (for building)

---

### **Step 10: Run Database Migrations**

```bash
# Wait for backend to be healthy (30-60 seconds)
sleep 60

# Run migrations
docker exec crypto-backend alembic upgrade head

# Verify database
docker exec crypto-backend python -c "
from server_fastapi.database import SessionLocal
db = SessionLocal()
print('Database connection successful!')
db.close()
"
```

**Time:** 2 minutes

---

### **Step 11: Test Your Backend**

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API docs
curl http://localhost:8000/docs
```

**From your computer:**
```bash
# Replace with your droplet IP
curl http://YOUR_DROPLET_IP:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

**Test in browser:**
- Visit: `http://YOUR_DROPLET_IP:8000/docs`
- You should see FastAPI Swagger documentation

**Time:** 2 minutes

---

### **Step 12: Deploy Frontend to Vercel**

1. Go to: https://vercel.com
2. Sign in with GitHub
3. Click **"New Project"**
4. Import your repository: `CryptoOrchestrator`
5. Configure:

```yaml
Framework Preset: Vite
Root Directory: client
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

6. Add Environment Variable:
```
Name: VITE_API_URL
Value: http://YOUR_DROPLET_IP:8000
```

7. Click **"Deploy"**

**Time:** 5 minutes

---

### **Step 13: Update CORS in Backend**

```bash
# Edit .env on droplet
nano .env
```

Update `ALLOWED_ORIGINS` with your Vercel URL:
```
ALLOWED_ORIGINS=https://your-app.vercel.app,http://your-app.vercel.app,http://YOUR_DROPLET_IP:8000
```

Restart backend:
```bash
docker-compose -f docker-compose.deploy.yml restart backend
```

**Time:** 2 minutes

---

## ✅ **You're Live!**

```yaml
✅ Backend API: http://YOUR_DROPLET_IP:8000
✅ API Docs: http://YOUR_DROPLET_IP:8000/docs  
✅ Frontend: https://your-app.vercel.app
✅ Database: PostgreSQL (internal)
✅ Cache: Redis (internal)
✅ Workers: Celery (internal)

💰 Cost: $0 (using $200 trial credits)
⏱️ Duration: ~5.5 months free ($36/month)
```

---

## 📊 **Monitor Your Credits**

1. Go to DigitalOcean dashboard
2. Click your profile → **Billing**
3. View **Credits & Promotions**
4. See remaining balance

Set up billing alerts:
1. **Billing** → **Settings** → **Email Preferences**
2. Enable: **Billing threshold alerts**

---

## 🔄 **Maintenance Commands**

```bash
# View all logs
docker-compose -f docker-compose.deploy.yml logs -f

# Restart all services
docker-compose -f docker-compose.deploy.yml restart

# Update application
cd /root/CryptoOrchestrator
git pull origin main
docker-compose -f docker-compose.deploy.yml build --no-cache
docker-compose -f docker-compose.deploy.yml up -d

# Backup database
docker exec crypto-postgres pg_dump -U cryptouser cryptodb > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20251226.sql | docker exec -i crypto-postgres psql -U cryptouser -d cryptodb

# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up Docker
docker system prune -a
```

---

## 🚨 **Troubleshooting**

### **Backend not accessible**

```bash
# Check if services are running
docker-compose -f docker-compose.deploy.yml ps

# Check backend logs
docker logs crypto-backend

# Check firewall
ufw status

# Verify port is listening
netstat -tulpn | grep 8000
```

### **Database connection issues**

```bash
# Check PostgreSQL logs
docker logs crypto-postgres

# Test connection
docker exec crypto-postgres psql -U cryptouser -d cryptodb -c "SELECT 1;"
```

### **Out of memory**

```bash
# Check memory usage
free -h

# Check Docker stats
docker stats

# Option: Upgrade to 8GB droplet ($72/month)
# DigitalOcean dashboard → Resize → Choose 8GB
```

### **Build fails**

```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose -f docker-compose.deploy.yml build --no-cache --pull

# Check logs
docker-compose -f docker-compose.deploy.yml logs builder
```

---

## 🔒 **Security Best Practices**

```bash
# 1. Create non-root user
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy

# 2. Disable root SSH login
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart sshd

# 3. Enable automatic security updates
apt install unattended-upgrades -y
dpkg-reconfigure -plow unattended-upgrades

# 4. Set up Fail2Ban
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban

# 5. Regular backups (add to crontab)
crontab -e
# Add: 0 2 * * * /root/backup.sh
```

---

## 🌐 **Optional: Add Custom Domain**

### **With Cloudflare (Free SSL):**

1. Point your domain's A record to: `YOUR_DROPLET_IP`
2. Wait for DNS propagation (5-60 minutes)
3. Update `.env`:
   ```
   BACKEND_URL=https://api.yourdomain.com
   ALLOWED_ORIGINS=https://yourdomain.com
   ```
4. Set up Nginx reverse proxy with Let's Encrypt:

```bash
# Install Nginx
apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
nano /etc/nginx/sites-available/cryptoorchestrator

# Add:
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
ln -s /etc/nginx/sites-available/cryptoorchestrator /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d api.yourdomain.com
```

---

## 💰 **After Trial Ends**

### **Option 1: Continue on DigitalOcean**
```yaml
Cost: $36/month (4GB droplet)
Action: Enable billing, continue using
```

### **Option 2: Migrate to Oracle Cloud (Free Forever)**
```yaml
Cost: $0/month forever
Action: Follow ORACLE_CLOUD_SETUP_2025.md
Steps:
  1. Export data from DigitalOcean
  2. Create Oracle Cloud account
  3. Deploy to always-free tier
  4. Import data
```

### **Option 3: Downgrade to Smaller Droplet**
```yaml
Cost: $18/month (2GB droplet)
Action: May work with optimized image
Risk: Might be tight on memory
```

---

## 📈 **Performance Monitoring**

```bash
# Install monitoring tools
apt install htop iotop nethogs -y

# Real-time resource monitoring
htop

# Monitor Docker containers
docker stats

# Check application logs
docker-compose -f docker-compose.deploy.yml logs -f backend
```

---

## 🎉 **Success Checklist**

- ✅ Droplet created and accessible
- ✅ Docker and Docker Compose installed
- ✅ Application running on port 8000
- ✅ PostgreSQL database healthy
- ✅ Redis cache connected
- ✅ Celery workers running
- ✅ Health endpoint returns 200 OK
- ✅ API docs accessible at /docs
- ✅ Frontend deployed to Vercel
- ✅ CORS configured correctly
- ✅ All services restart automatically

---

**Total Setup Time:** 45-60 minutes  
**Monthly Cost (after trial):** $36  
**Trial Duration:** 60 days ($200 credits = ~5.5 months)  
**Difficulty:** ⭐⭐ Easy  
**Recommended For:** Quick deployment with simple management  

---

*Created: December 26, 2025*  
*Guide Version: 1.0*  
*Status: ✅ Production Ready*
