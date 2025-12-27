# 🏆 **ORACLE CLOUD ALWAYS FREE - COMPLETE SETUP GUIDE**
## Deploy Your Full 10GB CryptoOrchestrator for $0 Forever

**Date:** December 26, 2025  
**Time Required:** 60-90 minutes  
**Cost:** $0/month FOREVER  
**Result:** Full app with 24GB RAM, all ML features working

---

## 🎯 **WHAT YOU'LL GET**

### **Oracle Cloud Always Free Tier:**

```yaml
Compute (Choose ONE):
  Option A - ARM Ampere (RECOMMENDED):
    - 4 OCPUs (ARM64 cores)
    - 24GB RAM (!!!)
    - Ampere Altra processors
    - Modern, efficient architecture
  
  Option B - AMD x86:
    - 2 VMs with 1GB RAM each (2GB total)
    - Less powerful
    - Not recommended for 10GB app

Storage:
  - 200GB block storage
  - 10GB object storage (backups)

Networking:
  - 10TB outbound bandwidth/month
  - Public IPv4 + IPv6
  - Free load balancer

Database:
  - 2 Autonomous Databases (20GB each)
  - OR self-install PostgreSQL on compute

Cost: $0/month FOREVER (verified since 2019)
```

---

## ✅ **WHAT WORKS ON ORACLE FREE**

```yaml
Your Full Application:
  ✅ 10GB Docker image (TensorFlow + PyTorch + all ML)
  ✅ FastAPI backend
  ✅ PostgreSQL database
  ✅ Redis cache
  ✅ Celery workers
  ✅ React frontend
  ✅ WebSocket connections
  ✅ ML predictions (TensorFlow/PyTorch)
  ✅ DEX trading
  ✅ All features enabled

Performance:
  - 24GB RAM (handles multiple apps)
  - 4 ARM cores (good performance)
  - 200GB storage (plenty of space)
  - No cold starts (always-on VM)
  - 10TB bandwidth (more than enough)
```

---

## 📋 **PREREQUISITES**

### **What You Need:**

```yaml
Required:
  ✅ Email address
  ✅ Phone number (for verification)
  ⚠️ Credit card (for verification ONLY - never charged)
  ✅ Basic terminal/SSH knowledge
  ✅ 60-90 minutes time

Optional but Recommended:
  ✅ Custom domain (for HTTPS)
  ✅ Cloudflare account (free CDN)
```

### **Credit Card Note:**

```
Oracle requires credit card for account verification.

✅ Verified by millions: Never charges for Always Free resources
✅ Used since 2019 without charges
✅ Documented "Always Free" (not a trial)
⚠️ Only charges if you manually upgrade to paid resources

If you create paid resources by accident, you'll get email warnings.
```

---

## 🚀 **STEP-BY-STEP SETUP**

---

## **PART 1: CREATE ORACLE CLOUD ACCOUNT** (10 minutes)

### **Step 1.1: Sign Up**

1. **Go to:** https://www.oracle.com/cloud/free/

2. **Click:** "Start for free" or "Try Oracle Cloud Free Tier"

3. **Fill in Account Information:**
   ```
   Country/Region: [Your country]
   Email Address: [Your email]
   Name: [Your name]
   Cloud Account Name: [Choose unique name]
   ```
   
   **Cloud Account Name Tips:**
   - Must be unique across all Oracle Cloud
   - 3-30 characters
   - Letters, numbers, hyphens only
   - Example: `cryptoorchestrator-prod`

4. **Choose Home Region:**
   ```
   IMPORTANT: Cannot be changed later!
   
   Recommended Regions:
   - US East (Ashburn) - Good latency for North America
   - US West (Phoenix) - Good for West Coast
   - EU (Frankfurt) - Good for Europe
   - AP (Tokyo) - Good for Asia
   ```

5. **Click "Continue"**

---

### **Step 1.2: Verify Email**

1. **Check your email**
2. **Click verification link**
3. **Return to Oracle Cloud signup**

