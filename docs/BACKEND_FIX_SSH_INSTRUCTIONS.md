# Backend Server Fix - Complete SSH Instructions
**Date:** January 5, 2026  
**Issue:** Backend returning 503 Service Unavailable

## Overview
The backend server at `moderator-analyze-thumbs-have.trycloudflare.com` is returning 503 errors, indicating the FastAPI server is either down or not responding correctly.

## Prerequisites
- SSH access to the server
- Server credentials (username, host, port if not default 22)

## Step-by-Step Instructions

### Step 1: Connect via SSH

Open your terminal and connect to the server:

```bash
ssh username@your-server-ip
```

Or if using a specific port:
```bash
ssh -p PORT username@your-server-ip
```

If you're using a Cloudflare Tunnel, you may need to SSH to the machine running the tunnel.

**Common scenarios:**
- If running on a VPS: `ssh root@your-vps-ip`
- If running on local machine with tunnel: Connect to that machine directly
- If using cloud service: Check your cloud provider's SSH instructions

---

### Step 2: Check Current Directory and Navigate to Project

Once connected, check where you are and navigate to the project:

```bash
# Check current directory
pwd

# Navigate to project (adjust path as needed)
cd /path/to/CryptoOrchestrator
# OR
cd ~/CryptoOrchestrator
# OR if in home directory
cd CryptoOrchestrator

# Verify you're in the right place
ls -la
# You should see: server_fastapi/, client/, etc.
```

---

### Step 3: Check if Server is Running

Check if the FastAPI server process is running:

```bash
# Check for Python/FastAPI processes
ps aux | grep uvicorn
ps aux | grep python
ps aux | grep fastapi

# Check for processes on port 8000 (default FastAPI port)
sudo netstat -tlnp | grep 8000
# OR
sudo ss -tlnp | grep 8000
# OR
sudo lsof -i :8000

# Check if running as a service (systemd)
sudo systemctl status cryptoorchestrator
sudo systemctl status fastapi
# OR check all services
sudo systemctl list-units --type=service | grep -i crypto
sudo systemctl list-units --type=service | grep -i fastapi

# Check if using PM2 (Node.js process manager)
pm2 list
pm2 status
```

**What to look for:**
- If you see uvicorn/python processes running → Server might be running but not responding
- If no processes found → Server is not running
- If systemd service exists but shows "failed" → Service needs to be restarted

---

### Step 4: Check Server Logs

View recent logs to identify the issue:

```bash
# If using systemd service
sudo journalctl -u cryptoorchestrator -n 100 --no-pager
sudo journalctl -u fastapi -n 100 --no-pager

# Check general system logs
sudo tail -n 100 /var/log/syslog | grep -i fastapi
sudo tail -n 100 /var/log/syslog | grep -i crypto

# If logs are in project directory
cd server_fastapi
tail -n 100 logs/*.log
# OR
tail -n 100 *.log

# Check application logs (if exists)
cat server_fastapi/logs/app.log | tail -100
```

**What to look for:**
- Database connection errors
- Port already in use errors
- Import/module errors
- Configuration errors

---

### Step 5: Check Python Environment and Dependencies

Verify Python and dependencies are installed:

```bash
# Check Python version (should be 3.12+)
python3 --version
python3.12 --version

# Check if virtual environment exists
ls -la | grep venv
ls -la | grep .venv
ls -la | grep env

# Activate virtual environment if it exists
source venv/bin/activate
# OR
source .venv/bin/activate
# OR
source env/bin/activate

# Check if dependencies are installed
pip list | grep fastapi
pip list | grep uvicorn
pip list | grep sqlalchemy

# Install/update dependencies if needed
cd server_fastapi
pip install -r requirements.txt
```

---

### Step 6: Check Database Connection

Verify database is accessible:

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql
# OR
sudo service postgresql status

# Check database connection (if .env file exists)
cd server_fastapi
cat .env | grep DATABASE_URL

# Test database connection (adjust connection string)
psql $DATABASE_URL -c "SELECT 1;"
```

---

### Step 7: Check Environment Variables

Verify required environment variables are set:

```bash
cd server_fastapi

# Check if .env file exists
ls -la .env

# View environment variables (be careful with secrets)
cat .env
# OR view without secrets
cat .env | grep -v PASSWORD | grep -v SECRET | grep -v KEY

# Check required variables
# DATABASE_URL, REDIS_URL, SECRET_KEY should be set
```

---

### Step 8: Stop Existing Server (if running)

If the server is running but not responding, stop it first:

```bash
# If using systemd
sudo systemctl stop cryptoorchestrator
sudo systemctl stop fastapi

# If using PM2
pm2 stop all
pm2 delete all

