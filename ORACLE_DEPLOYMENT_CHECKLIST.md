# ☁️ **ORACLE CLOUD DEPLOYMENT - QUICK CHECKLIST**

**Complete guide:** `docs/deployment/ORACLE_CLOUD_DEPLOYMENT.md`

---

## ✅ **DEPLOYMENT CHECKLIST**

### **Before You Start** (5 minutes)
- [ ] Oracle Cloud account created (https://www.oracle.com/cloud/free/)
- [ ] GitHub repository accessible
- [ ] 2-3 hours available (one-time setup)

---

### **Part 1: Setup SSH Key** (2 minutes)

**Windows:**
```powershell
ssh-keygen -t rsa -b 4096 -f $HOME\.ssh\oracle_key -N '""'
Get-Content $HOME\.ssh\oracle_key.pub  # Copy this!
```

**Mac/Linux:**
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_key -N ""
cat ~/.ssh/oracle_key.pub  # Copy this!
```

- [ ] SSH key generated
- [ ] Public key copied

---

### **Part 2: Create Backend VM** (15 minutes)

**In Oracle Cloud Console:**
1. [ ] Compute → Instances → Create Instance
2. [ ] Name: `cryptoorchestrator-backend`
3. [ ] Image: Ubuntu 22.04
4. [ ] Shape: VM.Standard.E2.1.Micro (Always Free)
5. [ ] Create VCN: `cryptoorchestrator-vcn`
6. [ ] Assign Public IP: Yes
7. [ ] Paste SSH public key
8. [ ] Create Instance
9. [ ] **Copy Public IP:** `____________________`

**Configure Security (in VCN → Security Lists):**
- [ ] Add Rule: Port 80 (HTTP) - Source: 0.0.0.0/0
- [ ] Add Rule: Port 443 (HTTPS) - Source: 0.0.0.0/0
- [ ] Add Rule: Port 8000 (API) - Source: 0.0.0.0/0

**Setup VM:**
```bash
ssh -i ~/.ssh/oracle_key ubuntu@<BACKEND_IP>
curl -O https://raw.githubusercontent.com/yourusername/CryptoOrchestrator/main/scripts/deploy/setup-oracle-vm.sh
chmod +x setup-oracle-vm.sh
./setup-oracle-vm.sh backend
```

- [ ] Connected via SSH
- [ ] Setup script downloaded
- [ ] Setup script executed
- [ ] .env file updated with secrets
- [ ] Backend running: `curl http://localhost:8000/api/health`
- [ ] Backend accessible: `curl http://<BACKEND_IP>/api/health`

---

### **Part 3: Create Frontend VM** (15 minutes)

**In Oracle Cloud Console:**
1. [ ] Compute → Instances → Create Instance
2. [ ] Name: `cryptoorchestrator-frontend`
3. [ ] Image: Ubuntu 22.04
4. [ ] Shape: VM.Standard.E2.1.Micro (Always Free)
5. [ ] VCN: `cryptoorchestrator-vcn` (same as backend)
6. [ ] Assign Public IP: Yes
7. [ ] Paste SSH public key
8. [ ] Create Instance
9. [ ] **Copy Public IP:** `____________________`

**Setup VM:**
```bash
ssh -i ~/.ssh/oracle_key ubuntu@<FRONTEND_IP>
curl -O https://raw.githubusercontent.com/yourusername/CryptoOrchestrator/main/scripts/deploy/setup-oracle-vm.sh
chmod +x setup-oracle-vm.sh
./setup-oracle-vm.sh frontend
# Enter backend IP when prompted: <BACKEND_IP>
```

- [ ] Connected via SSH
- [ ] Setup script downloaded
- [ ] Setup script executed
- [ ] Backend IP entered
- [ ] Frontend built (takes 3-5 minutes)
- [ ] Frontend accessible: `http://<FRONTEND_IP>`

---

### **Part 4: Configure Firewall** (5 minutes)

**On Both VMs:**
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

- [ ] Firewall configured on backend VM
- [ ] Firewall configured on frontend VM

---

### **Part 5: Test Deployment** (5 minutes)

- [ ] Frontend loads: `http://<FRONTEND_IP>`
- [ ] Can register a user
- [ ] Can login
- [ ] Can create a bot
- [ ] Dashboard shows data
- [ ] No console errors

---

### **Part 6: Optional - SSL Certificate** (10 minutes)

**Prerequisites:**
- [ ] Custom domain (e.g., cryptoorchestrator.com)
- [ ] DNS A records:
  - `@` → `<FRONTEND_IP>`
  - `www` → `<FRONTEND_IP>`
  - `api` → `<BACKEND_IP>`

**On Frontend VM:**
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**On Backend VM:**
```bash
sudo certbot --nginx -d api.yourdomain.com
```

- [ ] SSL certificate installed (frontend)
- [ ] SSL certificate installed (backend)
- [ ] HTTPS works: `https://yourdomain.com`
- [ ] HTTP redirects to HTTPS

---

### **Part 7: Optional - Cloudflare CDN** (10 minutes)

1. [ ] Sign up at https://cloudflare.com (free)
2. [ ] Add your domain
3. [ ] Add DNS records (A records to VM IPs)
4. [ ] Update nameservers at registrar
5. [ ] Configure settings:
   - [ ] SSL/TLS: Full
   - [ ] Always Use HTTPS: On
   - [ ] Auto Minify: On
   - [ ] Brotli: On
6. [ ] Wait for propagation (5-30 minutes)
7. [ ] Test: `https://yourdomain.com`

---

## 🎉 **DEPLOYMENT COMPLETE!**

### **Your Resources:**
- **Frontend:** `http://<FRONTEND_IP>` or `https://yourdomain.com`
- **Backend API:** `http://<BACKEND_IP>/api` or `https://api.yourdomain.com`
- **API Docs:** `http://<BACKEND_IP>/api/docs`

### **Monthly Cost:** **$0** ✅

### **Performance:**
- ✅ No cold starts
- ✅ Always-on VMs
- ✅ 10TB bandwidth/month
- ✅ Full control

---

## 📝 **IMPORTANT IPs** (Write these down!)

```
Backend VM Public IP:  ____________________
Frontend VM Public IP: ____________________

SSH Command (Backend):
ssh -i ~/.ssh/oracle_key ubuntu@____________________

SSH Command (Frontend):
ssh -i ~/.ssh/oracle_key ubuntu@____________________
```

---

## 🔄 **MAINTENANCE COMMANDS**

### Update Application:
```bash
# Backend
ssh -i ~/.ssh/oracle_key ubuntu@<BACKEND_IP>
cd /home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cryptoorchestrator

# Frontend
ssh -i ~/.ssh/oracle_key ubuntu@<FRONTEND_IP>
cd /home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator/client
git pull
npm install --legacy-peer-deps
npm run build
sudo systemctl reload nginx
```

### Monitor Services:
```bash
# Check backend status
sudo systemctl status cryptoorchestrator

# View logs
sudo journalctl -u cryptoorchestrator -f

# Check resources
free -h
df -h
```

---

## 🆘 **TROUBLESHOOTING**

### Backend not responding:
```bash
sudo systemctl restart cryptoorchestrator
sudo journalctl -u cryptoorchestrator -n 100
```

### Frontend not loading:
```bash
sudo systemctl restart nginx
sudo tail -f /var/log/nginx/error.log
```

### Out of memory:
```bash
# Add 1GB swap
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📚 **NEXT STEPS**

1. [ ] Test all features thoroughly
2. [ ] Set up monitoring (optional)
3. [ ] Configure backups
4. [ ] Add Cloudflare for CDN
5. [ ] Setup SSL certificates
6. [ ] Invite users to test

**Happy Trading! 🚀📈💰**

---

**Full Guide:** `docs/deployment/ORACLE_CLOUD_DEPLOYMENT.md`  
**Setup Script:** `scripts/deploy/setup-oracle-vm.sh`  
**Need Help?** Check the troubleshooting section in the full guide.
