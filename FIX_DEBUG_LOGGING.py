#!/usr/bin/env python3
# Fix the debug logging that was incorrectly inserted

import re

file_path = 'server_fastapi/middleware/compression.py'

with open(file_path, 'r') as f:
    content = f.read()

# Find and fix the broken line - it should be before the try block, not in the comment
# Look for the broken pattern and fix it
pattern = r'logger\.info\(f"DEBUG: Checking Cloudflare.*?\)\s*\(Cloudflare handles compression\)'
replacement = '# Skip compression if behind Cloudflare (Cloudflare handles compression)'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Now add debug logging in the right place - inside the try block, right after the try:
pattern2 = r'(try:\s+# Skip compression if behind Cloudflare)'
replacement2 = r'''try:
            # Skip compression if behind Cloudflare (Cloudflare handles compression)
            logger.info(f"DEBUG: Checking Cloudflare - Host: {request.headers.get('host', 'NOT SET')}, CF-Ray: {request.headers.get('cf-ray', 'NOT SET')}")'''

new_content = re.sub(pattern2, replacement2, new_content)

if new_content != content:
    # Backup
    import shutil
    shutil.copy2(file_path, file_path + '.backup2')
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("✅ Fixed debug logging")
else:
    print("⚠️ Pattern not found - file might already be fixed or structure is different")
