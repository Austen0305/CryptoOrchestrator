# Start both Python adapters in separate PowerShell windows for development
# Usage: .\start_adapters.ps1

$python = $env:PYTHON
if (-not $python) { $python = 'python' }

Start-Process -FilePath $python -ArgumentList 'server/integrations/freqtrade_adapter.py' -NoNewWindow
Start-Process -FilePath $python -ArgumentList 'server/integrations/jesse_adapter.py' -NoNewWindow

Write-Host "Started freqtrade_adapter and jesse_adapter (check process list)."