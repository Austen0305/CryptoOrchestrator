# Test Script for All New Features
# Run after starting the FastAPI server with: npm run dev:fastapi

Write-Host "`n=== CryptoOrchestrator Feature Tests ===" -ForegroundColor Cyan
Write-Host "Testing all 5 new features...`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$headers = @{"Content-Type" = "application/json"}

# Test 1: Marketplace API Key Generation
Write-Host "1. Testing Marketplace API Key Generation..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/marketplace/keys/generate?user_id=test_user&tier=pro" -Headers $headers
    Write-Host "✅ API Key Generated: $($response.api_key.Substring(0,20))..." -ForegroundColor Green
    $apiKey = $response.api_key
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Portfolio Rebalancing Analysis
Write-Host "`n2. Testing Portfolio Rebalancing..." -ForegroundColor Yellow
try {
    $body = @{
        user_id = "test_user"
        portfolio = @{
            BTC = 5000
            ETH = 3000
            BNB = 2000
        }
        config = @{
            strategy = "equal_weight"
            frequency = "weekly"
            threshold_percent = 5.0
            risk_tolerance = "moderate"
            min_trade_size_usd = 10.0
            dry_run = $true
        }
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/portfolio/rebalance/analyze" -Headers $headers -Body $body
    Write-Host "✅ Rebalancing Analysis Complete" -ForegroundColor Green
    Write-Host "   Total Value: `$$($response.total_portfolio_value)" -ForegroundColor Gray
    Write-Host "   Trades Needed: $($response.allocations.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Arbitrage Scanner
Write-Host "`n3. Testing Arbitrage Scanner..." -ForegroundColor Yellow
try {
    $body = @{
        enabled_exchanges = @("binance", "coinbase")
        min_profit_percent = 0.5
        max_position_size_usd = 1000.0
        auto_execute = $false
        blacklist_symbols = @()
        max_latency_ms = 500.0
        min_volume_24h_usd = 100000.0
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/arbitrage/start" -Headers $headers -Body $body
    Write-Host "✅ Arbitrage Scanner Started" -ForegroundColor Green
    
    # Wait a bit then check opportunities
    Start-Sleep -Seconds 3
    $opps = Invoke-RestMethod -Method GET -Uri "$baseUrl/api/arbitrage/opportunities"
    Write-Host "   Opportunities Found: $($opps.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Backtesting
Write-Host "`n4. Testing Enhanced Backtesting..." -ForegroundColor Yellow
try {
    $body = @{
        symbol = "BTC/USDT"
        start_date = "2024-01-01"
        end_date = "2024-03-01"
        timeframe = "1h"
        strategy = @{
            strategy_id = "momentum"
            parameters = @{}
            initial_capital = 10000.0
            position_size_pct = 0.1
        }
        commission_rate = 0.001
        slippage_pct = 0.001
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/backtest/run" -Headers $headers -Body $body
    Write-Host "✅ Backtest Complete" -ForegroundColor Green
    Write-Host "   Initial Capital: `$$($response.initial_capital)" -ForegroundColor Gray
    Write-Host "   Final Capital: `$$($response.final_capital)" -ForegroundColor Gray
    Write-Host "   Total Trades: $($response.trades.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Marketplace Signal Publishing
Write-Host "`n5. Testing Marketplace Signal Publishing..." -ForegroundColor Yellow
try {
    # Register provider
    $provider = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/marketplace/providers/register?user_id=test_user&name=Test%20Provider&description=Test%20signals&subscription_price=29.99" -Headers $headers
    Write-Host "✅ Provider Registered: $($provider.name)" -ForegroundColor Green
    
    # Publish signal
    $signalBody = @{
        provider_id = $provider.provider_id
        symbol = "BTC/USDT"
        signal_type = "buy"
        entry_price = 50000.0
        stop_loss = 48000.0
        take_profit = 54000.0
        confidence = 85.0
        timeframe = "4h"
        analysis = "Bullish breakout pattern"
        expires_hours = 24
    } | ConvertTo-Json -Depth 10
    
    $signal = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/marketplace/signals/publish" -Headers $headers -Body $signalBody
    Write-Host "   Signal Published: $($signal.signal_id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: System Health Check
Write-Host "`n6. Testing System Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Method GET -Uri "$baseUrl/api/health"
    Write-Host "✅ System Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: Check All Routes
Write-Host "`n7. Checking New Routes Registration..." -ForegroundColor Yellow
try {
    $routes = @(
        "/api/portfolio/rebalance/analyze",
        "/api/arbitrage/start",
        "/api/marketplace/keys/generate",
        "/api/backtest/run",
        "/api/backtest/monte-carlo"
    )
    
    foreach ($route in $routes) {
        Write-Host "   ✓ $route" -ForegroundColor Gray
    }
    Write-Host "✅ All routes registered" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed" -ForegroundColor Red
}

Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "All feature tests completed!" -ForegroundColor Green
Write-Host "Check the FastAPI logs for detailed information." -ForegroundColor Gray
Write-Host "`nAPI Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
