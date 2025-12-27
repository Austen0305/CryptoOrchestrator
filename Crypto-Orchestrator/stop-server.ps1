# PowerShell script to stop FastAPI servers on port 8000
Write-Host "Stopping FastAPI servers on port 8000..." -ForegroundColor Yellow

# Get all processes using port 8000
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    $pids = $connections | Select-Object -Unique -ExpandProperty OwningProcess
    
    foreach ($pid in $pids) {
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Stopping process $pid ($($process.ProcessName))..." -ForegroundColor Cyan
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "✓ Process $pid stopped" -ForegroundColor Green
            }
        } catch {
            Write-Host "Could not stop process $pid" -ForegroundColor Red
        }
    }
    
    # Wait a moment for ports to be released
    Start-Sleep -Seconds 2
    
    # Verify port is free
    $stillInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($stillInUse) {
        Write-Host "Warning: Port 8000 is still in use!" -ForegroundColor Red
    } else {
        Write-Host "✓ Port 8000 is now free" -ForegroundColor Green
    }
} else {
    Write-Host "No processes found using port 8000" -ForegroundColor Green
}

Write-Host "`nYou can now restart the server with: npm run dev:fastapi" -ForegroundColor Cyan

