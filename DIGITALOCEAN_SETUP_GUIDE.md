# 🌊 **DIGITALOCEAN COMPLETE SETUP GUIDE**
## Deploy Your 10GB CryptoOrchestrator in 30 Minutes

**Date:** December 26, 2025  
**Time Required:** 20-30 minutes  
**Free Period:** 60 days ($200 credit)  
**After Trial:** $66/month (or migrate to free hosting)

---

## 🎯 **WHAT YOU'LL GET**

```yaml
Trial Period (60 days):
  Credits: $200
  Cost: $0
  
Your Setup:
  Droplet (VM): 4GB RAM, 2 vCPU, 80GB SSD ($36/month)
  PostgreSQL: Managed database ($15/month)
  Redis: Managed cache ($15/month)
  Total: $66/month (covered by $200 for ~3 months)

After 60 Days:
  Option 1: Continue at $66/month
  Option 2: Migrate to free hosting (I'll help)
  Option 3: Optimize to lower tier ($24/month)
```

---

## ✅ **WHAT WORKS**

```yaml
✅ Full 10GB Docker image (TensorFlow + PyTorch)
✅ FastAPI backend
✅ PostgreSQL database (managed)
✅ Redis cache (managed)
✅ Celery workers
✅ React frontend
✅ All ML features
✅ All trading features
✅ WebSocket support
```

---

## 📋 **WHAT YOU NEED**

```yaml
Required:
  ✅ Email address
  ✅ Credit card (will charge ONLY after $200 runs out)
  ✅ 20-30 minutes

Nice to Have:
  ✅ GitHub account (for easy deployment)
  ✅ Domain name (optional, for custom URL)
```

---

## 🚀 **STEP-BY-STEP SETUP**

---

## **PART 1: CREATE DIGITALOCEAN ACCOUNT** (5 minutes)

### **Step 1.1: Sign Up**

1. **Go to:** https://www.digitalocean.com

2. **Click:** "Sign Up" (top right)

3. **Sign up with:**
   - **Email** (recommended for $200 credit)
   - OR Google
   - OR GitHub

4. **Enter email and password**

5. **Verify email:**
   - Check your inbox
   - Click verification link

---

### **Step 1.2: Get $200 Credit**

1. **After email verification**, you should see a banner for free credits

2. **If you see a promo code field:**
   - Try: `DORETRY200` or `DO200`
   - Or search "DigitalOcean $200 credit December 2025"

3. **Alternatively:**
   - New accounts automatically get $200 for 60 days
   - Check your account balance after adding payment method

---

### **Step 1.3: Add Payment Method**

1. **Click:** "Billing" in left sidebar

2. **Add Payment Method:**
   - Enter credit card details
   - Billing address

3. **Verify:**
   - Small verification charge (~$1, refunded immediately)
   - SMS verification code (if requested)

4. **Check Balance:**
   - Should show $200 credit
   - Valid for 60 days

---

## **PART 2: CREATE DROPLET (VM)** (10 minutes)

### **Step 2.1: Create Droplet**

1. **Click:** "Create" (top right) → "Droplets"

2. **Choose Region:**
   ```
   Recommended:
   - New York (US East)
   - San Francisco (US West)
   - London (Europe)
   - Singapore (Asia)
   
   Choose closest to you or your users
   ```

---

### **Step 2.2: Choose Image**

1. **Select:** "Marketplace" tab

2. **Search:** "Docker"

3. **Select:** "Docker on Ubuntu 22.04"
   - Pre-installed Docker
   - Pre-installed Docker Compose
   - Saves time!

**OR if not using Marketplace:**
- Choose "Ubuntu" → "22.04 (LTS) x64"
- We'll install Docker manually

---

### **Step 2.3: Choose Size**

**IMPORTANT:** Choose the right size for your 10GB app

1. **Click:** "General Purpose" tab

2. **Select:**
   ```
   CPU options: Regular
   
   Choose: 4GB RAM / 2 vCPUs / 80GB SSD
   Price: $36/month
   
   This is minimum for your 10GB app
   ```

**For better performance (optional):**
```
Choose: 8GB RAM / 4 vCPUs / 160GB SSD
Price: $72/month
(Would give you less trial time but better performance)
```

**Recommendation:** Start with 4GB, upgrade if needed

---

### **Step 2.4: Choose Authentication**

