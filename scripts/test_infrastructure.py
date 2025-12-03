#!/usr/bin/env python3
"""
Infrastructure Testing Script - Phase 1
Tests database, Redis, and backend health
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List
import aiohttp
from datetime import datetime


class InfrastructureTester:
    """Test infrastructure components"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []
    
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} - {test_name}")
        if message:
            print(f"   └─ {message}")
    
    async def test_backend_health(self):
        """Test backend health endpoint"""
        print("\n🏥 Testing Backend Health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.log_result(
                            "Backend Health Check",
                            True,
                            f"Status: {data.get('status', 'unknown')}"
                        )
                        
                        # Check database connectivity
                        db_status = data.get('database', {}).get('status')
                        self.log_result(
                            "Database Connectivity",
                            db_status == "connected",
                            f"DB Status: {db_status}"
                        )
                        
                        # Check Redis connectivity
                        redis_status = data.get('redis', {}).get('status')
                        self.log_result(
                            "Redis Connectivity",
                            redis_status == "connected",
                            f"Redis Status: {redis_status}"
                        )
                        
                        return True
                    else:
                        self.log_result(
                            "Backend Health Check",
                            False,
                            f"Status code: {resp.status}"
                        )
                        return False
        except Exception as e:
            self.log_result("Backend Health Check", False, str(e))
            return False
    
    async def test_api_endpoints(self):
        """Test basic API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        endpoints = [
            ("/api/health", "GET"),
            ("/api/bots", "GET"),
            ("/api/integrations/status", "GET"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    async with session.request(method, url) as resp:
                        # Accept 200-299 or 401 (auth required)
                        passed = resp.status < 300 or resp.status == 401
                        self.log_result(
                            f"{method} {endpoint}",
                            passed,
                            f"Status: {resp.status}"
                        )
                except Exception as e:
                    self.log_result(f"{method} {endpoint}", False, str(e))
    
    async def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET"
                }
                async with session.options(
                    f"{self.base_url}/health",
                    headers=headers
                ) as resp:
                    cors_header = resp.headers.get("Access-Control-Allow-Origin")
                    self.log_result(
                        "CORS Headers Present",
                        cors_header is not None,
                        f"Allow-Origin: {cors_header}"
                    )
        except Exception as e:
            self.log_result("CORS Configuration", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print("\n" + "=" * 60)
        print("📊 Infrastructure Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print("=" * 60)
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - {r['test']}: {r['message']}")
        
        return failed == 0


async def main():
    """Main test runner"""
    print("🚀 Starting Infrastructure Tests...")
    print(f"Time: {datetime.now()}")
    
    tester = InfrastructureTester()
    
    # Run tests
    await tester.test_backend_health()
    await tester.test_api_endpoints()
    await tester.test_cors_configuration()
    
    # Print summary
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
