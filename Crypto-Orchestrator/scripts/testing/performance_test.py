#!/usr/bin/env python3
"""
Performance Testing Script
Uses Locust for load testing API endpoints
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import aiohttp
import time
from typing import Dict, Any, List
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceTester:
    """Performance testing using aiohttp"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        iterations: int = 100,
        concurrent: int = 10,
    ) -> Dict[str, Any]:
        """
        Test an endpoint with load
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            headers: Request headers
            data: Request data (for POST/PUT)
            iterations: Number of requests
            concurrent: Concurrent requests
        
        Returns:
            Performance metrics
        """
        url = f"{self.base_url}{endpoint}"
        headers = headers or {}
        
        latencies = []
        errors = 0
        successes = 0
        
        async def make_request(session: aiohttp.ClientSession):
            nonlocal errors, successes
            start = time.time()
            try:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        await response.read()
                elif method == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        await response.read()
                elif method == "PUT":
                    async with session.put(url, json=data, headers=headers) as response:
                        await response.read()
                elif method == "DELETE":
                    async with session.delete(url, headers=headers) as response:
                        await response.read()
                
                latency = (time.time() - start) * 1000  # Convert to ms
                latencies.append(latency)
                successes += 1
            except Exception as e:
                errors += 1
                logger.error(f"Request failed: {e}")
        
        # Run concurrent requests
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(iterations):
                if len(tasks) >= concurrent:
                    # Wait for some to complete
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
                    await asyncio.gather(*done)
                
                tasks.append(make_request(session))
            
            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks)
        
        # Calculate statistics
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[len(sorted_latencies) // 2]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        else:
            avg_latency = min_latency = max_latency = p50 = p95 = p99 = 0
        
        metrics = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "concurrent": concurrent,
            "successes": successes,
            "errors": errors,
            "success_rate": (successes / iterations * 100) if iterations > 0 else 0,
            "latency_ms": {
                "avg": round(avg_latency, 2),
                "min": round(min_latency, 2),
                "max": round(max_latency, 2),
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
            },
            "throughput_rps": round(successes / (max(latencies) / 1000) if latencies else 0, 2),
        }
        
        self.results.append(metrics)
        return metrics
    
    def generate_report(self) -> str:
        """Generate performance test report"""
        report = ["# Performance Test Report\n"]
        report.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for result in self.results:
            report.append(f"## {result['method']} {result['endpoint']}\n\n")
            report.append(f"- **Iterations**: {result['iterations']}\n")
            report.append(f"- **Concurrent**: {result['concurrent']}\n")
            report.append(f"- **Success Rate**: {result['success_rate']:.2f}%\n")
            report.append(f"- **Throughput**: {result['throughput_rps']} req/s\n")
            report.append(f"- **Latency (avg)**: {result['latency_ms']['avg']}ms\n")
            report.append(f"- **Latency (p95)**: {result['latency_ms']['p95']}ms\n")
            report.append(f"- **Latency (p99)**: {result['latency_ms']['p99']}ms\n\n")
        
        return "\n".join(report)


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance testing script")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--endpoints", nargs="+", help="Endpoints to test")
    parser.add_argument("--iterations", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    tester = PerformanceTester(base_url=args.base_url)
    
    # Default endpoints if not provided
    endpoints = args.endpoints or [
        "/api/health",
        "/api/bots",
        "/api/trades",
    ]
    
    for endpoint in endpoints:
        logger.info(f"Testing {endpoint}...")
        await tester.test_endpoint(
            endpoint=endpoint,
            iterations=args.iterations,
            concurrent=args.concurrent,
        )
    
    # Generate report
    report = tester.generate_report()
    print(report)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