# If running directly, kill the process
# Find the process ID from Step 3
sudo kill -9 <PID>
# OR kill all uvicorn processes
sudo pkill -9 uvicorn
sudo pkill -9 python
```

---

### Step 9: Start/Restart the Server

Start the FastAPI server:

#### Option A: Using systemd (if service exists)

```bash
sudo systemctl start cryptoorchestrator
sudo systemctl enable cryptoorchestrator  # Enable on boot
sudo systemctl status cryptoorchestrator  # Check status
```

#### Option B: Manual Start (for testing)

```bash
cd server_fastapi

# Activate virtual environment
source ../venv/bin/activate
# OR activate if venv is in server_fastapi
source venv/bin/activate

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# OR in production mode (no reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Option C: Using PM2 (if installed)

```bash
cd server_fastapi
source ../venv/bin/activate
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name crypto-api
pm2 save
pm2 startup
```

#### Option D: Using screen/tmux (for background)

```bash
# Using screen
screen -S crypto-api
cd server_fastapi
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
# Press Ctrl+A then D to detach

# Using tmux
tmux new -s crypto-api
cd server_fastapi
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
# Press Ctrl+B then D to detach
```

---

### Step 10: Verify Server is Running

Check if server started successfully:

```bash
# Check if process is running
ps aux | grep uvicorn

# Check if port is listening
sudo netstat -tlnp | grep 8000
# OR
curl http://localhost:8000/docs
curl http://localhost:8000/health
curl http://localhost:8000/api/health

# Check server response
curl -v http://localhost:8000

# Check logs in real-time
sudo journalctl -u cryptoorchestrator -f
# OR if running manually, check terminal output
```

---

### Step 11: Check Cloudflare Tunnel Status

If using Cloudflare Tunnel, verify it's running:

```bash
# Check if cloudflared is running
ps aux | grep cloudflared

# Check cloudflare tunnel status
cloudflared tunnel list
cloudflared tunnel info <tunnel-name>

# Restart tunnel if needed
cloudflared tunnel run <tunnel-name>
# OR if using systemd
sudo systemctl status cloudflared
sudo systemctl restart cloudflared
```

---

### Step 12: Test from Browser

Once server is running, test the endpoints:

```bash
# From server, test locally
curl http://localhost:8000/api/health
curl http://localhost:8000/api/auth/register -X POST -H "Content-Type: application/json" -d '{"email":"test@example.com","username":"test","password":"Test12345678!"}'

# Check if accessible via Cloudflare tunnel URL
curl https://moderator-analyze-thumbs-have.trycloudflare.com/api/health
```

---

## Common Issues and Solutions

### Issue 1: Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000
# Kill the process
sudo kill -9 <PID>
# OR use a different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Issue 2: Database Connection Failed

```bash
# Check PostgreSQL is running
sudo systemctl start postgresql
# Check connection string in .env
# Test connection
psql $DATABASE_URL
```

### Issue 3: Missing Dependencies

```bash
cd server_fastapi
source ../venv/bin/activate
pip install -r requirements.txt
```

### Issue 4: Permission Denied

```bash
# Fix permissions
sudo chown -R $USER:$USER /path/to/CryptoOrchestrator
chmod +x server_fastapi/main.py
```

### Issue 5: Python Version Mismatch

```bash
# Install Python 3.12 if needed
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
# Create new venv with Python 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Restart Script

Create a quick restart script:

```bash
cd server_fastapi
cat > restart.sh << 'EOF'
#!/bin/bash
echo "Stopping server..."
pkill -9 uvicorn
sleep 2
echo "Starting server..."
source ../venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
echo "Server started. PID: $!"
tail -f server.log
EOF

chmod +x restart.sh
```

---

## Monitoring Commands

Keep these running to monitor the server:

```bash
# Watch logs in real-time
tail -f server_fastapi/server.log
# OR
sudo journalctl -u cryptoorchestrator -f

# Monitor process
watch -n 1 'ps aux | grep uvicorn'

# Monitor port
watch -n 1 'netstat -tlnp | grep 8000'

# Monitor system resources
htop
# OR
top
```

---

## Next Steps After Server is Running

1. Verify server responds: `curl http://localhost:8000/api/health`
2. Test registration endpoint: Use the frontend or curl
3. Check Cloudflare tunnel is forwarding correctly
4. Monitor logs for any errors
5. Set up proper service management (systemd/PM2) for production

---

## Need Help?

If you encounter issues:
1. Check the logs (Step 4)
2. Verify environment variables (Step 7)
3. Test database connection (Step 6)
4. Check Python version and dependencies (Step 5)

Copy the error messages and we can troubleshoot further!
