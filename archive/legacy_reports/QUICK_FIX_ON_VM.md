# Quick Fix Instructions for VM

Since the commit hasn't been pushed yet and the systemd service name might be different, here are the steps to fix directly on the VM:

## Option 1: Apply Fix Directly on VM (Fastest)

Since git pull shows "Already up to date", you can apply the fix directly:

```bash
cd ~/CryptoOrchestrator

# Check current compression middleware file
cat server_fastapi/middleware/compression.py | grep -A 10 "is_behind_cloudflare"

# Apply the fix - edit the file to add Host header check
nano server_fastapi/middleware/compression.py
# OR use sed to apply the fix automatically (see below)
```

Or use this automated fix:

```bash
cd ~/CryptoOrchestrator

# Backup the file
cp server_fastapi/middleware/compression.py server_fastapi/middleware/compression.py.backup

# Apply the fix using sed (adds Host header check)
sed -i '/is_behind_cloudflare = any(/a\            \n            # Also check Host header for Cloudflare tunnel domains\n            if not is_behind_cloudflare:\n                host = request.headers.get("host", "").lower()\n                is_behind_cloudflare = (\n                    "trycloudflare.com" in host or\n                    "cloudflare.com" in host or\n                    host.endswith(".trycloudflare.com") or\n                    host.endswith(".cloudflare.com")\n                )' server_fastapi/middleware/compression.py
```

Actually, it's easier to just edit the file manually. Here's what to change:

## Manual Fix Steps

1. **Open the compression middleware file:**
   ```bash
   nano server_fastapi/middleware/compression.py
   ```

2. **Find this section (around line 114-123):**
   ```python
   # Skip compression if behind Cloudflare (Cloudflare handles compression)
   # Check for Cloudflare headers (CF-Ray, CF-Connecting-IP, etc.)
   cloudflare_headers = ["cf-ray", "cf-connecting-ip", "cf-visitor"]
   is_behind_cloudflare = any(
       header in request.headers for header in cloudflare_headers
   )
   
   if is_behind_cloudflare:
   ```

3. **Replace it with:**
   ```python
   # Skip compression if behind Cloudflare (Cloudflare handles compression)
   # Check for Cloudflare headers (CF-Ray, CF-Connecting-IP, etc.)
   cloudflare_headers = ["cf-ray", "cf-connecting-ip", "cf-visitor"]
   is_behind_cloudflare = any(
       header in request.headers for header in cloudflare_headers
   )
   
   # Also check Host header for Cloudflare tunnel domains
   if not is_behind_cloudflare:
       host = request.headers.get("host", "").lower()
       is_behind_cloudflare = (
           "trycloudflare.com" in host or
           "cloudflare.com" in host or
           host.endswith(".trycloudflare.com") or
           host.endswith(".cloudflare.com")
       )
   
   if is_behind_cloudflare:
   ```

4. **Save and exit** (Ctrl+X, then Y, then Enter for nano)

## Check How Backend is Running

First, let's check how the backend is currently running:

```bash
# Check for systemd services
systemctl list-units | grep -i crypto

# Check for running processes
ps aux | grep -E "uvicorn|python.*server_fastapi" | grep -v grep

# Check if there's a service file
ls -la /etc/systemd/system/ | grep -i crypto

# Check if port 8000 is in use
sudo ss -tlnp | grep 8000
```

Common service names to try:
- `cryptoorchestrator-backend.service`
- `cryptoorchestrator.service`
- `crypto-orchestrator-backend.service`

## Restart the Backend

Once you know the service name, restart it:

```bash
# If using systemd (try these service names):
sudo systemctl restart cryptoorchestrator-backend
# OR
sudo systemctl restart cryptoorchestrator-backend.service
# OR if running manually, kill and restart:
pkill -f "uvicorn.*server_fastapi"
cd ~/CryptoOrchestrator
source venv/bin/activate  # if using venv
python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 &
```

## Test the Fix

After restarting:

```bash
# Test health endpoint
curl -v http://localhost:8000/health

# Test status endpoint (should return 200, not 500)
curl -v http://localhost:8000/api/status/

# Check logs for compression errors
tail -50 ~/CryptoOrchestrator/logs/app.log | grep -i compression
```
