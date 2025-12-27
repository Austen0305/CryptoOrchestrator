#!/usr/bin/env python3
"""
API Compatibility Testing
Tests backward compatibility between API versions
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APICompatibilityTester:
    """Test API version compatibility"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    async def test_version_info(self, session: aiohttp.ClientSession, version: str) -> Dict[str, Any]:
        """Test version info endpoint"""
        try:
            url = f"{self.base_url}/api/{version}/info"
            async with session.get(url) as response:
                data = await response.json()
                return {
                    "version": version,
                    "endpoint": "/info",
                    "status_code": response.status_code,
                    "success": response.status == 200,
                    "data": data,
                    "headers": dict(response.headers),
                }
        except Exception as e:
            return {
                "version": version,
                "endpoint": "/info",
                "success": False,
                "error": str(e),
            }

    async def test_deprecation_headers(self, session: aiohttp.ClientSession, version: str) -> Dict[str, Any]:
        """Test deprecation headers"""
        try:
            url = f"{self.base_url}/api/{version}/info"
            async with session.get(url) as response:
                headers = dict(response.headers)
                return {
                    "version": version,
                    "deprecated": headers.get("X-API-Deprecated") == "true",
                    "deprecation_date": headers.get("X-API-Deprecation-Date"),
                    "sunset_date": headers.get("X-API-Sunset-Date"),
                    "migration_guide": headers.get("X-API-Migration-Guide"),
                    "api_version": headers.get("X-API-Version"),
                    "supported_versions": headers.get("X-Supported-Versions"),
                }
        except Exception as e:
            return {
                "version": version,
                "success": False,
                "error": str(e),
            }

    async def test_endpoint_compatibility(
        self, session: aiohttp.ClientSession, version: str, endpoint: str
    ) -> Dict[str, Any]:
        """Test endpoint compatibility across versions"""
        try:
            url = f"{self.base_url}/api/{version}{endpoint}"
            async with session.get(url) as response:
                return {
                    "version": version,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": response.status < 400,
                    "headers": dict(response.headers),
                }
        except Exception as e:
            return {
                "version": version,
                "endpoint": endpoint,
                "success": False,
                "error": str(e),
            }

    async def run_compatibility_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests"""
        async with aiohttp.ClientSession() as session:
            # Test versions
            versions = ["v1", "v2"]

            results = {
                "test_date": datetime.now().isoformat(),
                "base_url": self.base_url,
                "versions_tested": versions,
                "tests": [],
            }

            # Test version info endpoints
            for version in versions:
                logger.info(f"Testing {version} version info...")
                info_result = await self.test_version_info(session, version)
                results["tests"].append(info_result)

                # Test deprecation headers
                logger.info(f"Testing {version} deprecation headers...")
                deprecation_result = await self.test_deprecation_headers(session, version)
                results["tests"].append(deprecation_result)

                # Test common endpoints
                common_endpoints = ["/health", "/metrics"]
                for endpoint in common_endpoints:
                    logger.info(f"Testing {version}{endpoint}...")
                    endpoint_result = await self.test_endpoint_compatibility(session, version, endpoint)
                    results["tests"].append(endpoint_result)

            return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate compatibility test report"""
        report = []
        report.append("=" * 60)
        report.append("API Compatibility Test Report")
        report.append("=" * 60)
        report.append(f"\nTest Date: {results['test_date']}")
        report.append(f"Base URL: {results['base_url']}")
        report.append(f"Versions Tested: {', '.join(results['versions_tested'])}")

        # Summary
        total_tests = len(results["tests"])
        passed_tests = sum(1 for test in results["tests"] if test.get("success", False))
        failed_tests = total_tests - passed_tests

        report.append(f"\nSummary:")
        report.append(f"  Total Tests: {total_tests}")
        report.append(f"  Passed: {passed_tests}")
        report.append(f"  Failed: {failed_tests}")
        report.append(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # Detailed results
        report.append(f"\nDetailed Results:")
        for test in results["tests"]:
            status = "✅ PASS" if test.get("success", False) else "❌ FAIL"
            report.append(f"\n{status} - {test.get('version', 'unknown')} - {test.get('endpoint', 'unknown')}")
            if not test.get("success", False):
                report.append(f"  Error: {test.get('error', 'Unknown error')}")
            if "deprecated" in test:
                report.append(f"  Deprecated: {test.get('deprecated', False)}")
                if test.get("sunset_date"):
                    report.append(f"  Sunset Date: {test.get('sunset_date')}")

        return "\n".join(report)


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="API Compatibility Testing")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API",
    )
    parser.add_argument(
        "--output",
        help="Output file for report (default: stdout)",
    )

    args = parser.parse_args()

    tester = APICompatibilityTester(base_url=args.base_url)
    results = await tester.run_compatibility_tests()
    report = tester.generate_report(results)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report written to {args.output}")
    else:
        print(report)

    # Exit with error code if tests failed
    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"] if test.get("success", False))
    if passed_tests < total_tests:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
