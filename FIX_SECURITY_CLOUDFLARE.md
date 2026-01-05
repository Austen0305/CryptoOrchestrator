# Fix Security Middleware for Cloudflare

The security middleware is blocking Cloudflare tunnel requests. We need to add Cloudflare detection to skip security checks for Cloudflare requests.

Run this on the VM:

```bash
cd ~/CryptoOrchestrator

# Apply the fix to security middleware
python3 << 'PYTHON_FIX'
import re

file_path = 'server_fastapi/middleware/security_advanced.py'

with open(file_path, 'r') as f:
    content = f.read()

# Add Cloudflare detection right after getting client_ip
pattern = r'(# Get client IP\s+client_ip = request\.client\.host if request\.client else "unknown"\s+)# Allow localhost/127.0.0.1 for health checks'
replacement = r'''\1
        # Check if request is coming through Cloudflare tunnel
        cloudflare_headers = ["cf-ray", "cf-connecting-ip", "cf-visitor"]
        is_behind_cloudflare = any(
            header in request.headers for header in cloudflare_headers
        )
        if not is_behind_cloudflare:
            host = request.headers.get("host", "").lower()
            is_behind_cloudflare = (
                "trycloudflare.com" in host or
                "cloudflare.com" in host or
                host.endswith(".trycloudflare.com") or
                host.endswith(".cloudflare.com")
            )
        
        # Skip security checks for Cloudflare tunnel requests
        if is_behind_cloudflare:
            return await call_next(request)
        
        # Allow localhost/127.0.0.1 for health checks'''

new_content = re.sub(pattern, replacement, content)

if new_content != content:
    import shutil
    shutil.copy2(file_path, file_path + '.backup')
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("✅ Security middleware fix applied")
else:
    print("❌ Pattern not found - check the file structure")
PYTHON_FIX

# Check for syntax errors
python3 -m py_compile server_fastapi/middleware/security_advanced.py && echo "✅ Syntax OK" || echo "❌ Syntax error"

# Restart service
sudo systemctl restart cryptoorchestrator-backend
sleep 5

# Test
curl -v https://moderator-analyze-thumbs-have.trycloudflare.com/api/status/
```
