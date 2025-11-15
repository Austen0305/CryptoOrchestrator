# Start Celery worker for Windows
Write-Host "Starting Celery worker..." -ForegroundColor Green

$rootPath = Split-Path -Parent $PSScriptRoot

Set-Location $rootPath

celery -A server_fastapi.celery_app worker `
  --loglevel=info `
  --concurrency=4 `
  --max-tasks-per-child=1000 `
  --logfile=logs\celery.log `
  --pool=solo

Write-Host "Celery worker stopped" -ForegroundColor Yellow