---

### **Step 1.3: Add Payment Method**

1. **Enter credit card details**
   ```
   Why needed: Account verification only
   What Oracle says: "We will not charge you unless you elect to upgrade"
   Reality: Millions use free tier without charges
   ```

2. **Enter billing address**

3. **Verify your phone number:**
   - Enter phone number
   - Receive SMS verification code
   - Enter code

4. **Accept terms** and click "Complete Sign-Up"

---

### **Step 1.4: Wait for Account Provisioning**

```
Oracle creates your account...
This takes 2-10 minutes.

You'll receive email when ready:
"Your Oracle Cloud account is ready"
```

**☕ Take a break!** Account creation can take up to 10 minutes.

---

### **Step 1.5: First Login**

1. **Go to:** https://cloud.oracle.com

2. **Enter your Cloud Account Name** (from Step 1.1)

3. **Click "Next"**

4. **Enter your email and password**

5. **Click "Sign In"**

6. **You're in the Oracle Cloud Console!** 🎉

---

## **PART 2: CREATE ARM AMPERE INSTANCE** (20 minutes)

### **Step 2.1: Navigate to Compute**

1. **Click hamburger menu** (☰) in top left

2. **Go to:** `Compute` → `Instances`

3. **You'll see "Create Instance" button**

---

### **Step 2.2: Create Instance**

1. **Click "Create Instance"**

2. **Name your instance:**
   ```
   Name: cryptoorchestrator-main
   
   (This will be your main application server)
   ```

3. **Compartment:** Leave as "root" (default)

---

### **Step 2.3: Choose Image**

1. **Click "Edit" next to "Image and shape"**

2. **Click "Change Image"**

3. **Select:**
   ```
   Image: Canonical Ubuntu
   Version: 22.04 (Latest)
   Image build: 2024.xx.xx (most recent)
   ```

4. **Click "Select Image"**

---

### **Step 2.4: Choose Shape (CRITICAL!)**

1. **Click "Change Shape"**

2. **Select "Ampere"** (ARM-based processors)

3. **Choose shape:**
   ```
   Shape: VM.Standard.A1.Flex
   
   Configure:
   - OCPUs: 4 (maximum for free tier)
   - Memory: 24 GB (maximum for free tier)
   
   This uses your ENTIRE Always Free ARM allowance.
   ```

4. **Verify you see:**
   ```
   ✅ "Always Free-eligible"
   ✅ 4 OCPUs
   ✅ 24 GB memory
   ```

5. **Click "Select Shape"**

**⚠️ IMPORTANT:** If you don't see "Always Free-eligible", you selected wrong shape!

---

### **Step 2.5: Configure Networking**

1. **Primary VNIC Information:**
   ```
   Create new VCN: ✅ (checked)
   VCN Name: cryptoorchestrator-vcn
   Subnet Name: public-subnet
   ```

2. **Public IP Address:**
   ```
   ✅ Assign a public IPv4 address (MUST be checked)
   ```

---

### **Step 2.6: Add SSH Keys**

**Option A: Generate New Key (Recommended)**

1. **Open PowerShell/Terminal on YOUR computer**

2. **Run this command:**
   ```powershell
   # Windows PowerShell
   ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\oracle_key" -N '""'
   
   # Mac/Linux
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_key -N ""
   ```

3. **View your public key:**
   ```powershell
   # Windows
   Get-Content "$HOME\.ssh\oracle_key.pub"
   
   # Mac/Linux
   cat ~/.ssh/oracle_key.pub
   ```

4. **Copy the entire output** (starts with `ssh-rsa`)

5. **In Oracle console:**
   - Select "Paste public keys"
   - Paste your public key
   - ✅ Make sure it's one line (no line breaks)

**Option B: Use Existing Key**

1. **If you have an existing SSH key:**
   ```bash
   cat ~/.ssh/id_rsa.pub
   ```

2. **Paste it in Oracle console**

---

### **Step 2.7: Configure Boot Volume**

