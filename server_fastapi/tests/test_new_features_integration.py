"""
Integration Tests for New Features
Tests portfolio rebalancing, backtesting, marketplace, and arbitrage
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestPortfolioRebalancing:
    """Test portfolio rebalancing functionality"""
    
    def test_analyze_rebalance(self, client):
        """Test portfolio rebalancing analysis"""
        response = client.post(
            "/api/portfolio/rebalance/analyze",
            json={
                "user_id": "test_user",
                "portfolio": {
                    "BTC": 5000,
                    "ETH": 3000,
                    "BNB": 2000
                },
                "config": {
                    "strategy": "equal_weight",
                    "frequency": "weekly",
                    "threshold_percent": 5.0,
                    "risk_tolerance": "moderate",
                    "min_trade_size_usd": 10.0,
                    "dry_run": True
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "rebalance_id" in data
        assert "allocations" in data
        assert data["dry_run"] is True
        assert len(data["allocations"]) == 3
    
    def test_schedule_rebalance(self, client):
        """Test scheduling automatic rebalancing"""
        response = client.post(
            "/api/portfolio/rebalance/schedule",
            json={
                "user_id": "test_user",
                "config": {
                    "strategy": "risk_parity",
                    "frequency": "daily",
                    "threshold_percent": 5.0,
                    "risk_tolerance": "moderate",
                    "min_trade_size_usd": 10.0,
                    "dry_run": False
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["enabled"] is True
        assert "next_run" in data
    
    def test_get_schedules(self, client):
        """Test retrieving user schedules"""
        response = client.get("/api/portfolio/rebalance/schedules/test_user")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestEnhancedBacktesting:
    """Test enhanced backtesting functionality"""
    
    def test_standard_backtest(self, client):
        """Test standard backtest execution"""
        response = client.post(
            "/api/backtest/run",
            json={
                "symbol": "BTC/USDT",
                "start_date": "2024-01-01",
                "end_date": "2024-02-01",
                "timeframe": "1h",
                "strategy": {
                    "strategy_id": "momentum",
                    "parameters": {},
                    "initial_capital": 10000.0,
                    "position_size_pct": 0.1
                },
                "commission_rate": 0.001,
                "slippage_pct": 0.001
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "backtest_id" in data
        assert "metrics" in data
        assert "equity_curve" in data
        assert "trades" in data
    
    def test_monte_carlo_simulation(self, client):
        """Test Monte Carlo simulation"""
        response = client.post(
            "/api/backtest/monte-carlo",
            json={
                "backtest_config": {
                    "symbol": "BTC/USDT",
                    "start_date": "2024-01-01",
                    "end_date": "2024-02-01",
                    "timeframe": "1h",
                    "strategy": {
                        "strategy_id": "momentum",
                        "parameters": {},
                        "initial_capital": 10000.0,
                        "position_size_pct": 0.1
                    }
                },
                "num_simulations": 100,
                "confidence_level": 0.95,
                "randomize_trades": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "simulation_id" in data
        assert "confidence_interval" in data
        assert "risk_of_ruin" in data
        assert len(data["simulated_returns"]) == 100
    
    def test_walk_forward_analysis(self, client):
        """Test walk-forward analysis"""
        response = client.post(
            "/api/backtest/walk-forward",
            json={
                "backtest_config": {
                    "symbol": "BTC/USDT",
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-01",
                    "timeframe": "1h",
                    "strategy": {
                        "strategy_id": "momentum",
                        "parameters": {},
                        "initial_capital": 10000.0,
                        "position_size_pct": 0.1
                    }
                },
                "in_sample_days": 60,
                "out_sample_days": 30,
                "anchor": False,
                "optimize_metric": "sharpe_ratio"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert "degradation_factor" in data
        assert "consistency_score" in data


class TestAPIMarketplace:
    """Test API marketplace functionality"""
    
    def test_generate_api_key(self, client):
        """Test API key generation"""
        response = client.post(
            "/api/marketplace/keys/generate",
            params={"user_id": "test_user", "tier": "pro"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["tier"] == "pro"
        assert data["rate_limit_per_hour"] == 1000
    
    def test_register_provider(self, client):
        """Test signal provider registration"""
        response = client.post(
            "/api/marketplace/providers/register",
            params={
                "user_id": "test_provider",
                "name": "Test Signals",
                "description": "High quality signals",
                "subscription_price": 29.99
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "provider_id" in data
        assert data["name"] == "Test Signals"
        assert data["subscription_price_monthly"] == 29.99
    
    def test_publish_signal(self, client):
        """Test signal publishing"""
        # First register provider
        provider_response = client.post(
            "/api/marketplace/providers/register",
            params={
                "user_id": "test_provider",
                "name": "Test Signals",
                "description": "Test",
                "subscription_price": 29.99
            }
        )
        provider_id = provider_response.json()["provider_id"]
        
        # Publish signal
        response = client.post(
            "/api/marketplace/signals/publish",
            json={
                "provider_id": provider_id,
                "symbol": "BTC/USDT",
                "signal_type": "buy",
                "entry_price": 50000.0,
                "stop_loss": 48000.0,
                "take_profit": 54000.0,
                "confidence": 85.0,
                "timeframe": "4h",
                "analysis": "Bullish breakout",
                "expires_hours": 24
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "signal_id" in data
        assert data["symbol"] == "BTC/USDT"
        assert data["confidence"] == 85.0
    
    def test_get_marketplace_stats(self, client):
        """Test marketplace statistics"""
        response = client.get("/api/marketplace/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_providers" in data
        assert "total_signals_24h" in data


class TestMultiExchangeArbitrage:
    """Test multi-exchange arbitrage functionality"""
    
    def test_start_scanner(self, client):
        """Test starting arbitrage scanner"""
        response = client.post(
            "/api/arbitrage/start",
            json={
                "enabled_exchanges": ["binance", "coinbase"],
                "min_profit_percent": 0.5,
                "max_position_size_usd": 1000.0,
                "auto_execute": False,
                "blacklist_symbols": [],
                "max_latency_ms": 500.0,
                "min_volume_24h_usd": 100000.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_opportunities(self, client):
        """Test retrieving arbitrage opportunities"""
        # Start scanner first
        client.post(
            "/api/arbitrage/start",
            json={
                "enabled_exchanges": ["binance", "coinbase"],
                "min_profit_percent": 0.5,
                "max_position_size_usd": 1000.0,
                "auto_execute": False
            }
        )
        
        # Get opportunities
        response = client.get("/api/arbitrage/opportunities")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_arbitrage_stats(self, client):
        """Test arbitrage statistics"""
        response = client.get("/api/arbitrage/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_opportunities_detected" in data
        assert "total_executed" in data
        assert "success_rate" in data
    
    def test_stop_scanner(self, client):
        """Test stopping arbitrage scanner"""
        # Start first
        client.post(
            "/api/arbitrage/start",
            json={
                "enabled_exchanges": ["binance", "coinbase"],
                "min_profit_percent": 0.5,
                "max_position_size_usd": 1000.0,
                "auto_execute": False
            }
        )
        
        # Stop
        response = client.post("/api/arbitrage/stop")
        
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestIntegrationScenarios:
    """Test complete user workflows"""
    
    def test_complete_trading_workflow(self, client):
        """Test complete workflow: backtest -> rebalance -> monitor"""
        # 1. Run backtest
        backtest_response = client.post(
            "/api/backtest/run",
            json={
                "symbol": "BTC/USDT",
                "start_date": "2024-01-01",
                "end_date": "2024-02-01",
                "timeframe": "1h",
                "strategy": {
                    "strategy_id": "momentum",
                    "parameters": {},
                    "initial_capital": 10000.0,
                    "position_size_pct": 0.1
                }
            }
        )
        assert backtest_response.status_code == 200
        
        # 2. Schedule rebalancing
        rebalance_response = client.post(
            "/api/portfolio/rebalance/schedule",
            json={
                "user_id": "test_user",
                "config": {
                    "strategy": "risk_parity",
                    "frequency": "daily",
                    "threshold_percent": 5.0,
                    "dry_run": False
                }
            }
        )
        assert rebalance_response.status_code == 200
        
        # 3. Check system health
        health_response = client.get("/api/health")
        assert health_response.status_code == 200
    
    def test_marketplace_workflow(self, client):
        """Test complete marketplace workflow"""
        # 1. Register provider
        provider_response = client.post(
            "/api/marketplace/providers/register",
            params={
                "user_id": "test_provider",
                "name": "Elite Signals",
                "description": "Premium signals",
                "subscription_price": 49.99
            }
        )
        provider_id = provider_response.json()["provider_id"]
        
        # 2. Publish signal
        signal_response = client.post(
            "/api/marketplace/signals/publish",
            json={
                "provider_id": provider_id,
                "symbol": "BTC/USDT",
                "signal_type": "buy",
                "entry_price": 50000.0,
                "confidence": 90.0,
                "timeframe": "4h",
                "analysis": "Strong bullish trend"
            }
        )
        signal_id = signal_response.json()["signal_id"]
        
        # 3. Generate API key for subscriber
        key_response = client.post(
            "/api/marketplace/keys/generate",
            params={"user_id": "subscriber", "tier": "basic"}
        )
        
        # 4. Subscribe to provider
        subscribe_response = client.post(
            f"/api/marketplace/subscribe/{provider_id}",
            params={"user_id": "subscriber"}
        )
        assert subscribe_response.json()["success"] is True


# Pytest configuration
@pytest.fixture
def client():
    """Create test client"""
    from server_fastapi.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
