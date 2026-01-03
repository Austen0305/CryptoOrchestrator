# PowerShell script to help set Vercel environment variables
# This script provides instructions and can optionally use Vercel CLI

Write-Host "🚀 Vercel Environment Variable Setup" -ForegroundColor Cyan
Write-Host ""

# Check if Vercel CLI is installed
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue

if (-not $vercelInstalled) {
    Write-Host "⚠️  Vercel CLI not found. Installing..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Choose installation method:" -ForegroundColor Yellow
    Write-Host "1. Install via npm (requires Node.js)"
    Write-Host "2. Set manually via Vercel Dashboard"
    Write-Host ""
    $choice = Read-Host "Enter choice (1 or 2)"
    
    if ($choice -eq "1") {
        Write-Host "Installing Vercel CLI..." -ForegroundColor Cyan
        npm install -g vercel
        $vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Vercel Environment Variable Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get backend URL
$backendUrl = Read-Host "Enter your backend URL (e.g., https://api.example.com or https://xxxxx.trycloudflare.com)"
if ([string]::IsNullOrWhiteSpace($backendUrl)) {
    Write-Host "❌ Backend URL is required" -ForegroundColor Red
    exit 1
}

# Remove trailing slash
$backendUrl = $backendUrl.TrimEnd('/')

# Ensure /api suffix
if (-not $backendUrl.EndsWith('/api')) {
    $apiUrl = "$backendUrl/api"
}
else {
    $apiUrl = $backendUrl
}

# Derive WebSocket URL
$wsUrl = $apiUrl -replace '^https://', 'wss://' -replace '^http://', 'ws://' -replace '/api$', ''

Write-Host ""
Write-Host "Environment Variables to Set:" -ForegroundColor Green
Write-Host ""
Write-Host "VITE_API_URL = $apiUrl" -ForegroundColor Yellow
Write-Host "VITE_WS_URL = $wsUrl" -ForegroundColor Yellow
Write-Host ""

if ($vercelInstalled) {
    Write-Host "Vercel CLI detected. Would you like to set these automatically?" -ForegroundColor Cyan
    $autoSet = Read-Host "Set automatically? (Y/n)"
    
    if ($autoSet -ne 'n' -and $autoSet -ne 'N') {
        Write-Host ""
        Write-Host "Setting VITE_API_URL..." -ForegroundColor Cyan
        
        # Check if logged in
        $loggedIn = vercel whoami 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Please login to Vercel first:" -ForegroundColor Yellow
            vercel login
        }
        
        # Set environment variables
        Write-Host "Setting VITE_API_URL..." -ForegroundColor Cyan
        echo $apiUrl | vercel env add VITE_API_URL production preview development
        
        Write-Host "Setting VITE_WS_URL..." -ForegroundColor Cyan
        echo $wsUrl | vercel env add VITE_WS_URL production preview development
        
        Write-Host ""
        Write-Host "✅ Environment variables set!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Redeploy your Vercel project"
        Write-Host "2. Or push a new commit to trigger redeploy"
    }
    else {
        ShowManualInstructions $apiUrl $wsUrl
    }
}
else {
    ShowManualInstructions $apiUrl $wsUrl
}

function ShowManualInstructions {
    param(
        [string]$apiUrl,
        [string]$wsUrl
    )
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Manual Setup Instructions" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Go to Vercel Dashboard:" -ForegroundColor Yellow
    Write-Host "   https://vercel.com/dashboard" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Select your project: CryptoOrchestrator" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Go to Settings → Environment Variables" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. Add these variables:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Variable Name: VITE_API_URL" -ForegroundColor Green
    Write-Host "   Value: $apiUrl" -ForegroundColor White
    Write-Host "   Environment: Production, Preview, Development" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Variable Name: VITE_WS_URL" -ForegroundColor Green
    Write-Host "   Value: $wsUrl" -ForegroundColor White
    Write-Host "   Environment: Production, Preview, Development" -ForegroundColor Gray
    Write-Host ""
    Write-Host "5. Click 'Save' for each variable" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "6. Redeploy your project:" -ForegroundColor Yellow
    Write-Host "   - Go to Deployments tab" -ForegroundColor Gray
    Write-Host "   - Click '...' on latest deployment" -ForegroundColor Gray
    Write-Host "   - Click 'Redeploy'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "✅ Done! Your frontend will use the new backend URL" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
