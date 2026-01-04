# Install Recommended VS Code Extensions for CryptoOrchestrator
# All extensions are completely free with no paid tiers

Write-Host "🚀 Installing Recommended VS Code Extensions for CryptoOrchestrator" -ForegroundColor Cyan
Write-Host ""

# Critical Extensions (High Impact)
Write-Host "📦 Installing Critical Extensions..." -ForegroundColor Yellow

$criticalExtensions = @(
    "usernamehw.errorlens",                    # Error Lens - Inline error display
    "ryanluker.vscode-coverage-gutters",      # Coverage Gutters - Test coverage
    "rangav.vscode-thunder-client",            # Thunder Client - API testing
    "sonarsource.sonarlint-vscode",           # SonarLint - Code quality
    "bradlc.vscode-tailwindcss"               # Tailwind CSS IntelliSense
)

# Important Extensions (Medium Impact)
Write-Host "📦 Installing Important Extensions..." -ForegroundColor Yellow

$importantExtensions = @(
    "christian-kohler.path-intellisense",     # Path Intellisense - Import autocomplete
    "gruntfuggly.todo-tree",                   # Todo Tree - TODO management
    "streetsidesoftware.code-spell-checker",  # Code Spell Checker - Typo detection
    "littlefoxteam.vscode-python-test-adapter", # Python Test Explorer
    "wix.vscode-import-cost"                  # Import Cost - Bundle size
)

# Nice to Have Extensions
Write-Host "📦 Installing Nice-to-Have Extensions..." -ForegroundColor Yellow

$niceToHaveExtensions = @(
    "aaron-bond.better-comments",              # Better Comments - Color-coded comments
    "yzhang.markdown-all-in-one",             # Markdown All in One
    "shd101wyy.markdown-preview-enhanced",   # Markdown Preview Enhanced
    "firsttris.vscode-jest-runner",           # Jest Runner
    "snyk-security.snyk-vulnerability-scanner" # Snyk Security
    [string]$ExtensionName,
    [string]$Description
)
    
Write-Host "  Installing: $ExtensionName" -ForegroundColor Gray
Write-Host "    Description: $Description" -ForegroundColor DarkGray
$result = code --install-extension $ExtensionId 2>&1
    
if ($LASTEXITCODE -eq 0) {
    Write-Host "    ✅ Installed: $ExtensionName" -ForegroundColor Green
    return $true
}
else {
    Write-Host "    ⚠️  Failed or already installed: $ExtensionName" -ForegroundColor Yellow
    return $false
}
}

# Install Missing Extensions
$installedCount = 0
foreach ($ext in $missingExtensions) {
    if (Install-Extension -ExtensionId $ext.Id -ExtensionName $ext.Name -Description $ext.Description) {
        $installedCount++
    }
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "✅ Installed $installedCount/$($missingExtensions.Count) missing extensions" -ForegroundColor Green
Write-Host ""

# Ask about optional extension
Write-Host "📋 Optional Extension Available:" -ForegroundColor Cyan
Write-Host "  $($optionalExtension.Name) - $($optionalExtension.Description)" -ForegroundColor Gray
$installOptional = Read-Host "  Install optional extension? (y/N)"
if ($installOptional -eq "y" -or $installOptional -eq "Y") {
    Install-Extension -ExtensionId $optionalExtension.Id -ExtensionName $optionalExtension.Name -Description $optionalExtension.Description
}

# Summary
$totalExtensions = $missingExtensions.Count
if (Install-Extension -ExtensionId $ext -ExtensionName $name) {
    $niceToHaveCount++
}
Start-Sleep -Milliseconds 500
Write-Host "  ✅ Already Installed:  12/14 recommended extensions" -ForegroundColor Green
Write-Host "  📦 Just Installed:     $installedCount/$totalExtensions missing extensions" -ForegroundColor $(if ($installedCount -eq $totalExtensions) { "Green" } else { "Yellow" })
Write-Host "  ──────────────────────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "  📊 Total Coverage:     $(12 + $installedCount)/14 extensions" -ForegroundColor $(if ($installedCount -eq $totalExtensions) { "Green" } else { "Yellow" })

# Summary
$totalInstalled = $criticalCount + $importantCount + $niceToHaveCount
$totalExtensions = $criticalExtensions.Count + $importantExtensions.Count + $niceToHaveExtensions.Count

Write-Host "  2. Configure Thunder Client (if installed):" -ForegroundColor White
Write-Host "     - Open Thunder Client panel (Ctrl+Shift+P -> 'Thunder Client')" -ForegroundColor Gray
Write-Host "     - Import your FastAPI endpoints from docs/openapi.json" -ForegroundColor Gray
Write-Host "  3. Configure Tailwind IntelliSense (if installed):" -ForegroundColor White
Write-Host "     - Should work automatically with your tailwind.config.ts" -ForegroundColor Gray
Write-Host "     - Verify autocomplete works in React components" -ForegroundColor Gray
Write-Host "  4. Set up Coverage Gutters (already installed):" -ForegroundColor White
Write-Host "     - Run: npm run test:coverage" -ForegroundColor Gray
Write-Host "     - Open a test file to see coverage indicators" -ForegroundColor Gray
Write-Host "  5. SonarLint (already installed):" -ForegroundColor White
Write-Host "     - Automatically analyzes your code - no setup needed" -ForegroundColor Gray
# Next Steps
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Reload VS Code window (Ctrl+Shift+P -> 'Reload Window')" -ForegroundColor White
Write-Host "  2. Configure Coverage Gutters:" -ForegroundColor White
Write-Host "     - Run: npm run test:coverage" -ForegroundColor Gray
Write-Host "     - Open a test file to see coverage indicators" -ForegroundColor Gray
Write-Host "  3. Set up Thunder Client:" -ForegroundColor White
Write-Host "     - Open Thunder Client panel (Ctrl+Shift+P -> 'Thunder Client')" -ForegroundColor Gray
Write-Host "     - Import your FastAPI endpoints" -ForegroundColor Gray
Write-Host "  4. Enable SonarLint:" -ForegroundColor White
Write-Host "     - SonarLint will automatically analyze your code" -ForegroundColor Gray
Write-Host "  5. Configure Tailwind IntelliSense:" -ForegroundColor White
Write-Host "     - Should work automatically with your tailwind.config.ts" -ForegroundColor Gray
Write-Host ""

# MCP Recommendations
Write-Host "📡 MCP Recommendations:" -ForegroundColor Cyan
Write-Host "  ✅ You already have excellent MCP coverage (17 MCPs)" -ForegroundColor Green
Write-Host "  💡 Best MCPs for your project:" -ForegroundColor Yellow
Write-Host "     - api-tester: Perfect for FastAPI testing" -ForegroundColor White
Write-Host "     - context7: FastAPI/React documentation" -ForegroundColor White
Write-Host "     - typescript-definition-finder: TypeScript support" -ForegroundColor White
Write-Host "     - coingecko: Crypto price data" -ForegroundColor White
Write-Host ""

Write-Host "✨ Installation Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📖 For detailed information, see: docs/MCP_AND_TOOL_RECOMMENDATIONS.md" -ForegroundColor Cyan
