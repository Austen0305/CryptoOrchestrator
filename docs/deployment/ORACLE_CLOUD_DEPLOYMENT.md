# ☁️ **ORACLE CLOUD ALWAYS FREE DEPLOYMENT**

**Deploy CryptoOrchestrator for $0/month with Best Performance**

---

## 🎯 **WHAT YOU GET**

Oracle Cloud's Always Free tier provides:

- ✅ **2x VM Instances** (1 OCPU + 1GB RAM each, Always Free)
- ✅ **100GB Block Storage** (Always Free)
- ✅ **10TB Bandwidth/Month** (Always Free)
- ✅ **Load Balancer** (Always Free)
- ✅ **No Cold Starts** (always-on VMs)
- ✅ **Excellent Performance**
- ✅ **Never Expires** (truly "Always Free")

**Cost:** **$0/month forever** ✅

---

## 📋 **PREREQUISITES**

### What You Need:
- Oracle Cloud account (free to create)
- SSH key pair (we'll generate if needed)
- GitHub repository with your code
- 2-3 hours for setup (one-time)

### What You'll Deploy:
```
VM #1 (Backend):
  - FastAPI backend (Uvicorn)
  - PostgreSQL database
  - Redis cache
  - Nginx reverse proxy

VM #2 (Frontend):
  - React frontend (built)
  - Nginx web server
  - Reverse proxy to backend
```

---

## 🚀 **STEP-BY-STEP DEPLOYMENT**

### **Step 1: Create Oracle Cloud Account** (5 minutes)

1. Go to https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in your details:
   - Email address
   - Country/Region
   - Cloud Account Name
4. Verify your email
5. Complete account setup

**Note:** Some regions may require credit card verification, but Always Free resources **never charge**.

---

### **Step 2: Create SSH Key Pair** (2 minutes)

#### On Windows (PowerShell):
```powershell
# Create .ssh directory
New-Item -ItemType Directory -Force -Path $HOME\.ssh

# Generate key pair
ssh-keygen -t rsa -b 4096 -f $HOME\.ssh\oracle_key -N '""'

# Key files created:
# - $HOME\.ssh\oracle_key (private key)
# - $HOME\.ssh\oracle_key.pub (public key)
```

#### On Mac/Linux:
```bash
# Create .ssh directory
mkdir -p ~/.ssh

# Generate key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_key -N ""

# Key files created:
# - ~/.ssh/oracle_key (private key)
# - ~/.ssh/oracle_key.pub (public key)
```

**Copy your public key:**
```bash
# Windows
Get-Content $HOME\.ssh\oracle_key.pub

# Mac/Linux
cat ~/.ssh/oracle_key.pub
```

Keep this public key handy - you'll need it soon!

---

### **Step 3: Create Backend VM** (10 minutes)

1. **Login to Oracle Cloud Console**
   - Go to https://cloud.oracle.com
   - Sign in with your account

2. **Open Compute Instances**
   - Click hamburger menu (☰) → Compute → Instances

3. **Create Instance**
   - Click "Create Instance"

4. **Configure Instance:**

   **Name:** `cryptoorchestrator-backend`

   **Placement:**
   - Availability Domain: (any available)

   **Image:**
   - Click "Change Image"
   - Select "Canonical Ubuntu" → "22.04"
   - Click "Select Image"

   **Shape:**
   - Click "Change Shape"
   - Select "VM.Standard.E2.1.Micro" (Always Free)
   - 1 OCPU, 1 GB RAM
   - Click "Select Shape"

   **Networking:**
   - Create new Virtual Cloud Network: `cryptoorchestrator-vcn`
   - Create new Subnet: `public-subnet`
   - Assign public IP: **Yes**

   **Add SSH Keys:**
   - Paste your public key from Step 2

   **Boot Volume:**
   - Default (50 GB) - Always Free

5. **Click "Create"**

6. **Wait for Provisioning** (2-3 minutes)
   - Status will change: Provisioning → Running

7. **Note the Public IP Address**
   - Copy the "Public IP Address" - you'll need it!

---

### **Step 4: Configure Backend VM Security** (5 minutes)

We need to open ports 80 (HTTP) and 443 (HTTPS).

1. **In Oracle Cloud Console:**
   - Go to: Compute → Instances → cryptoorchestrator-backend
   - Click on the VCN name: `cryptoorchestrator-vcn`

2. **Open Security Lists:**
   - Click "Security Lists" in left menu
   - Click "Default Security List for cryptoorchestrator-vcn"

3. **Add Ingress Rules:**
   Click "Add Ingress Rules" and add these 3 rules:

   **Rule 1: HTTP**
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: `TCP`
   - Destination Port Range: `80`
   - Description: `HTTP`
   - Click "Add Ingress Rules"

   **Rule 2: HTTPS**
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: `TCP`
   - Destination Port Range: `443`
   - Description: `HTTPS`
   - Click "Add Ingress Rules"

   **Rule 3: API (Optional, for testing)**
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: `TCP`
   - Destination Port Range: `8000`
   - Description: `FastAPI`
   - Click "Add Ingress Rules"

---

### **Step 5: Setup Backend VM** (15 minutes)

1. **Connect via SSH:**

   **Windows (PowerShell):**
   ```powershell
   ssh -i $HOME\.ssh\oracle_key ubuntu@<BACKEND_PUBLIC_IP>
   ```

   **Mac/Linux:**
   ```bash
   ssh -i ~/.ssh/oracle_key ubuntu@<BACKEND_PUBLIC_IP>
   ```

   Replace `<BACKEND_PUBLIC_IP>` with the IP from Step 3.

2. **Download Setup Script:**
   ```bash
   curl -O https://raw.githubusercontent.com/yourusername/CryptoOrchestrator/main/scripts/deploy/setup-oracle-vm.sh
   chmod +x setup-oracle-vm.sh
   ```

   **Or create it manually:**
   ```bash
   nano setup-oracle-vm.sh
   # Paste the script content from your repository
   # Save: Ctrl+X, Y, Enter
   chmod +x setup-oracle-vm.sh
   ```

3. **Run Setup Script:**
   ```bash
   ./setup-oracle-vm.sh backend
   ```

   The script will:
   - ✅ Update system packages
   - ✅ Install Python 3.12
   - ✅ Install PostgreSQL
   - ✅ Install Redis
   - ✅ Install Nginx
   - ✅ Clone your repository
   - ✅ Setup Python environment
   - ✅ Create systemd service
   - ✅ Configure Nginx reverse proxy

4. **Follow Prompts:**
   - Enter your GitHub repository URL when asked
   - Update `.env` file with generated secrets
   - Press ENTER to continue

5. **Verify Backend is Running:**
   ```bash
   # Check service status
   sudo systemctl status cryptoorchestrator

   # Check logs
   sudo journalctl -u cryptoorchestrator -f

   # Test API
   curl http://localhost:8000/api/health
   ```

   You should see: `{"status":"healthy",...}`

6. **Test from Outside:**
   ```bash
   curl http://<BACKEND_PUBLIC_IP>/api/health
   ```

---

### **Step 6: Create Frontend VM** (10 minutes)

1. **In Oracle Cloud Console:**
   - Go to: Compute → Instances
   - Click "Create Instance"

2. **Configure Instance:**
   - **Name:** `cryptoorchestrator-frontend`
   - **Image:** Canonical Ubuntu 22.04
   - **Shape:** VM.Standard.E2.1.Micro (Always Free)
   - **VCN:** Select `cryptoorchestrator-vcn` (same VCN as backend)
   - **Subnet:** Select `public-subnet`
   - **Public IP:** Yes
   - **SSH Key:** Paste your public key

3. **Click "Create"**

4. **Note the Public IP Address**

---

### **Step 7: Setup Frontend VM** (15 minutes)

1. **Connect via SSH:**
   ```bash
   ssh -i ~/.ssh/oracle_key ubuntu@<FRONTEND_PUBLIC_IP>
   ```

2. **Download Setup Script:**
   ```bash
   curl -O https://raw.githubusercontent.com/yourusername/CryptoOrchestrator/main/scripts/deploy/setup-oracle-vm.sh
   chmod +x setup-oracle-vm.sh
   ```

3. **Run Setup Script:**
   ```bash
   ./setup-oracle-vm.sh frontend
   ```

   The script will:
   - ✅ Install Node.js 20
   - ✅ Install Nginx
   - ✅ Clone repository
   - ✅ Build frontend
   - ✅ Configure Nginx
   - ✅ Proxy API to backend

4. **Enter Backend IP:**
   When prompted, enter your backend VM's public IP from Step 3.

5. **Wait for Build:**
   Frontend build takes 3-5 minutes.

6. **Verify Frontend:**
   Open browser: `http://<FRONTEND_PUBLIC_IP>`

   You should see your CryptoOrchestrator app! 🎉

---

### **Step 8: Configure Firewall (Both VMs)** (5 minutes)

Oracle Linux has a built-in firewall that blocks ports by default.

**On Both VMs (Backend + Frontend):**

```bash
# Allow HTTP
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT

# Allow HTTPS
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# Save rules
sudo netfilter-persistent save
```

**Alternative (simpler but less secure):**
```bash
# Disable firewall (not recommended for production)
sudo systemctl stop iptables
sudo systemctl disable iptables
```

---

### **Step 9: Setup SSL (Optional but Recommended)** (10 minutes)

**Prerequisites:**
- Custom domain pointed to your frontend VM IP
- DNS A records configured

**On Frontend VM:**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Redirect HTTP to HTTPS: Yes

# Test auto-renewal
sudo certbot renew --dry-run
```

**On Backend VM (if using api.yourdomain.com):**

```bash
sudo certbot --nginx -d api.yourdomain.com
```

**Your app now runs on HTTPS!** 🔒

---

### **Step 10: Add Cloudflare CDN (Optional but Recommended)** (10 minutes)

Cloudflare provides free:
- Global CDN
- DDoS protection
- SSL (if you don't have custom domain)
- Caching
- Web Application Firewall

**Setup:**

1. **Sign up at https://cloudflare.com** (free)

2. **Add Your Domain:**
   - Click "Add a site"
   - Enter your domain
   - Choose "Free" plan

3. **Update DNS Records:**
   - Add A record: `@` → `<FRONTEND_PUBLIC_IP>`
   - Add A record: `www` → `<FRONTEND_PUBLIC_IP>`
   - Add A record: `api` → `<BACKEND_PUBLIC_IP>`

4. **Update Nameservers:**
   - Copy Cloudflare nameservers
   - Update at your domain registrar

5. **Configure Settings:**
   - SSL/TLS: Full (or Full Strict if you have SSL)
   - Always Use HTTPS: On
   - Auto Minify: CSS, JS, HTML
   - Brotli: On

6. **Wait for Propagation** (5-30 minutes)

Your site is now behind Cloudflare! 🚀

---

## 🔄 **UPDATE & MAINTENANCE**

### Update Application Code:

**Backend VM:**
```bash
ssh -i ~/.ssh/oracle_key ubuntu@<BACKEND_IP>
cd /home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart cryptoorchestrator
```

**Frontend VM:**
```bash
ssh -i ~/.ssh/oracle_key ubuntu@<FRONTEND_IP>
cd /home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator/client
git pull origin main
npm install --legacy-peer-deps
npm run build
sudo systemctl reload nginx
```

### Monitor Services:

```bash
# Check backend status
sudo systemctl status cryptoorchestrator

# View backend logs
sudo journalctl -u cryptoorchestrator -f

# Check PostgreSQL
sudo systemctl status postgresql

# Check Redis
sudo systemctl status redis-server

# Check Nginx
sudo systemctl status nginx

# Check disk space
df -h

# Check memory
free -h
```

### Backup Database:

```bash
# Create backup
sudo -u postgres pg_dump cryptoorchestrator > backup_$(date +%Y%m%d).sql

# Restore from backup
sudo -u postgres psql cryptoorchestrator < backup_20250101.sql
```

---

## 🆘 **TROUBLESHOOTING**

### Backend not responding:

```bash
# Check if service is running
sudo systemctl status cryptoorchestrator

# Check logs
sudo journalctl -u cryptoorchestrator -n 100

# Restart service
sudo systemctl restart cryptoorchestrator

# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000
```

### Frontend not loading:

```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx config
sudo nginx -t

# View Nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Database connection failed:

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql -c "SELECT version();"

# Reset password if needed
sudo -u postgres psql
ALTER USER cryptouser WITH PASSWORD 'new_password';
\q

# Update .env with new password
nano /home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator/.env
```

### Out of memory:

```bash
# Check memory usage
free -h

# Add swap file (1GB)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Can't connect via SSH:

```bash
# Check security list rules in Oracle Cloud Console
# Ensure port 22 is open for your IP

# Verify SSH key permissions (local machine)
chmod 600 ~/.ssh/oracle_key

# Try verbose SSH for debugging
ssh -v -i ~/.ssh/oracle_key ubuntu@<VM_IP>
```

---

## 📊 **PERFORMANCE TUNING**

### Optimize PostgreSQL:

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/14/main/postgresql.conf

# Recommended settings for 1GB RAM VM:
shared_buffers = 256MB
effective_cache_size = 768MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Optimize Uvicorn Workers:

```bash
# Edit systemd service
sudo nano /etc/systemd/system/cryptoorchestrator.service

# For 1GB RAM, use 2 workers:
ExecStart=.../uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 --workers 2

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart cryptoorchestrator
```

### Enable Nginx Caching:

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/default

# Add caching for static files:
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Reload Nginx
sudo systemctl reload nginx
```

---

## 💰 **COST BREAKDOWN**

| Resource | Oracle Free Tier | Usage | Cost |
|----------|------------------|-------|------|
| VM #1 (Backend) | VM.Standard.E2.1.Micro | Always Free | $0/month |
| VM #2 (Frontend) | VM.Standard.E2.1.Micro | Always Free | $0/month |
| Block Storage | 100GB | Always Free | $0/month |
| Bandwidth | 10TB/month | Always Free | $0/month |
| Load Balancer | 10 Mbps | Always Free | $0/month |
| **TOTAL** | | | **$0/month** ✅ |

**Always Free resources never expire and never charge!**

---

## 🎉 **YOU'RE DONE!**

Your CryptoOrchestrator is now deployed on Oracle Cloud with:

- ✅ **Zero monthly cost** ($0/month forever)
- ✅ **No cold starts** (always-on VMs)
- ✅ **10TB bandwidth/month**
- ✅ **Excellent performance**
- ✅ **Full control** over infrastructure
- ✅ **Production-ready** setup

**Your App:**
- Frontend: `http://<FRONTEND_IP>` (or https://yourdomain.com)
- Backend API: `http://<BACKEND_IP>/api/health`
- API Docs: `http://<BACKEND_IP>/api/docs`

---

## 📚 **NEXT STEPS**

1. **Test Everything:**
   - Register a user
   - Create a bot
   - Test paper trading
   - Test real-time updates

2. **Monitor Performance:**
   - Set up monitoring (optional)
   - Check logs regularly
   - Monitor resource usage

3. **Optimize:**
   - Add more swap if needed
   - Tune PostgreSQL settings
   - Enable Nginx caching

4. **Secure:**
   - Setup SSL (Let's Encrypt)
   - Add Cloudflare CDN
   - Configure firewall rules
   - Regular updates

**Happy Trading! 🚀📈💰**

---

**Need Help?** Check the troubleshooting section or the main deployment guide.
