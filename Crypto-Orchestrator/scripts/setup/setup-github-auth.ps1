# GitHub Authentication Setup Script
# This script helps set up authentication for private GitHub repositories

Write-Host "=== GitHub Authentication Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is available
$ghAvailable = Get-Command gh -ErrorAction SilentlyContinue
if ($ghAvailable) {
    Write-Host "GitHub CLI detected. Attempting authentication..." -ForegroundColor Yellow
    gh auth status
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Not authenticated. Run: gh auth login" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Option 1: Personal Access Token (PAT) ===" -ForegroundColor Green
Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor White
Write-Host "2. Click 'Generate new token' -> 'Generate new token (classic)'" -ForegroundColor White
Write-Host "3. Name it: 'Crypto-Orchestrator-Access'" -ForegroundColor White
Write-Host "4. Select scope: 'repo' (Full control of private repositories)" -ForegroundColor White
Write-Host "5. Click 'Generate token'" -ForegroundColor White
Write-Host "6. Copy the token (you won't see it again!)" -ForegroundColor Red
Write-Host ""
Write-Host "Then update your remote URL with:" -ForegroundColor Yellow
Write-Host "  git remote set-url origin https://YOUR_TOKEN@github.com/Austen0305/Crypto-Orchestrator.git" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use credential helper (Windows Credential Manager will prompt):" -ForegroundColor Yellow
Write-Host "  git fetch origin" -ForegroundColor Cyan
Write-Host "  (Enter your GitHub username and paste the token as password)" -ForegroundColor White
Write-Host ""

Write-Host "=== Option 2: SSH Key ===" -ForegroundColor Green
Write-Host "1. Generate SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'" -ForegroundColor White
Write-Host "2. Add to GitHub: https://github.com/settings/keys" -ForegroundColor White
Write-Host "3. Update remote: git remote set-url origin git@github.com:Austen0305/Crypto-Orchestrator.git" -ForegroundColor White
Write-Host ""

Write-Host "=== Current Configuration ===" -ForegroundColor Cyan
Write-Host "Remote URL:"
git remote get-url origin
Write-Host ""
Write-Host "Credential Helper:"
git config --global credential.helper
Write-Host ""
