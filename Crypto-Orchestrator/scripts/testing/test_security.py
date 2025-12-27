#!/usr/bin/env python3
"""
Security Testing Script - Phase 2
Tests authentication, rate limiting, SQL injection, XSS, and CSRF protection
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
import time


class SecurityTester:
    """Test security features"""
    
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
    
    async def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        print("\n🛡️ Testing SQL Injection Protection...")
        
        # Common SQL injection patterns
        injection_attempts = [
            "admin' OR '1'='1",
            "admin' OR '1'='1' --",
            "admin'; DROP TABLE users; --",
            "' OR 1=1 --",
            "1' UNION SELECT NULL, NULL, NULL --"
        ]
        
        async with aiohttp.ClientSession() as session:
            for payload in injection_attempts:
                try:
                    # Try injection in login endpoint
                    data = {
                        "email": payload,
                        "password": "test"
                    }
                    async with session.post(
                        f"{self.base_url}/api/auth/login",
                        json=data
                    ) as resp:
                        # Should reject with 400/401/422, not 500 (server error)
                        passed = resp.status in [400, 401, 422]
                        self.log_result(
                            f"SQL Injection Block: {payload[:30]}...",
                            passed,
                            f"Status: {resp.status}"
                        )
                except Exception as e:
                    self.log_result(
                        f"SQL Injection Test: {payload[:30]}...",
                        False,
                        str(e)
                    )
    
    async def test_xss_protection(self):
        """Test XSS protection"""
        print("\n🛡️ Testing XSS Protection...")
        
        # Common XSS patterns
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        async with aiohttp.ClientSession() as session:
            for payload in xss_attempts:
                try:
                    # Try XSS in registration endpoint
                    data = {
                        "email": f"test@test.com",
                        "username": payload,
                        "password": "Test1234!"
                    }
                    async with session.post(
                        f"{self.base_url}/api/auth/register",
                        json=data
                    ) as resp:
                        # Should reject with 400/422, not accept
                        passed = resp.status in [400, 422]
                        self.log_result(
                            f"XSS Block: {payload[:30]}...",
                            passed,
                            f"Status: {resp.status}"
                        )
                except Exception as e:
                    self.log_result(
                        f"XSS Test: {payload[:30]}...",
                        False,
                        str(e)
                    )
    
    async def test_rate_limiting(self):
        """Test rate limiting"""
        print("\n⏱️ Testing Rate Limiting...")
        
        async with aiohttp.ClientSession() as session:
            # Make rapid requests
            statuses = []
            for i in range(20):
                try:
                    async with session.post(
                        f"{self.base_url}/api/auth/login",
                        json={"email": "test@test.com", "password": "wrong"}
                    ) as resp:
                        statuses.append(resp.status)
                except Exception:
                    pass
            
            # Should eventually get rate limited (429)
            rate_limited = 429 in statuses
            self.log_result(
                "Rate Limiting Active",
                rate_limited,
                f"Got 429 after {statuses.count(429)} requests"
            )
    
    async def test_content_security_policy(self):
        """Test Content Security Policy headers"""
        print("\n🔒 Testing Security Headers...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    # Check for security headers
                    headers = resp.headers
                    
                    csp = headers.get("Content-Security-Policy")
                    self.log_result(
                        "Content-Security-Policy Header",
                        csp is not None,
                        f"CSP: {csp[:50] if csp else 'Missing'}..."
                    )
                    
                    xframe = headers.get("X-Frame-Options")
                    self.log_result(
                        "X-Frame-Options Header",
                        xframe is not None,
                        f"X-Frame-Options: {xframe}"
                    )
                    
                    xcontent = headers.get("X-Content-Type-Options")
                    self.log_result(
                        "X-Content-Type-Options Header",
                        xcontent is not None,
                        f"X-Content-Type-Options: {xcontent}"
                    )
        except Exception as e:
            self.log_result("Security Headers", False, str(e))
    
    async def test_password_validation(self):
        """Test password validation"""
        print("\n🔑 Testing Password Validation...")
        
        # Weak passwords that should be rejected (clearly marked as test data)
        weak_passwords = [
            "TEST123",  # Too weak
            "TEST_PASSWORD_WEAK",  # Common pattern
            "12345678",  # All numbers
            "testonly"  # Too simple
        ]
        
        async with aiohttp.ClientSession() as session:
            for password in weak_passwords:
                try:
                    data = {
                        "email": "test@example.com",
                        "username": "testuser",
                        "password": password
                    }
                    async with session.post(
                        f"{self.base_url}/api/auth/register",
                        json=data
                    ) as resp:
                        # Should reject weak passwords
                        passed = resp.status in [400, 422]
                        self.log_result(
                            f"Weak Password Rejected: {password}",
                            passed,
                            f"Status: {resp.status}"
                        )
                except Exception as e:
                    self.log_result(
                        f"Password Validation Test: {password}",
                        False,
                        str(e)
                    )
    
    async def test_cors_restrictions(self):
        """Test CORS restrictions"""
        print("\n🌐 Testing CORS Restrictions...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try with unauthorized origin
                headers = {
                    "Origin": "http://evil.com",
                    "Access-Control-Request-Method": "POST"
                }
                async with session.options(
                    f"{self.base_url}/api/auth/login",
                    headers=headers
                ) as resp:
                    cors_header = resp.headers.get("Access-Control-Allow-Origin")
                    # Should not allow evil.com
                    passed = cors_header != "http://evil.com"
                    self.log_result(
                        "CORS Restricts Unauthorized Origins",
                        passed,
                        f"Allow-Origin: {cors_header}"
                    )
        except Exception as e:
            self.log_result("CORS Restrictions", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print("\n" + "=" * 60)
        print("🔒 Security Test Summary")
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
        else:
            print("\n✅ All security tests passed!")
        
        return failed == 0


async def main():
    """Main test runner"""
    print("🚀 Starting Security Tests...")
    print(f"Time: {datetime.now()}")
    
    tester = SecurityTester()
    
    # Run tests
    await tester.test_sql_injection_protection()
    await tester.test_xss_protection()
    await tester.test_rate_limiting()
    await tester.test_content_security_policy()
    await tester.test_password_validation()
    await tester.test_cors_restrictions()
    
    # Print summary
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
