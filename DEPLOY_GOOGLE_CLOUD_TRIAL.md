# 🚀 **Deploy to Google Cloud Platform - $300 Free Trial**

**Best For:** ML applications, 90 days of free testing  
**Credits:** $300 (highest among major providers)  
**Duration:** 90 days  
**Your App:** ✅ Can run optimized 2-3GB image  

---

## 📋 **What You Get**

```yaml
Free Trial Credits: $300
Duration: 90 days
Estimated Monthly Cost: ~$80-100
Free Testing Period: ~3 months

What You Can Run:
  - Compute Engine VM: e2-standard-2 (2 vCPU, 8GB RAM)
  - Cloud SQL PostgreSQL: db-n1-standard-1 (1 vCPU, 3.75GB RAM)
  - Cloud Memorystore Redis: 1GB instance
  - Or: Deploy everything on one VM with Docker Compose
```

---

## 🎯 **OPTION 1: Simple Approach - Single VM (Recommended)**

### **Step 1: Sign Up for Google Cloud**

1. Go to: https://cloud.google.com/free
2. Click **"Get started for free"**
3. Sign in with your Google account
4. Enter payment details (⚠️ Required for verification, won't be charged during trial)
5. Accept terms and complete verification
6. You'll receive $300 in credits automatically

**Time:** 5-10 minutes

---

### **Step 2: Create a VM Instance**

1. In Google Cloud Console, go to: **Navigation Menu** → **Compute Engine** → **VM Instances**
2. Click **"Create Instance"**

**Configure the VM:**

```yaml
Name: cryptoorchestrator-vm
Region: us-central1 (lowest cost)
Zone: us-central1-a

Machine Configuration:
  Series: E2
  Machine type: e2-standard-2
    - 2 vCPU
    - 8GB RAM
    - Cost: ~$48/month
    
Boot disk:
  Operating System: Ubuntu
  Version: Ubuntu 22.04 LTS
  Boot disk type: Balanced persistent disk
  Size: 50 GB
  
Firewall:
  ✅ Allow HTTP traffic
  ✅ Allow HTTPS traffic
```

3. Click **"Create"**
4. Wait 1-2 minutes for VM to start

**Time:** 3-5 minutes

---

### **Step 3: Set Up Firewall Rules**

1. Go to: **VPC Network** → **Firewall**
2. Click **"Create Firewall Rule"**

```yaml
Name: allow-crypto-app
Direction: Ingress
Targets: All instances in network
Source IP ranges: 0.0.0.0/0
Protocols and ports:
  ✅ tcp:8000 (FastAPI backend)
  ✅ tcp:80
  ✅ tcp:443
```

3. Click **"Create"**

**Time:** 2 minutes

---

### **Step 4: Connect to VM and Install Docker**

1. Click **"SSH"** button next to your VM in the console
2. A browser terminal will open

Run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in (close SSH, reopen)
exit
```

**Reconnect via SSH after exit**

```bash
# Verify Docker is working
docker --version
docker-compose --version
```

**Time:** 5 minutes

---

### **Step 5: Clone Your Repository**

```bash
# Install git
sudo apt install git -y

# Clone your repo
git clone https://github.com/Austen0305/CryptoOrchestrator.git
cd CryptoOrchestrator
```

**Time:** 2 minutes

---

### **Step 6: Create Environment File**

```bash
# Create .env file
nano .env
```

Paste this configuration (update values):

```bash
# Database
DATABASE_URL=postgresql://cryptouser:your_password_here@localhost:5432/cryptodb
POSTGRES_USER=cryptouser
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=cryptodb

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_secret_key_here_64_chars
JWT_SECRET_KEY=your_jwt_secret_here

# App
ENVIRONMENT=production
ALLOWED_ORIGINS=http://your-frontend.vercel.app,https://your-frontend.vercel.app
BACKEND_URL=http://YOUR_VM_EXTERNAL_IP:8000

# Optional: API Keys
STRIPE_SECRET_KEY=your_stripe_key
TWILIO_ACCOUNT_SID=your_twilio_sid
```

**Generate secure keys:**

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT_SECRET_KEY  
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save and exit: `Ctrl+X`, `Y`, `Enter`

**Time:** 3 minutes

---

### **Step 7: Deploy with Optimized Docker Image**

```bash
# Build optimized image
docker build -f Dockerfile.optimized -t cryptoorchestrator-backend .

# Start services with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or manually start all services:
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=cryptouser \
  -e POSTGRES_PASSWORD=your_password_here \
  -e POSTGRES_DB=cryptodb \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15

# Redis
docker run -d --name redis \
  -v redis_data:/data \
  -p 6379:6379 \
  redis:7-alpine

# Application
docker run -d --name crypto-backend \
  --env-file .env \
  -p 8000:8000 \
  --restart unless-stopped \
  cryptoorchestrator-backend
```

**Time:** 5-10 minutes (image build)

---

### **Step 8: Verify Deployment**

```bash
# Check running containers
docker ps

# Check logs
docker logs crypto-backend

# Test API
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","database":"connected","redis":"connected"}
```

**Get your VM's external IP:**

```bash
# In VM terminal
curl ifconfig.me
```

Or find it in Google Cloud Console under VM Instances.

**Test from your computer:**
```bash
curl http://YOUR_VM_EXTERNAL_IP:8000/health
```

**Time:** 2 minutes

---

### **Step 9: Deploy Frontend to Vercel**

1. Go to: https://vercel.com
2. Import your GitHub repo: `CryptoOrchestrator`
3. Configure build settings:

```yaml
Framework Preset: Vite
Build Command: npm run build
Output Directory: client/dist
Root Directory: client
```

4. Add environment variable:

```
VITE_API_URL=http://YOUR_VM_EXTERNAL_IP:8000
```

5. Click **Deploy**

**Time:** 5 minutes

---

### **Step 10: Update CORS Settings**

SSH back into your VM:

```bash
cd CryptoOrchestrator
nano .env
```

Update `ALLOWED_ORIGINS`:
```
ALLOWED_ORIGINS=https://your-app.vercel.app,http://your-app.vercel.app
```

Restart backend:
```bash
docker restart crypto-backend
```

---

## ✅ **You're Live!**

```yaml
✅ Backend: http://YOUR_VM_EXTERNAL_IP:8000
✅ API Docs: http://YOUR_VM_EXTERNAL_IP:8000/docs
✅ Frontend: https://your-app.vercel.app
✅ Cost: $0 (using $300 trial credits)
✅ Duration: ~3 months free
```

---

## 📊 **Cost Monitoring**

1. Go to: **Billing** → **Reports**
2. View your credit usage
3. Set up budget alerts:
   - **Billing** → **Budgets & Alerts**
   - Set budget: $100/month
   - Alert at: 50%, 90%, 100%

---

## 🔄 **After Trial Ends (90 days)**

```yaml
Option 1: Migrate to Oracle Cloud (forever free)
  - Export your data
  - Follow ORACLE_CLOUD_SETUP_2025.md
  - Import your data
  
Option 2: Continue on GCP (~$80-100/month)
  - Enable billing
  - Continue using same setup
  
Option 3: Migrate to DigitalOcean ($66/month)
  - Simpler pricing
  - Easier management
```

---

## 🛠️ **Useful Commands**

```bash
# View logs
docker logs -f crypto-backend

# Restart application
docker restart crypto-backend

# Update application
cd CryptoOrchestrator
git pull
docker build -f Dockerfile.optimized -t cryptoorchestrator-backend .
docker restart crypto-backend

# Database migrations
docker exec crypto-backend alembic upgrade head

# Backup database
docker exec postgres pg_dump -U cryptouser cryptodb > backup.sql

# Check disk usage
df -h

# Monitor resources
htop  # Install: sudo apt install htop
```

---

## 🚨 **Troubleshooting**

### **Problem: Cannot connect to backend**

```bash
# Check firewall
gcloud compute firewall-rules list

# Check container is running
docker ps

# Check logs
docker logs crypto-backend
```

### **Problem: Out of memory**

```bash
# Check memory
free -h

# Upgrade VM to e2-standard-4 (16GB RAM)
# Stop VM → Edit → Change machine type → Save
```

### **Problem: Docker build fails**

```bash
# Use optimized requirements
docker build -f Dockerfile.optimized \
  --build-arg PIP_NO_CACHE_DIR=1 \
  -t cryptoorchestrator-backend .
```

---

## 📈 **Performance Optimization**

```bash
# Enable Docker BuildKit
export DOCKER_BUILDKIT=1

# Use multi-stage build
docker build -f Dockerfile.optimized -t crypto-backend .

# Prune unused images
docker system prune -a
```

---

## 🎉 **Success Metrics**

After deployment:
- ✅ Backend responds in < 500ms
- ✅ All health checks pass
- ✅ Frontend loads in < 2 seconds
- ✅ Database queries < 100ms
- ✅ 99%+ uptime

---

**Total Setup Time:** 30-45 minutes  
**Monthly Cost (after trial):** ~$80-100  
**Trial Duration:** 90 days ($300 credits)  
**Recommendation:** Test for 3 months, then migrate to Oracle Cloud for free forever

---

*Created: December 26, 2025*  
*Guide Version: 1.0*  
*Status: ✅ Ready to Deploy*
