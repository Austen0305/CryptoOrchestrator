#!/bin/bash
# Start Celery worker for background tasks

echo "Starting Celery worker..."

cd "$(dirname "$0")/.."

celery -A server_fastapi.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --logfile=logs/celery.log

echo "Celery worker stopped"
