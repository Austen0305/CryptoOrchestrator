#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Feature Verification Script
Systematically tests all API routes, features, and integrations
"""

import os
import sys
import asyncio
import json
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    sys.exit(1)

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


@dataclass
class EndpointTest:
    """Test result for a single endpoint"""
    method: str
    path: str
    status_code: Optional[int] = None
    success: bool = False
    error: Optional[str] = None
    response_time_ms: Optional[float] = None
    requires_auth: bool = False
    tested: bool = False


@dataclass
class FeatureTestResult:
    """Test results for a feature category"""
    feature_name: str
    endpoints_tested: int = 0
    endpoints_passed: int = 0
    endpoints_failed: int = 0
    endpoints_skipped: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class FeatureVerifier:
    """Comprehensive feature verification system"""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token or os.getenv("AUTH_TOKEN")
        self.results: Dict[str, FeatureTestResult] = {}
        self.endpoint_results: List[EndpointTest] = []
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=10.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def test_endpoint(
        self,
        method: str,
        path: str,
        requires_auth: bool = False,
        json_data: Optional[Dict] = None,
        expected_status: Optional[int] = None
    ) -> EndpointTest:
        """Test a single endpoint"""
        full_url = f"{self.base_url}{path}"
        result = EndpointTest(
            method=method.upper(),
            path=path,
            requires_auth=requires_auth,
            tested=True
        )
        
        headers = {}
        if requires_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            import time
            start_time = time.time()
            
            response = await self.session.request(
                method=method.upper(),
                url=full_url,
                headers=headers,
                json=json_data
            )
            
            result.response_time_ms = (time.time() - start_time) * 1000
            result.status_code = response.status_code
            
            # Success criteria:
            # - 200-299: Success
            # - 401: Auth required (expected if requires_auth=True but no token)
            # - 404: Not found (endpoint doesn't exist)
            # - 422: Validation error (endpoint exists but bad request)
            # - 500+: Server error (endpoint exists but failed)
            
            if response.status_code < 300:
                result.success = True
            elif response.status_code == 401 and requires_auth and not self.auth_token:
                result.success = True  # Expected auth required
            elif response.status_code == 404:
                result.success = False
                result.error = "Endpoint not found"
            elif response.status_code == 422:
                result.success = True  # Endpoint exists, validation failed (expected)
            elif response.status_code >= 500:
                result.success = False
                result.error = f"Server error: {response.status_code}"
            else:
                result.success = True  # Other 4xx means endpoint exists
            
            if expected_status and response.status_code != expected_status:
                result.success = False
                result.error = f"Expected {expected_status}, got {response.status_code}"
                
        except Exception as e:
            result.success = False
            result.error = str(e)
        
        self.endpoint_results.append(result)
        return result
    
    async def verify_authentication_features(self) -> FeatureTestResult:
        """Verify authentication features"""
        feature = FeatureTestResult(feature_name="Authentication")
        
        print("\n🔐 Testing Authentication Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/auth/me", True),
            ("POST", "/api/auth/register", False),
            ("POST", "/api/auth/login", False),
            ("POST", "/api/auth/logout", True),
            ("POST", "/api/auth/refresh", False),
            ("POST", "/api/auth/forgot-password", False),
            ("POST", "/api/auth/reset-password", False),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["authentication"] = feature
        return feature
    
    async def verify_bot_features(self) -> FeatureTestResult:
        """Verify bot management features"""
        feature = FeatureTestResult(feature_name="Bot Management")
        
        print("\n🤖 Testing Bot Management Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/bots", True),
            ("POST", "/api/bots", True),
            ("GET", "/api/bots/{id}", True),
            ("PATCH", "/api/bots/{id}", True),
            ("DELETE", "/api/bots/{id}", True),
            ("POST", "/api/bots/{id}/start", True),
            ("POST", "/api/bots/{id}/stop", True),
        ]
        
        for method, path, requires_auth in endpoints:
            # Replace {id} with test ID
            test_path = path.replace("{id}", "test-bot-id")
            result = await self.test_endpoint(method, test_path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {test_path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {test_path}: {result.error}")
                print(f"  ❌ {method} {test_path}: {result.error}")
        
        self.results["bots"] = feature
        return feature
    
    async def verify_trading_features(self) -> FeatureTestResult:
        """Verify trading features"""
        feature = FeatureTestResult(feature_name="Trading")
        
        print("\n📈 Testing Trading Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/trades", True),
            ("POST", "/api/trades", True),
            ("GET", "/api/trades/{id}", True),
            ("GET", "/api/advanced-orders", True),
            ("POST", "/api/advanced-orders", True),
            ("GET", "/api/dca-trading", True),
            ("GET", "/api/grid-trading", True),
            ("GET", "/api/infinity-grid", True),
            ("GET", "/api/futures-trading", True),
            ("GET", "/api/copy-trading", True),
            ("GET", "/api/trailing-bot", True),
        ]
        
        for method, path, requires_auth in endpoints:
            test_path = path.replace("{id}", "test-id")
            result = await self.test_endpoint(method, test_path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {test_path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {test_path}: {result.error}")
                print(f"  ❌ {method} {test_path}: {result.error}")
        
        self.results["trading"] = feature
        return feature
    
    async def verify_dex_features(self) -> FeatureTestResult:
        """Verify DEX trading features"""
        feature = FeatureTestResult(feature_name="DEX Trading")
        
        print("\n💱 Testing DEX Trading Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/dex-trading/quote", True),
            ("POST", "/api/dex-trading/swap", True),
            ("GET", "/api/dex-trading/swap/{tx_hash}", True),
            ("GET", "/api/dex-positions", True),
            ("GET", "/api/mev-protection/status/{chain_id}", True),
            ("GET", "/api/transaction-monitoring", True),
        ]
        
        for method, path, requires_auth in endpoints:
            test_path = path.replace("{tx_hash}", "test-tx").replace("{chain_id}", "1")
            result = await self.test_endpoint(method, test_path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {test_path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {test_path}: {result.error}")
                print(f"  ❌ {method} {test_path}: {result.error}")
        
        self.results["dex"] = feature
        return feature
    
    async def verify_portfolio_features(self) -> FeatureTestResult:
        """Verify portfolio features"""
        feature = FeatureTestResult(feature_name="Portfolio")
        
        print("\n💼 Testing Portfolio Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/portfolio", True),
            ("GET", "/api/portfolio/performance", True),
            ("POST", "/api/portfolio-rebalance/schedule", True),
            ("GET", "/api/analytics", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["portfolio"] = feature
        return feature
    
    async def verify_wallet_features(self) -> FeatureTestResult:
        """Verify wallet features"""
        feature = FeatureTestResult(feature_name="Wallet")
        
        print("\n👛 Testing Wallet Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/wallets", True),
            ("POST", "/api/wallets", True),
            ("GET", "/api/wallet/{id}", True),
            ("GET", "/api/wallet/{id}/balance", True),
            ("POST", "/api/wallet/deposit", True),
            ("POST", "/api/withdrawals", True),
            ("GET", "/api/crypto-transfer", True),
        ]
        
        for method, path, requires_auth in endpoints:
            test_path = path.replace("{id}", "test-wallet-id")
            result = await self.test_endpoint(method, test_path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {test_path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {test_path}: {result.error}")
                print(f"  ❌ {method} {test_path}: {result.error}")
        
        self.results["wallet"] = feature
        return feature
    
    async def verify_staking_features(self) -> FeatureTestResult:
        """Verify staking features"""
        feature = FeatureTestResult(feature_name="Staking")
        
        print("\n💰 Testing Staking Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/staking", True),
            ("POST", "/api/staking/stake", True),
            ("POST", "/api/staking/unstake", True),
            ("GET", "/api/staking/rewards", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["staking"] = feature
        return feature
    
    async def verify_market_features(self) -> FeatureTestResult:
        """Verify market data features"""
        feature = FeatureTestResult(feature_name="Market Data")
        
        print("\n📊 Testing Market Data Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/markets", True),
            ("GET", "/api/markets/prices", True),
            ("GET", "/api/price-alerts", True),
            ("POST", "/api/price-alerts", True),
            ("GET", "/api/sentiment", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["markets"] = feature
        return feature
    
    async def verify_strategy_features(self) -> FeatureTestResult:
        """Verify strategy features"""
        feature = FeatureTestResult(feature_name="Strategies")
        
        print("\n📋 Testing Strategy Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/strategies", True),
            ("GET", "/api/strategies/{id}", True),
            ("POST", "/api/backtesting-enhanced/run", True),
            ("GET", "/api/backtesting-enhanced/results", True),
        ]
        
        for method, path, requires_auth in endpoints:
            test_path = path.replace("{id}", "test-id")
            result = await self.test_endpoint(method, test_path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {test_path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {test_path}: {result.error}")
                print(f"  ❌ {method} {test_path}: {result.error}")
        
        self.results["strategies"] = feature
        return feature
    
    async def verify_notification_features(self) -> FeatureTestResult:
        """Verify notification features"""
        feature = FeatureTestResult(feature_name="Notifications")
        
        print("\n🔔 Testing Notification Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/notifications", True),
            ("PATCH", "/api/notifications/{id}/read", True),
            ("GET", "/api/alerting", True),
            ("POST", "/api/alerting", True),
        ]
        
        for method, path, requires_auth in endpoints:
            test_path = path.replace("{id}", "test-id")
            result = await self.test_endpoint(method, test_path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {test_path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {test_path}: {result.error}")
                print(f"  ❌ {method} {test_path}: {result.error}")
        
        self.results["notifications"] = feature
        return feature
    
    async def verify_settings_features(self) -> FeatureTestResult:
        """Verify settings features"""
        feature = FeatureTestResult(feature_name="Settings")
        
        print("\n⚙️  Testing Settings Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/preferences", True),
            ("PATCH", "/api/preferences", True),
            ("GET", "/api/trading-mode", True),
            ("POST", "/api/trading-mode/switch", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["settings"] = feature
        return feature
    
    async def verify_health_features(self) -> FeatureTestResult:
        """Verify health check features"""
        feature = FeatureTestResult(feature_name="Health Checks")
        
        print("\n🏥 Testing Health Check Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/health", False),
            ("GET", "/api/health/aggregated", False),
            ("GET", "/health", False),
            ("GET", "/healthz", False),
            ("GET", "/api/status", False),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["health"] = feature
        return feature
    
    async def discover_routes_from_openapi(self) -> List[Tuple[str, str, str]]:
        """Discover routes from OpenAPI schema"""
        try:
            openapi_url = f"{self.base_url}/openapi.json"
            response = await self.session.get(openapi_url)
            
            if response.status_code != 200:
                return []
            
            schema = response.json()
            routes = []
            
            for path, methods in schema.get("paths", {}).items():
                for method, details in methods.items():
                    if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                        # Determine if auth required from security
                        requires_auth = bool(details.get("security"))
                        routes.append((method.upper(), path, requires_auth))
            
            return routes
        except Exception as e:
            print(f"  ⚠️  Could not discover routes from OpenAPI: {e}")
            return []
    
    async def verify_all_routes_discovered(self) -> FeatureTestResult:
        """Verify all routes discovered from OpenAPI"""
        feature = FeatureTestResult(feature_name="All Routes (Discovered)")
        
        print("\n🔍 Discovering routes from OpenAPI...")
        print("-" * 60)
        
        routes = await self.discover_routes_from_openapi()
        
        if not routes:
            print("  ⚠️  Could not discover routes, skipping discovered route tests")
            return feature
        
        print(f"  ✅ Discovered {len(routes)} routes")
        print(f"\n📋 Testing discovered routes...")
        
        # Test a sample of routes (limit to avoid timeout)
        sample_routes = routes[:50]  # Test first 50 routes
        
        for method, path, requires_auth in sample_routes:
            # Skip routes with path parameters for now (would need test IDs)
            if "{" in path and "}" in path:
                continue
            
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            
            if result.success:
                feature.endpoints_passed += 1
            else:
                feature.endpoints_failed += 1
                if len(feature.errors) < 10:  # Limit error list
                    feature.errors.append(f"{method} {path}: {result.error}")
        
        self.results["all_routes_discovered"] = feature
        return feature
    
    async def verify_risk_features(self) -> FeatureTestResult:
        """Verify risk management features"""
        feature = FeatureTestResult(feature_name="Risk Management")
        
        print("\n⚠️  Testing Risk Management Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/risk-management", True),
            ("GET", "/api/risk-scenarios", True),
            ("GET", "/api/risk", True),
            ("GET", "/api/trading-safety", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["risk"] = feature
        return feature
    
    async def verify_ml_features(self) -> FeatureTestResult:
        """Verify ML/AI features"""
        feature = FeatureTestResult(feature_name="ML/AI")
        
        print("\n🤖 Testing ML/AI Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/ml/training", True),
            ("GET", "/api/ml-v2", True),
            ("GET", "/api/ai-analysis", True),
            ("GET", "/api/ai-copilot", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["ml"] = feature
        return feature
    
    async def verify_billing_features(self) -> FeatureTestResult:
        """Verify billing features"""
        feature = FeatureTestResult(feature_name="Billing")
        
        print("\n💳 Testing Billing Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/billing", True),
            ("GET", "/api/payments", True),
            ("GET", "/api/payment-methods", True),
            ("GET", "/api/fees", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["billing"] = feature
        return feature
    
    async def verify_admin_features(self) -> FeatureTestResult:
        """Verify admin features"""
        feature = FeatureTestResult(feature_name="Admin")
        
        print("\n👑 Testing Admin Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/admin", True),
            ("GET", "/api/platform-revenue", True),
            ("GET", "/api/business-metrics", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["admin"] = feature
        return feature
    
    async def verify_security_features(self) -> FeatureTestResult:
        """Verify security features"""
        feature = FeatureTestResult(feature_name="Security")
        
        print("\n🔒 Testing Security Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/security", True),
            ("GET", "/api/security-whitelists", True),
            ("GET", "/api/cold-storage", True),
            ("GET", "/api/fraud-detection", True),
            ("GET", "/api/kyc", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["security"] = feature
        return feature
    
    async def verify_monitoring_features(self) -> FeatureTestResult:
        """Verify monitoring features"""
        feature = FeatureTestResult(feature_name="Monitoring")
        
        print("\n📊 Testing Monitoring Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/monitoring", True),
            ("GET", "/api/metrics", True),
            ("GET", "/api/performance", True),
            ("GET", "/api/activity", True),
            ("GET", "/api/database-performance", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["monitoring"] = feature
        return feature
    
    async def verify_additional_features(self) -> FeatureTestResult:
        """Verify additional features"""
        feature = FeatureTestResult(feature_name="Additional Features")
        
        print("\n➕ Testing Additional Features...")
        print("-" * 60)
        
        endpoints = [
            ("GET", "/api/leaderboard", True),
            ("GET", "/api/marketplace", True),
            ("GET", "/api/favorites", True),
            ("GET", "/api/recommendations", True),
            ("GET", "/api/automation", True),
            ("GET", "/api/export", True),
            ("GET", "/api/licensing", True),
            ("GET", "/api/demo-mode", True),
        ]
        
        for method, path, requires_auth in endpoints:
            result = await self.test_endpoint(method, path, requires_auth=requires_auth)
            feature.endpoints_tested += 1
            if result.success:
                feature.endpoints_passed += 1
                print(f"  ✅ {method} {path}")
            else:
                feature.endpoints_failed += 1
                feature.errors.append(f"{method} {path}: {result.error}")
                print(f"  ❌ {method} {path}: {result.error}")
        
        self.results["additional"] = feature
        return feature
    
    async def verify_all_features(self, discover_routes: bool = False) -> Dict[str, FeatureTestResult]:
        """Verify all features"""
        print("🚀 CryptoOrchestrator Comprehensive Feature Verification")
        print("=" * 60)
        
        # Run all feature tests
        await self.verify_health_features()
        await self.verify_authentication_features()
        await self.verify_bot_features()
        await self.verify_trading_features()
        await self.verify_dex_features()
        await self.verify_portfolio_features()
        await self.verify_wallet_features()
        await self.verify_staking_features()
        await self.verify_market_features()
        await self.verify_strategy_features()
        await self.verify_notification_features()
        await self.verify_settings_features()
        await self.verify_risk_features()
        await self.verify_ml_features()
        await self.verify_billing_features()
        await self.verify_admin_features()
        await self.verify_security_features()
        await self.verify_monitoring_features()
        await self.verify_additional_features()
        
        # Optionally discover and test all routes from OpenAPI
        if discover_routes:
            await self.verify_all_routes_discovered()
        
        # Generate summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 60)
        print("📊 Feature Verification Summary")
        print("-" * 60)
        
        total_tested = sum(r.endpoints_tested for r in self.results.values())
        total_passed = sum(r.endpoints_passed for r in self.results.values())
        total_failed = sum(r.endpoints_failed for r in self.results.values())
        
        for feature_name, result in self.results.items():
            status = "✅" if result.endpoints_failed == 0 else "❌"
            print(f"  {status} {result.feature_name}: "
                  f"{result.endpoints_passed}/{result.endpoints_tested} passed")
        
        print("-" * 60)
        print(f"  Total: {total_passed}/{total_tested} endpoints passed")
        
        if total_failed > 0:
            print(f"\n❌ {total_failed} endpoints failed")
            print("\nErrors:")
            for result in self.results.values():
                for error in result.errors[:5]:  # Show first 5 errors per feature
                    print(f"  - {error}")
        else:
            print("\n✅ All endpoints verified successfully!")
    
    def save_report(self, output_file: str = "feature_verification_report.json"):
        """Save verification report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "features": {k: asdict(v) for k, v in self.results.items()},
            "endpoints": [asdict(e) for e in self.endpoint_results]
        }
        
        output_path = Path(output_file)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\n📄 Report saved to: {output_path.absolute()}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive feature verification for CryptoOrchestrator"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BACKEND_URL", "http://localhost:8000"),
        help="Backend base URL"
    )
    parser.add_argument(
        "--auth-token",
        default=os.getenv("AUTH_TOKEN"),
        help="JWT authentication token"
    )
    parser.add_argument(
        "--output",
        default="feature_verification_report.json",
        help="Output report file"
    )
    parser.add_argument(
        "--discover-routes",
        action="store_true",
        help="Discover and test all routes from OpenAPI schema"
    )
    
    args = parser.parse_args()
    
    async with FeatureVerifier(base_url=args.base_url, auth_token=args.auth_token) as verifier:
        results = await verifier.verify_all_features(discover_routes=args.discover_routes)
        verifier.save_report(args.output)
        
        # Exit with error code if any failures
        total_failed = sum(r.endpoints_failed for r in results.values())
        sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