**Option A: SSH Key (Recommended)**

1. **On YOUR computer, open PowerShell/Terminal:**

   ```powershell
   # Windows PowerShell
   ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\digitalocean_key" -N '""'
   
   # Mac/Linux
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/digitalocean_key -N ""
   ```

2. **Copy your public key:**
   ```powershell
   # Windows
   Get-Content "$HOME\.ssh\digitalocean_key.pub"
   
   # Mac/Linux
   cat ~/.ssh/digitalocean_key.pub
   ```

3. **In DigitalOcean:**
   - Click "New SSH Key"
   - Paste your public key
   - Name it: `my-key`
   - Click "Add SSH Key"
   - Select the checkbox next to it

**Option B: Password (Easier but less secure)**

1. **Select:** "Password"
2. **You'll receive root password via email**

---

### **Step 2.5: Finalize and Create**

1. **Hostname:**
   ```
   cryptoorchestrator-app
   ```

2. **Tags (optional):**
   ```
   production, crypto, ml-app
   ```

3. **Backups (optional):**
   - Uncheck for now (adds 20% cost)
   - Can enable later

4. **Monitoring:**
   - ✅ Check "Monitoring" (free)

5. **Click:** "Create Droplet"

6. **Wait 1-2 minutes** for droplet creation

7. **Copy the Public IP Address** when shown
   - Example: `134.209.XXX.XXX`
   - 📋 Save this - you'll need it constantly!

---

## **PART 3: ADD MANAGED DATABASES** (10 minutes)

### **Step 3.1: Create PostgreSQL Database**

1. **Click:** "Create" → "Databases"

2. **Choose database engine:**
   - **PostgreSQL** version 15

3. **Choose cluster configuration:**
   ```
   Node Plan: Basic
   Node: 1GB RAM / 1 vCPU / 10GB Disk
   Price: $15/month
   ```

4. **Choose region:**
   - **SAME region as your Droplet!**

5. **Choose VPC Network:**
   - Default VPC

6. **Database cluster name:**
   ```
   crypto-postgres-db
   ```

7. **Click:** "Create Database Cluster"

8. **Wait 3-5 minutes** for provisioning

9. **When ready:**
   - **Copy the connection string**
   - Format: `postgresql://username:password@host:port/database?sslmode=require`
   - 📋 Save this!

---

### **Step 3.2: Create Redis Database**

1. **Click:** "Create" → "Databases"

2. **Choose database engine:**
   - **Redis** version 7

3. **Choose cluster configuration:**
   ```
   Node Plan: Basic
   Node: 1GB RAM
   Price: $15/month
   ```

4. **Choose region:**
   - **SAME region as your Droplet!**

5. **Database cluster name:**
   ```
   crypto-redis-cache
   ```

6. **Click:** "Create Database Cluster"

7. **Wait 3-5 minutes**

8. **When ready:**
   - **Copy the connection string**
   - Format: `rediss://username:password@host:port`
   - 📋 Save this!

---

## **PART 4: CONNECT TO DROPLET** (5 minutes)

### **Step 4.1: SSH into Droplet**

**If using SSH Key:**
```bash
ssh -i ~/.ssh/digitalocean_key root@YOUR_DROPLET_IP
```

**If using Password:**
```bash
ssh root@YOUR_DROPLET_IP
# Enter password from email
```

Replace `YOUR_DROPLET_IP` with IP from Step 2.5

---

### **Step 4.2: Update System**

```bash
# Update package list
apt update

# Upgrade packages (takes 2-3 minutes)
apt upgrade -y

# Install useful tools
apt install -y curl git nano
```

---

### **Step 4.3: Verify Docker**

If you chose "Docker on Ubuntu" marketplace image:

```bash
# Check Docker version
docker --version
docker-compose --version

# Should see:
# Docker version 24.x.x
# docker-compose version 1.29.x or 2.x.x
```

If Docker NOT installed (you chose regular Ubuntu):

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install -y docker-compose

# Verify
docker --version
docker-compose --version
```

---

## **PART 5: DEPLOY YOUR APP** (15 minutes)

### **Step 5.1: Clone Repository**

```bash
# Clone your repo
git clone https://github.com/Austen0305/CryptoOrchestrator.git

# Navigate to project
cd CryptoOrchestrator

# Verify files
ls -la
```

---

### **Step 5.2: Create Environment File**

```bash
# Copy example
cp .env.example .env

