#!/usr/bin/env python3
"""
Apply compression middleware fix directly to the file
This adds Cloudflare Host header detection
"""

import re
import shutil
from pathlib import Path

file_path = Path("server_fastapi/middleware/compression.py")

if not file_path.exists():
    print(f"❌ File not found: {file_path}")
    exit(1)

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Check if fix is already applied
if 'Also check Host header for Cloudflare tunnel domains' in content:
    print("✅ Fix already applied!")
    exit(0)

# Pattern to find and replace
# We need to find the is_behind_cloudflare assignment and the if statement after it
pattern = r'(is_behind_cloudflare = any\(\s+header in request\.headers for header in cloudflare_headers\s+\))\s+(\n\s+if is_behind_cloudflare:)'

replacement = r'''\1
            
            # Also check Host header for Cloudflare tunnel domains
            if not is_behind_cloudflare:
                host = request.headers.get("host", "").lower()
                is_behind_cloudflare = (
                    "trycloudflare.com" in host or
                    "cloudflare.com" in host or
                    host.endswith(".trycloudflare.com") or
                    host.endswith(".cloudflare.com")
                )
            \2'''

new_content = re.sub(pattern, replacement, content)

if new_content == content:
    print("❌ Could not find the pattern to replace. The file structure might be different.")
    print("Please apply the fix manually. See QUICK_FIX_ON_VM.md")
    exit(1)

# Backup original
backup_path = file_path.with_suffix('.py.backup')
shutil.copy2(file_path, backup_path)
print(f"✅ Backup created: {backup_path}")

# Write fixed version
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Fix applied successfully!")
print(f"✅ File updated: {file_path}")
print("\nNext steps:")
print("  1. Review the changes: git diff server_fastapi/middleware/compression.py")
print("  2. Restart the backend: sudo systemctl restart cryptoorchestrator-backend")
print("  3. Test: curl -v http://localhost:8000/api/status/")
