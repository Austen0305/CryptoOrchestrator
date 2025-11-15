Param(
    [string]$Email = "devuser@example.com",
    [string]$Password = "DevPass123!",
    [string]$Name = "Dev User"
)

Write-Host "[Dev Login] Registering (if new) user $Email" -ForegroundColor Cyan
$registerBody = @{ email = $Email; password = $Password; name = $Name } | ConvertTo-Json
try {
    $reg = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/auth/register" -ContentType "application/json" -Body $registerBody -ErrorAction SilentlyContinue
    if ($reg) { Write-Host "[Dev Login] Registration response:" ($reg | ConvertTo-Json -Depth 5) }
}
catch { Write-Host "[Dev Login] Registration skipped (may already exist)" -ForegroundColor Yellow }

Write-Host "[Dev Login] Logging in user $Email" -ForegroundColor Cyan
$loginBody = @{ email = $Email; password = $Password } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/auth/login" -ContentType "application/json" -Body $loginBody
$token = $login.data.token

if (-not $token) { Write-Error "Login failed; no token returned"; exit 1 }

Set-Content -Path "$PSScriptRoot\dev_token.txt" -Value $token
Write-Host "[Dev Login] Token saved to dev_token.txt" -ForegroundColor Green
Write-Host "[Dev Login] To use in the browser, open DevTools console and run:" -ForegroundColor Green
Write-Host "localStorage.setItem('auth_token', '$token');" -ForegroundColor Yellow
Write-Host "localStorage.setItem('auth_user', JSON.stringify({ email: '$Email', name: '$Name' }));" -ForegroundColor Yellow
Write-Host "Then refresh the page." -ForegroundColor Green