```yaml
Boot Volume:
  Size: 50 GB (default, Always Free)
  
  ✅ Leave as default
```

---

### **Step 2.8: Create Instance**

1. **Scroll down** and review settings:
   ```
   ✅ Name: cryptoorchestrator-main
   ✅ Shape: VM.Standard.A1.Flex (4 OCPUs, 24 GB)
   ✅ Image: Ubuntu 22.04
   ✅ Always Free: Yes
   ✅ Public IP: Yes
   ✅ SSH Key: Added
   ```

2. **Click "Create"**

3. **Wait for provisioning** (3-5 minutes)
   ```
   Status: Provisioning... → Running
   ```

4. **When status is "Running":**
   - ✅ **Copy the Public IP Address**
   - 📋 Save it somewhere (you'll need it constantly)
   - Example: `129.146.XXX.XXX`

---

## **PART 3: CONFIGURE SECURITY** (10 minutes)

### **Step 3.1: Open Firewall Ports**

We need to allow HTTP (80), HTTPS (443), and SSH (22).

1. **Click on your instance name** (cryptoorchestrator-main)

2. **In "Instance Details", find "Primary VNIC"**

3. **Click on the subnet name** (public-subnet)

4. **Click "Default Security List for cryptoorchestrator-vcn"**

---

### **Step 3.2: Add Ingress Rules**

Click **"Add Ingress Rules"** and add these **one by one:**

**Rule 1: HTTP (Required)**
```yaml
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port Range: 80
Description: HTTP traffic
```
Click "Add Ingress Rules"

**Rule 2: HTTPS (Required)**
```yaml
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port Range: 443
Description: HTTPS traffic
```
Click "Add Ingress Rules"

**Rule 3: API Port (Optional - for testing)**
```yaml
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port Range: 8000
Description: FastAPI direct access
```
Click "Add Ingress Rules"

**Note:** Port 22 (SSH) is already open by default.

---

## **PART 4: INSTALL DOCKER** (15 minutes)

### **Step 4.1: Connect to Your Instance**

1. **Open PowerShell/Terminal on YOUR computer**

2. **Set correct permissions (first time only):**
   ```powershell
   # Windows
   icacls "$HOME\.ssh\oracle_key" /inheritance:r /grant:r "$env:USERNAME:(R)"
   
   # Mac/Linux
   chmod 600 ~/.ssh/oracle_key
   ```

3. **Connect via SSH:**
   ```bash
   ssh -i ~/.ssh/oracle_key ubuntu@YOUR_PUBLIC_IP
   ```
   
   Replace `YOUR_PUBLIC_IP` with IP from Step 2.8

4. **Accept fingerprint:**
   ```
   The authenticity of host... can't be established.
   Are you sure you want to continue connecting (yes/no)? yes
   ```

5. **You're now connected to your Oracle instance!** 🎉

---

### **Step 4.2: Update System**

```bash
# Update package list
sudo apt update

# Upgrade packages (takes 2-3 minutes)
sudo apt upgrade -y
```

---

### **Step 4.3: Install Docker**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Verify installation
docker --version
docker-compose --version
```

**Expected output:**
```
Docker version 24.0.x
docker-compose version 1.29.x
```

---

### **Step 4.4: Restart Session**

```bash
# Exit and reconnect for group changes
exit

# Reconnect
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_PUBLIC_IP

# Test docker without sudo
docker ps
```

Should work without permission errors.

---

## **PART 5: DEPLOY YOUR APPLICATION** (20 minutes)

### **Step 5.1: Clone Your Repository**

```bash
# Install git if needed
sudo apt install -y git

# Clone your repository
git clone https://github.com/Austen0305/CryptoOrchestrator.git
cd CryptoOrchestrator
```

---

### **Step 5.2: Create Environment File**

```bash
# Copy example env file
cp .env.example .env

# Edit with nano
nano .env
```

**Set these critical variables:**

```bash
# Database
DATABASE_URL=postgresql://cryptouser:CHANGE_THIS_PASSWORD@localhost:5432/cryptoorchestrator

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (GENERATE NEW ONES!)
JWT_SECRET=<YOUR_JWT_SECRET_FROM_EARLIER>
EXCHANGE_KEY_ENCRYPTION_KEY=<YOUR_ENCRYPTION_KEY_FROM_EARLIER>

# API URLs
VITE_API_URL=http://YOUR_PUBLIC_IP
VITE_WS_URL=ws://YOUR_PUBLIC_IP

# Features
ENABLE_TESTNET=true
ENABLE_REAL_MONEY_TRADING=false

# Blockchain RPC URLs (Alchemy free tier)
ETHEREUM_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY
# Add your Alchemy keys if you have them, or leave for later
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

---

### **Step 5.3: Deploy with Docker Compose**

```bash
# Make sure you're in the project root
cd ~/CryptoOrchestrator

# Start all services
docker-compose up -d

# This will:
# - Build your 10GB Docker image (10-15 minutes)
# - Start PostgreSQL
# - Start Redis
# - Start FastAPI backend
# - Start Celery workers
# - Start frontend
```

**Wait for build...** This takes 10-15 minutes on first run.

---

### **Step 5.4: Monitor Deployment**

```bash
# Watch logs
docker-compose logs -f

# Check status
docker-compose ps

# You should see:
# - postgres (running)
# - redis (running)
# - backend (running)
# - frontend (running)
# - celery_worker (running)
```

Press `Ctrl+C` to stop watching logs.

---

### **Step 5.5: Run Database Migrations**

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Running upgrade ...
# INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl
```

---

## **PART 6: VERIFY DEPLOYMENT** (5 minutes)

### **Step 6.1: Test Backend**

```bash
# From your Oracle instance
curl http://localhost:8000/api/health

# Should return:
# {"status":"healthy","database":"connected","redis":"connected"}
```

---

### **Step 6.2: Test from Internet**

```bash
# From YOUR computer (not Oracle instance)
curl http://YOUR_PUBLIC_IP/api/health
```

Should return the same health check JSON.

---

### **Step 6.3: Test Frontend**

1. **Open browser on YOUR computer**

2. **Go to:** `http://YOUR_PUBLIC_IP`

3. **You should see your CryptoOrchestrator app!** 🎉

---

### **Step 6.4: Test API Documentation**

1. **Go to:** `http://YOUR_PUBLIC_IP/api/docs`

2. **You should see Swagger UI** with all your endpoints

---

## **PART 7: CONFIGURE FIREWALL (UBUNTU)** (5 minutes)

Oracle Ubuntu instances have a built-in firewall that may block traffic.

```bash
# SSH back into your instance
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_PUBLIC_IP

# Allow HTTP
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT

# Allow HTTPS
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# Allow API (8000)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT

# Save rules
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

**Test again** from your browser: `http://YOUR_PUBLIC_IP`

---

## **OPTIONAL: ADD CUSTOM DOMAIN** (15 minutes)

If you have a domain, point it to your Oracle instance.

### **Step 7.1: Configure DNS**

At your domain registrar (Namecheap, GoDaddy, etc.):

```
A Record:
  Name: @
  Value: YOUR_PUBLIC_IP
  TTL: 300

A Record:
  Name: www
  Value: YOUR_PUBLIC_IP
  TTL: 300

A Record (optional, for API):
  Name: api
  Value: YOUR_PUBLIC_IP
  TTL: 300
```

Wait 5-30 minutes for DNS propagation.

---

### **Step 7.2: Install SSL Certificate (Let's Encrypt)**

```bash
# SSH into your instance
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_PUBLIC_IP

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Redirect HTTP to HTTPS: Yes

# Test auto-renewal
sudo certbot renew --dry-run
```

**Your site now has HTTPS!** 🔒 `https://yourdomain.com`

---

## 🔄 **MAINTENANCE & UPDATES**

### **Update Application:**

```bash
# SSH into instance
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_PUBLIC_IP

# Go to project directory
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
docker-compose logs -f celery_worker
```

---

### **Backup Database:**

```bash
# Create backup
docker-compose exec postgres pg_dump -U cryptouser cryptoorchestrator > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U cryptouser cryptoorchestrator < backup_20250101.sql
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

# Top processes
htop
```

---

## 🆘 **TROUBLESHOOTING**

### **Problem: Can't SSH to instance**

```bash
# Check your SSH key permissions
chmod 600 ~/.ssh/oracle_key

# Try verbose mode
ssh -v -i ~/.ssh/oracle_key ubuntu@YOUR_PUBLIC_IP

# Verify security list has port 22 open
# (Should be open by default)
```

---

### **Problem: Website not loading**

```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs backend
docker-compose logs frontend

# Verify firewall rules
sudo iptables -L INPUT -n --line-numbers

# Test from instance
curl http://localhost:8000/api/health
```

---

### **Problem: Docker build fails (out of memory)**

```bash
# Add swap space (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h

# Try build again
docker-compose up -d --build
```

---

### **Problem: Database connection failed**

```bash
# Check PostgreSQL container
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Verify DATABASE_URL in .env matches docker-compose.yml
```

---

### **Problem: Out of disk space**

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a

# Check logs size
du -sh /var/lib/docker/containers/*
```

---

## 💰 **COST VERIFICATION**

### **Always Free Resources Used:**

```yaml
Compute:
  ✅ VM.Standard.A1.Flex (4 OCPU, 24GB) - Always Free
  
Storage:
  ✅ 50GB boot volume - Always Free (up to 200GB total)

Networking:
  ✅ Public IP - Always Free
  ✅ Data transfer (up to 10TB/month) - Always Free

Total Monthly Cost: $0
```

### **How to Verify No Charges:**

1. **Go to:** Oracle Cloud Console → Billing → Usage Report

2. **Check:** "Always Free" label on all resources

3. **Set up billing alerts:**
   - Billing → Cost Analysis → Create Budget
   - Set budget: $0.01
   - Get email if ANY charges occur

---

## 🎉 **CONGRATULATIONS!**

Your CryptoOrchestrator is now running on Oracle Cloud!

### **What You Have:**

```yaml
✅ Full 10GB application deployed
✅ 24GB RAM (can run multiple apps!)
✅ 4 ARM CPUs (good performance)
✅ 200GB storage available
✅ 10TB bandwidth/month
✅ All ML features working (TensorFlow, PyTorch)
✅ PostgreSQL + Redis + Celery
✅ Cost: $0/month FOREVER
✅ No cold starts (always-on)
```

### **Your URLs:**

```
Frontend: http://YOUR_PUBLIC_IP
Backend API: http://YOUR_PUBLIC_IP/api
API Docs: http://YOUR_PUBLIC_IP/api/docs
Health Check: http://YOUR_PUBLIC_IP/api/health

With domain (if configured):
Frontend: https://yourdomain.com
API: https://api.yourdomain.com
```

---

## 📚 **NEXT STEPS**

1. **✅ Test everything thoroughly**
2. **✅ Set up custom domain + SSL**
3. **✅ Configure Cloudflare CDN (optional)**
4. **✅ Set up monitoring**
5. **✅ Create backup schedule**
6. **✅ Add more security hardening**

---

## 🔗 **USEFUL LINKS**

- Oracle Cloud Console: https://cloud.oracle.com
- Oracle Free Tier FAQ: https://www.oracle.com/cloud/free/faq.html
- Your instance: Oracle Cloud Console → Compute → Instances
- Documentation: `docs/` folder in your repository

---

**You now have enterprise-grade hosting for $0/month!** 🚀💰

**Questions?** Check the troubleshooting section or create an issue on GitHub.

---

*Guide Version: 2.0*  
*Last Updated: December 26, 2025*  
*Tested On: Oracle Cloud Always Free Tier (ARM Ampere)*
