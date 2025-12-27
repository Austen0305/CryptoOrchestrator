#!/usr/bin/env python3
"""
Security Testing Script
Basic security testing for API endpoints
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityTester:
    """Basic security testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.vulnerabilities: List[Dict[str, Any]] = []
    
    async def test_sql_injection(self, endpoint: str, param: str = "id") -> List[Dict[str, Any]]:
        """Test for SQL injection vulnerabilities"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            "1 OR 1=1",
        ]
        
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            for payload in sql_payloads:
                try:
                    url = f"{self.base_url}{endpoint}?{param}={payload}"
                    async with session.get(url) as response:
                        if response.status == 500:
                            vulnerabilities.append({
                                "type": "sql_injection",
                                "endpoint": endpoint,
                                "payload": payload,
                                "severity": "high",
                            })
                except Exception as e:
                    logger.debug(f"Error testing payload {payload}: {e}")
        
        return vulnerabilities
    
    async def test_xss(self, endpoint: str, param: str = "input") -> List[Dict[str, Any]]:
        """Test for XSS vulnerabilities"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            for payload in xss_payloads:
                try:
                    url = f"{self.base_url}{endpoint}?{param}={payload}"
                    async with session.get(url) as response:
                        text = await response.text()
                        if payload in text:
                            vulnerabilities.append({
                                "type": "xss",
                                "endpoint": endpoint,
                                "payload": payload,
                                "severity": "medium",
                            })
                except Exception as e:
                    logger.debug(f"Error testing payload {payload}: {e}")
        
        return vulnerabilities
    
    async def test_authentication(self, endpoint: str) -> List[Dict[str, Any]]:
        """Test authentication requirements"""
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        vulnerabilities.append({
                            "type": "missing_authentication",
                            "endpoint": endpoint,
                            "severity": "high",
                            "message": "Endpoint accessible without authentication",
                        })
            except Exception as e:
                logger.debug(f"Error testing authentication: {e}")
        
        return vulnerabilities
    
    async def test_rate_limiting(self, endpoint: str, requests: int = 100) -> List[Dict[str, Any]]:
        """Test rate limiting"""
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            success_count = 0
            for i in range(requests):
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            success_count += 1
                except Exception as e:
                    logger.debug(f"Error in rate limit test: {e}")
            
            if success_count == requests:
                vulnerabilities.append({
                    "type": "no_rate_limiting",
                    "endpoint": endpoint,
                    "severity": "medium",
                    "message": f"Endpoint allowed {success_count} requests without rate limiting",
                })
        
        return vulnerabilities
    
    def generate_report(self) -> str:
        """Generate security test report"""
        report = ["# Security Test Report\n"]
        report.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if not self.vulnerabilities:
            report.append("✅ No vulnerabilities found\n")
        else:
            report.append(f"⚠️ Found {len(self.vulnerabilities)} potential vulnerabilities\n\n")
            
            # Group by severity
            high = [v for v in self.vulnerabilities if v.get("severity") == "high"]
            medium = [v for v in self.vulnerabilities if v.get("severity") == "medium"]
            low = [v for v in self.vulnerabilities if v.get("severity") == "low"]
            
            if high:
                report.append("## High Severity\n\n")
                for vuln in high:
                    report.append(f"- **{vuln['type']}** in {vuln['endpoint']}\n")
            
            if medium:
                report.append("\n## Medium Severity\n\n")
                for vuln in medium:
                    report.append(f"- **{vuln['type']}** in {vuln['endpoint']}\n")
        
        return "\n".join(report)


async def main():
    """Main function"""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="Security testing script")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--endpoints", nargs="+", help="Endpoints to test")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    tester = SecurityTester(base_url=args.base_url)
    
    # Default endpoints if not provided
    endpoints = args.endpoints or [
        "/api/bots",
        "/api/trades",
        "/api/users",
    ]
    
    for endpoint in endpoints:
        logger.info(f"Testing {endpoint}...")
        
        # Run security tests
        sql_vulns = await tester.test_sql_injection(endpoint)
        xss_vulns = await tester.test_xss(endpoint)
        auth_vulns = await tester.test_authentication(endpoint)
        rate_limit_vulns = await tester.test_rate_limiting(endpoint)
        
        tester.vulnerabilities.extend(sql_vulns + xss_vulns + auth_vulns + rate_limit_vulns)
    
    # Generate report
    report = tester.generate_report()
    print(report)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
