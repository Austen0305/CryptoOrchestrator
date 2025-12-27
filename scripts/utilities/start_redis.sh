#!/bin/bash
# Start Redis server for development

echo "Starting Redis server..."

if command -v redis-server &> /dev/null; then
    redis-server --daemonize yes
    echo "Redis started successfully"
else
    echo "Redis not installed. Install with:"
    echo "  Mac: brew install redis"
    echo "  Linux: sudo apt-get install redis-server"
    exit 1
fi
