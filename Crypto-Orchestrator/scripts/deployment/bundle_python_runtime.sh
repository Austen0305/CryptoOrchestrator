#!/bin/bash
# Bundle Python Runtime for Electron Desktop App
# Creates a portable Python runtime that can be bundled with the Electron app

set -e

# Configuration
PYTHON_VERSION="3.12"
RUNTIME_DIR="python-runtime"
VENV_DIR="${RUNTIME_DIR}/venv"

# Parse arguments
FORCE=false
if [[ "$1" == "--force" ]] || [[ "$1" == "-f" ]]; then
    FORCE=true
fi

echo "=== Python Runtime Bundling Script ==="
echo ""

# Check if runtime already exists
if [ -d "$RUNTIME_DIR" ]; then
    if [ "$FORCE" = false ]; then
        echo "Python runtime directory already exists: $RUNTIME_DIR"
        echo "Use --force to overwrite"
        exit 0
    else
        echo "Removing existing runtime directory..."
        rm -rf "$RUNTIME_DIR"
    fi
fi

# Check for Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Please install Python $PYTHON_VERSION or later."
    exit 1
fi

PYTHON_VERSION_OUTPUT=$(python3 --version 2>&1)
echo "Found: $PYTHON_VERSION_OUTPUT"

# Create runtime directory
echo "Creating runtime directory: $RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies"
    exit 1
fi

# Copy server_fastapi directory
echo "Copying server_fastapi directory..."
if [ -d "server_fastapi" ]; then
    cp -r server_fastapi "$RUNTIME_DIR/"
else
    echo "Warning: server_fastapi directory not found"
fi

# Copy shared directory
echo "Copying shared directory..."
if [ -d "shared" ]; then
    cp -r shared "$RUNTIME_DIR/"
else
    echo "Warning: shared directory not found"
fi

# Copy requirements.txt
echo "Copying requirements.txt..."
if [ -f "requirements.txt" ]; then
    cp requirements.txt "$RUNTIME_DIR/"
fi

# Create startup script
echo "Creating startup scripts..."

# Unix startup script
cat > "$RUNTIME_DIR/start_server.sh" << 'EOF'
#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_EXE="$VENV_DIR/bin/python"

# Check if Python executable exists
if [ ! -f "$PYTHON_EXE" ]; then
    echo "Python runtime not found in $VENV_DIR"
    exit 1
fi

# Set Python path
export PYTHONPATH="$SCRIPT_DIR"

# Run FastAPI server
"$PYTHON_EXE" -m uvicorn server_fastapi.main:app --host 127.0.0.1 --port 8000
EOF

chmod +x "$RUNTIME_DIR/start_server.sh"

# Create Python version info file
cat > "$RUNTIME_DIR/version.json" << EOF
{
  "python_version": "$PYTHON_VERSION_OUTPUT",
  "bundled_date": "$(date -u +"%Y-%m-%d %H:%M:%S")",
  "platform": "$(uname -s | tr '[:upper:]' '[:lower:]')"
}
EOF

echo ""
echo "=== Python Runtime Bundling Complete ==="
echo "Runtime directory: $RUNTIME_DIR"
echo "Virtual environment: $VENV_DIR"
echo ""
echo "Next steps:"
echo "1. Build Electron app: npm run build:electron"
echo "2. The Python runtime will be bundled automatically"
