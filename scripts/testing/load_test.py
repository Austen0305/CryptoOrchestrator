#!/usr/bin/env python3
"""
Load Testing Script
Tests system under various load conditions
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
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadTester:
    """Load testing for API endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    async def make_request(
        self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET"
    ) -> Dict[str, Any]:
        """Make a single request and measure performance"""
        start_time = asyncio.get_event_loop().time()
        try:
            async with session.request(method, f"{self.base_url}{endpoint}") as response:
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000  # ms
                await response.read()  # Read response body
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status,
                    "response_time_ms": round(elapsed, 2),
                    "success": response.status < 400,
                }
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "response_time_ms": round(elapsed, 2),
                "success": False,
                "error": str(e),
            }

    async def run_load_test(
        self,
        endpoint: str,
        concurrent_users: int,
        duration_seconds: int,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """Run load test for specified duration"""
        async with aiohttp.ClientSession() as session:
            start_time = asyncio.get_event_loop().time()
            end_time = start_time + duration_seconds

            # Create tasks for concurrent users
            tasks = []
            request_count = 0
            successful_requests = 0
            failed_requests = 0
            response_times = []

            async def user_loop():
                nonlocal request_count, successful_requests, failed_requests
                while asyncio.get_event_loop().time() < end_time:
                    result = await self.make_request(session, endpoint, method)
                    request_count += 1
                    if result["success"]:
                        successful_requests += 1
                        response_times.append(result["response_time_ms"])
                    else:
                        failed_requests += 1
                    await asyncio.sleep(0.1)  # Small delay between requests

            # Start concurrent users
            for _ in range(concurrent_users):
                tasks.append(asyncio.create_task(user_loop()))

            # Wait for all tasks
            await asyncio.gather(*tasks)

            # Calculate statistics
            if response_times:
                avg_time = statistics.mean(response_times)
                p50_time = statistics.median(response_times)
                sorted_times = sorted(response_times)
                p95_time = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0
                p99_time = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0
            else:
                avg_time = p50_time = p95_time = p99_time = 0

            actual_duration = asyncio.get_event_loop().time() - start_time
            requests_per_second = request_count / actual_duration if actual_duration > 0 else 0

            return {
                "endpoint": endpoint,
                "method": method,
                "concurrent_users": concurrent_users,
                "duration_seconds": actual_duration,
                "total_requests": request_count,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (
                    (successful_requests / request_count * 100) if request_count > 0 else 0
                ),
                "requests_per_second": round(requests_per_second, 2),
                "response_times": {
                    "avg_ms": round(avg_time, 2),
                    "p50_ms": round(p50_time, 2),
                    "p95_ms": round(p95_time, 2),
                    "p99_ms": round(p99_time, 2),
                },
                "timestamp": datetime.now().isoformat(),
            }

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate load test report"""
        report = []
        report.append("=" * 60)
        report.append("Load Test Report")
        report.append("=" * 60)
        report.append(f"\nEndpoint: {results['endpoint']}")
        report.append(f"Method: {results['method']}")
        report.append(f"Concurrent Users: {results['concurrent_users']}")
        report.append(f"Duration: {results['duration_seconds']:.2f}s")
        report.append(f"\nResults:")
        report.append(f"  Total Requests: {results['total_requests']}")
        report.append(f"  Successful: {results['successful_requests']}")
        report.append(f"  Failed: {results['failed_requests']}")
        report.append(f"  Success Rate: {results['success_rate']:.2f}%")
        report.append(f"  Requests/Second: {results['requests_per_second']:.2f}")
        report.append(f"\nResponse Times:")
        report.append(f"  Average: {results['response_times']['avg_ms']}ms")
        report.append(f"  p50: {results['response_times']['p50_ms']}ms")
        report.append(f"  p95: {results['response_times']['p95_ms']}ms")
        report.append(f"  p99: {results['response_times']['p99_ms']}ms")

        return "\n".join(report)


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Load Testing")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API",
    )
    parser.add_argument(
        "--endpoint",
        default="/api/health",
        help="Endpoint to test",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=100,
        help="Number of concurrent users",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds",
    )
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP method",
    )
    parser.add_argument(
        "--output",
        help="Output file for report (default: stdout)",
    )

    args = parser.parse_args()

    tester = LoadTester(base_url=args.base_url)
    results = await tester.run_load_test(
        endpoint=args.endpoint,
        concurrent_users=args.users,
        duration_seconds=args.duration,
        method=args.method,
    )
    report = tester.generate_report(results)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
