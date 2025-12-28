# Setup Cloudflare Tunnel for HTTPS backend access (Windows version)
# This provides free HTTPS for your backend without needing a domain or SSL certificate

Write-Host "Setting up Cloudflare Tunnel..." -ForegroundColor Cyan

# Check if cloudflared is installed
$cloudflaredPath = Get-Command cloudflared -ErrorAction SilentlyContinue

if (-not $cloudflaredPath) {
    Write-Host "Installing cloudflared..." -ForegroundColor Yellow
    
    # Download cloudflared for Windows
    $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    $installPath = "$env:ProgramFiles\cloudflared\cloudflared.exe"
    
    New-Item -ItemType Directory -Force -Path "$env:ProgramFiles\cloudflared" | Out-Null
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installPath
    
    # Add to PATH
    $env:Path += ";$env:ProgramFiles\cloudflared"
    [Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::Machine)
    
    Write-Host "cloudflared installed successfully" -ForegroundColor Green
} else {
    Write-Host "cloudflared already installed" -ForegroundColor Green
}

# For Windows, we'll run it manually or create a scheduled task
Write-Host ""
Write-Host "To start the tunnel, run:" -ForegroundColor Yellow
Write-Host "cloudflared tunnel --url http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "This will provide a URL like: https://*.trycloudflare.com" -ForegroundColor Cyan
Write-Host "Use that URL for your VITE_API_URL in Vercel" -ForegroundColor Cyan
