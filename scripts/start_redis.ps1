"""
Development and Production Scripts
Run: npm run <script>
"""

# scripts/start_redis.ps1
Write-Host "Starting Redis server for Windows..." -ForegroundColor Green

$redisPath = "C:\Program Files\Redis\redis-server.exe"

if (Test-Path $redisPath) {
    & $redisPath
} else {
    Write-Host "Redis not found. Installing via Chocolatey..." -ForegroundColor Yellow
    choco install redis-64 -y
    & "C:\Program Files\Redis\redis-server.exe"
}
