# Prepare Release Script (PowerShell)
# Helper script to prepare a release by running the automation script and creating a tag

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "Error: Invalid version format: $Version" -ForegroundColor Red
    Write-Host "Expected format: MAJOR.MINOR.PATCH (e.g., 1.2.3)" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Preparing release $Version" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Run release automation (dry run first)
Write-Host ""
Write-Host "📋 Running release automation (dry run)..." -ForegroundColor Yellow
python scripts/release_automation.py $Version --dry-run

Write-Host ""
$continue = Read-Host "Review the changes above. Continue with release? (y/N)"
if ($continue -ne 'y' -and $continue -ne 'Y') {
    Write-Host "Release cancelled." -ForegroundColor Yellow
    exit 1
}

# Run release automation for real
Write-Host ""
Write-Host "📝 Running release automation..." -ForegroundColor Yellow
python scripts/release_automation.py $Version

# Show changes
Write-Host ""
Write-Host "📊 Changes made:" -ForegroundColor Cyan
git diff --stat

Write-Host ""
$commit = Read-Host "Review the changes. Commit and create tag? (y/N)"
if ($commit -ne 'y' -and $commit -ne 'Y') {
    Write-Host ""
    Write-Host "Release preparation complete. Commit manually:" -ForegroundColor Yellow
    Write-Host "  git add CHANGELOG.md package.json pyproject.toml" -ForegroundColor Gray
    Write-Host "  git commit -m 'chore(release): bump version to $Version'" -ForegroundColor Gray
    Write-Host "  git tag -a v$Version -m 'Release $Version'" -ForegroundColor Gray
    Write-Host "  git push origin main && git push origin v$Version" -ForegroundColor Gray
    exit 0
}

# Commit changes
Write-Host ""
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git add CHANGELOG.md package.json pyproject.toml
git commit -m "chore(release): bump version to $Version" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "No changes to commit" -ForegroundColor Yellow
}

# Create tag
Write-Host ""
Write-Host "🏷️  Creating tag..." -ForegroundColor Yellow
git tag -a "v$Version" -m "Release $Version"

Write-Host ""
Write-Host "✅ Release $Version prepared!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review the changes: git show HEAD" -ForegroundColor Gray
Write-Host "  2. Push the commit: git push origin main" -ForegroundColor Gray
Write-Host "  3. Push the tag: git push origin v$Version" -ForegroundColor Gray
Write-Host ""
Write-Host "The GitHub Actions workflow will automatically:" -ForegroundColor Cyan
Write-Host "  - Create a GitHub release" -ForegroundColor Gray
Write-Host "  - Build Electron app" -ForegroundColor Gray
Write-Host "  - Upload release assets" -ForegroundColor Gray

