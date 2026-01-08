#!/bin/bash
# Verify the compression middleware fix was applied correctly

echo "🔍 Verifying compression middleware fix..."
echo ""

cd ~/CryptoOrchestrator

# Check if the fix is in the file
if grep -q "Also check Host header for Cloudflare tunnel domains" server_fastapi/middleware/compression.py; then
    echo "✅ Fix code is present in the file"
else
    echo "❌ Fix code NOT found in file!"
    exit 1
fi

# Check the specific code section
echo ""
echo "📋 Relevant code section:"
grep -A 15 "Also check Host header" server_fastapi/middleware/compression.py | head -20

# Check for syntax errors
echo ""
echo "🔍 Checking for Python syntax errors..."
python3 -m py_compile server_fastapi/middleware/compression.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ No syntax errors"
else
    echo "❌ Syntax errors found!"
    exit 1
fi

# Check if the service is using the updated file
echo ""
echo "📋 Checking when the service was last restarted:"
systemctl show cryptoorchestrator-backend --property=ActiveEnterTimestamp

echo ""
echo "📋 Checking file modification time:"
ls -la server_fastapi/middleware/compression.py | awk '{print "File modified: " $6 " " $7 " " $8}'

echo ""
echo "💡 If the file was modified AFTER the service restart, restart the service again:"
echo "   sudo systemctl restart cryptoorchestrator-backend"