# Edit with nano
nano .env
```

**Set these variables:**

```bash
# Database (use connection string from Step 3.1)
DATABASE_URL=postgresql://username:password@host:port/defaultdb?sslmode=require

# Redis (use connection string from Step 3.2)
REDIS_URL=rediss://username:password@host:port

# Security - Generate new ones!
JWT_SECRET=your_jwt_secret_here_make_it_long_and_random
EXCHANGE_KEY_ENCRYPTION_KEY=your_encryption_key_base64_encoded

# API URLs (use your Droplet IP)
VITE_API_URL=http://YOUR_DROPLET_IP
VITE_WS_URL=ws://YOUR_DROPLET_IP

# Features
ENABLE_TESTNET=true
ENABLE_REAL_MONEY_TRADING=false

# Environment
NODE_ENV=production
LOG_LEVEL=INFO
```

**To generate secure keys:**

```bash
# Generate JWT secret (in a new terminal on YOUR computer)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate encryption key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

---

### **Step 5.3: Configure Trusted Sources for Databases**

Your managed databases need to allow connections from your Droplet.

**For PostgreSQL:**

1. **Go to DigitalOcean dashboard** → Databases → crypto-postgres-db

2. **Click:** "Settings" tab

3. **Trusted Sources:**
   - Click "Edit"
   - Add your Droplet
   - Select your droplet from list
   - OR add Droplet IP manually
   - Click "Save"

**For Redis:**

1. **Go to DigitalOcean dashboard** → Databases → crypto-redis-cache

2. **Click:** "Settings" tab

3. **Trusted Sources:**
   - Click "Edit"
   - Add your Droplet
   - Click "Save"

---

### **Step 5.4: Deploy with Docker Compose**

```bash
# Make sure you're in project root
cd ~/CryptoOrchestrator

# Start all services
docker-compose up -d

# This will:
# - Build your Docker image (10-15 minutes first time!)
# - Start FastAPI backend
# - Start Celery workers
# - Start React frontend
# - Connect to managed PostgreSQL
# - Connect to managed Redis
```

**Monitor the build:**

```bash
# Watch logs (Ctrl+C to exit)
docker-compose logs -f

# Check status
docker-compose ps
```

---

### **Step 5.5: Run Database Migrations**

```bash
# Wait for backend to be fully up, then run migrations
docker-compose exec backend alembic upgrade head

# Should see:
# INFO  [alembic.runtime.migration] Running upgrade...
```

---

## **PART 6: CONFIGURE FIREWALL** (5 minutes)

### **Step 6.1: Configure UFW (Ubuntu Firewall)**

```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS
ufw allow 443/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

---

### **Step 6.2: Configure DigitalOcean Cloud Firewall (Optional)**

For extra security:

1. **Go to:** Networking → Firewalls

2. **Create Firewall**

3. **Inbound Rules:**
   - SSH: Port 22, All IPv4/IPv6
   - HTTP: Port 80, All IPv4/IPv6
   - HTTPS: Port 443, All IPv4/IPv6

4. **Apply to Droplets:** Select your droplet

5. **Create Firewall**

---

## **PART 7: VERIFY DEPLOYMENT** (5 minutes)

### **Step 7.1: Test Backend**

```bash
# From your Droplet
curl http://localhost:8000/api/health

# Should return:
# {"status":"healthy","database":"connected","redis":"connected"}
```

---

### **Step 7.2: Test from Internet**

**On YOUR computer:**

```bash
curl http://YOUR_DROPLET_IP/api/health
```

Should return same health check.

---

### **Step 7.3: Test Frontend**

1. **Open browser**
2. **Go to:** `http://YOUR_DROPLET_IP`
3. **You should see your CryptoOrchestrator app!** 🎉

---

### **Step 7.4: Test API Docs**

1. **Go to:** `http://YOUR_DROPLET_IP/api/docs`
2. **You should see Swagger UI**

---

## **OPTIONAL: ADD CUSTOM DOMAIN + SSL** (15 minutes)

### **Step 8.1: Point Domain to Droplet**

At your domain registrar:

```
A Record:
  Name: @
  Value: YOUR_DROPLET_IP
  TTL: 300

A Record:
  Name: www
  Value: YOUR_DROPLET_IP
  TTL: 300
```

Wait 5-30 minutes for DNS propagation.

