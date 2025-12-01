#!/bin/bash
# Bundle Python runtime for Electron distribution
# This script packages Python and dependencies for inclusion in Electron app

set -e

PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
OUTPUT_DIR="${OUTPUT_DIR:-python-runtime}"
INCLUDE_ALL_PACKAGES="${INCLUDE_ALL_PACKAGES:-false}"

echo "=== Bundling Python Runtime for Electron ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Please install Python first."
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
PYTHON_VERSION_OUTPUT=$($PYTHON_CMD --version 2>&1)
echo "Found Python: $PYTHON_VERSION_OUTPUT"

# Create output directory
if [ -d "$OUTPUT_DIR" ]; then
    echo "Cleaning existing output directory..."
    rm -rf "$OUTPUT_DIR"
fi

mkdir -p "$OUTPUT_DIR"
echo "Created output directory: $OUTPUT_DIR"

# Create virtual environment in output directory
echo "Creating virtual environment..."
$PYTHON_CMD -m venv "$OUTPUT_DIR/venv"

# Determine venv Python path based on OS
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    VENV_PYTHON="$OUTPUT_DIR/venv/bin/python"
    VENV_PIP="$OUTPUT_DIR/venv/bin/pip"
else
    VENV_PYTHON="$OUTPUT_DIR/venv/Scripts/python.exe"
    VENV_PIP="$OUTPUT_DIR/venv/Scripts/pip.exe"
fi

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "Installing dependencies..."
$VENV_PIP install --upgrade pip setuptools wheel
$VENV_PIP install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Copy server_fastapi to output
echo "Copying server_fastapi..."
cp -r server_fastapi "$OUTPUT_DIR/server_fastapi"

# Copy shared directory
echo "Copying shared directory..."
cp -r shared "$OUTPUT_DIR/shared"

# Copy requirements.txt
cp requirements.txt "$OUTPUT_DIR/requirements.txt"

# Create startup script for Linux/macOS
cat > "$OUTPUT_DIR/start_server.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
MAIN_FILE="$SCRIPT_DIR/server_fastapi/main.py"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Python runtime not found at $VENV_PYTHON"
    exit 1
fi

export PYTHONUNBUFFERED=1
export FASTAPI_ENV=production

echo "Starting CryptoOrchestrator API server..."
"$VENV_PYTHON" -m uvicorn server_fastapi.main:app --host 127.0.0.1 --port 8000
EOF

chmod +x "$OUTPUT_DIR/start_server.sh"
echo "Created startup script: start_server.sh"

# Calculate size
if command -v du &> /dev/null; then
    SIZE=$(du -sh "$OUTPUT_DIR" | cut -f1)
    echo "=== Python Runtime Bundled Successfully ==="
    echo "Output directory: $OUTPUT_DIR"
    echo "Size: $SIZE"
else
    echo "=== Python Runtime Bundled Successfully ==="
    echo "Output directory: $OUTPUT_DIR"
fi