---

### **Step 8.2: Install SSL Certificate**

```bash
# SSH into your Droplet
ssh -i ~/.ssh/digitalocean_key root@YOUR_DROPLET_IP

# Install Certbot
apt install -y certbot python3-certbot-nginx

# Install Nginx
apt install -y nginx

# Configure Nginx for your app
nano /etc/nginx/sites-available/default
```

**Add this configuration:**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Get SSL:**

```bash
# Test Nginx config
nginx -t

# Restart Nginx
systemctl restart nginx

# Get SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Redirect HTTP to HTTPS: Yes

# Your site now has HTTPS! 🔒
```

---

## 🔄 **MAINTENANCE**

### **Update Application:**

```bash
# SSH into Droplet
ssh -i ~/.ssh/digitalocean_key root@YOUR_DROPLET_IP

# Navigate to project
cd ~/CryptoOrchestrator

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations if needed
docker-compose exec backend alembic upgrade head
```

---

### **View Logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

### **Backup Database:**

```bash
# DigitalOcean managed databases auto-backup daily
# Manual backup:
docker-compose exec backend python -c "
from server_fastapi.database import SessionLocal
# Your backup script
"
```

---

### **Monitor Resources:**

```bash
# Check disk space
df -h

# Check memory
free -h

# Check Docker stats
docker stats

# DigitalOcean monitoring (in dashboard)
# Metrics → Select your droplet
```

---

## 💰 **COST TRACKING**

### **Check Your Balance:**

1. **Go to:** Billing → Balance
2. **See:** Remaining credit and usage
3. **Set up:** Billing alerts

### **Your Costs:**

```yaml
During Trial (60 days):
  Droplet (4GB): $36/month × 2 months = $72
  PostgreSQL: $15/month × 2 months = $30
  Redis: $15/month × 2 months = $30
  Total: $132 of your $200 credit
  Remaining: $68 credit

After Trial:
  Monthly: $66
  Annually: $792
  
  OR migrate to free hosting before trial ends!
```

---

## 🆘 **TROUBLESHOOTING**

### **Can't SSH:**

```bash
# Check SSH key permissions
chmod 600 ~/.ssh/digitalocean_key

# Try verbose
ssh -v -i ~/.ssh/digitalocean_key root@YOUR_DROPLET_IP

# Use password if SSH key fails
ssh root@YOUR_DROPLET_IP
```

---

### **Docker build fails (out of memory):**

```bash
# Add swap space
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Verify
free -h

# Try build again
docker-compose up -d --build
```

---

### **Can't connect to database:**

```bash
# Verify trusted sources in DigitalOcean dashboard
# PostgreSQL → Settings → Trusted Sources
# Make sure your Droplet is added

# Test connection
docker-compose exec backend python -c "
from server_fastapi.database import engine
print(engine.connect())
"
```

---

### **Frontend not loading:**

```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs frontend
docker-compose logs backend

# Restart all
docker-compose restart
```

---

## 🎉 **CONGRATULATIONS!**

Your CryptoOrchestrator is now live on DigitalOcean!

```yaml
✅ Full 10GB app deployed
✅ Managed PostgreSQL database
✅ Managed Redis cache
✅ All ML features working
✅ 60 days free ($200 credit)
✅ Simple, clean setup
```

---

## 📚 **NEXT STEPS**

1. **✅ Test all features thoroughly**
2. **✅ Add custom domain + SSL**
3. **✅ Set up monitoring**
4. **✅ Plan for after trial:**
   - Continue at $66/month
   - OR optimize to cheaper tier
   - OR migrate to free hosting (I'll help!)

---

## 🔗 **USEFUL LINKS**

- DigitalOcean Control Panel: https://cloud.digitalocean.com
- Your Droplet: Droplets → cryptoorchestrator-app
- Your Databases: Databases → crypto-postgres-db, crypto-redis-cache
- Documentation: https://docs.digitalocean.com

---

**Your app is live at:** `http://YOUR_DROPLET_IP`  
**API docs at:** `http://YOUR_DROPLET_IP/api/docs`  
**Health check:** `http://YOUR_DROPLET_IP/api/health`

---

**Questions? Issues?** Check troubleshooting section or let me know!

*Guide Version: 1.0*  
*Last Updated: December 26, 2025*  
*Tested: DigitalOcean December 2025*
