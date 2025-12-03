#!/usr/bin/env python3
"""
Load Testing Script for CryptoOrchestrator API
Tests API performance under load with comprehensive metrics
"""
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import argparse
from datetime import datetime
import json


class LoadTester:
    """Load testing tool for API endpoints with comprehensive metrics"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []
        self.start_time = None
        self.end_time = None
    
    async def make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str = "GET",
        headers: Dict = None,
        data: Dict = None
    ) -> Dict:
        """Make a single API request"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    await response.read()
            elif method == "POST":
                async with session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    await response.read()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            elapsed = time.time() - start_time
            
            return {
                "status": status,
                "elapsed": elapsed,
                "success": 200 <= status < 300,
                "error": None
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "status": 0,
                "elapsed": elapsed,
                "success": False,
                "error": str(e)
            }
    
    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_requests: int = 10,
        total_requests: int = 100,
        headers: Dict = None,
        data: Dict = None
    ):
        """Run load test on an endpoint"""
        print(f"\n🧪 Load Testing: {method} {endpoint}")
        print(f"   Concurrent: {concurrent_requests}, Total: {total_requests}")
        
        self.start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=concurrent_requests * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for i in range(total_requests):
                task = self.make_request(session, endpoint, method, headers, data)
                tasks.append(task)
                
                # Control concurrency
                if len(tasks) >= concurrent_requests:
                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)
                    tasks = []
                    await asyncio.sleep(0.1)  # Small delay between batches
            
            # Process remaining tasks
            if tasks:
                results = await asyncio.gather(*tasks)
                self.results.extend(results)
        
        self.end_time = time.time()
    
    def print_results(self):
        """Print load test results"""
        if not self.results:
            print("No results to display")
            return
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        elapsed_times = [r["elapsed"] for r in self.results]
        successful_times = [r["elapsed"] for r in self.results if r["success"]]
        
        # Calculate throughput
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        throughput = total / total_duration if total_duration > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 Load Test Results")
        print("=" * 60)
        print(f"Total Requests: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"Duration: {total_duration:.2f}s")
        print(f"Throughput: {throughput:.2f} req/s")
        
        if successful_times:
            print(f"\nResponse Times (successful requests):")
            print(f"  Min: {min(successful_times)*1000:.2f} ms")
            print(f"  Max: {max(successful_times)*1000:.2f} ms")
            print(f"  Mean: {statistics.mean(successful_times)*1000:.2f} ms")
            print(f"  Median: {statistics.median(successful_times)*1000:.2f} ms")
            if len(successful_times) > 1:
                print(f"  Std Dev: {statistics.stdev(successful_times)*1000:.2f} ms")
            
            # Percentiles
            sorted_times = sorted(successful_times)
            p50 = sorted_times[int(len(sorted_times) * 0.50)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            print(f"\nPercentiles:")
            print(f"  p50: {p50*1000:.2f} ms")
            print(f"  p95: {p95*1000:.2f} ms")
            print(f"  p99: {p99*1000:.2f} ms")
            
            # Performance assessment
            print(f"\n🎯 Performance Assessment:")
            if p95 * 1000 < 200:
                print(f"  ✅ Excellent - p95 response time under 200ms target")
            elif p95 * 1000 < 500:
                print(f"  ⚠️  Good - p95 response time under 500ms")
            else:
                print(f"  ❌ Needs Improvement - p95 response time over 500ms")
        
        # Errors
        errors = [r for r in self.results if r["error"]]
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            error_types = {}
            for r in errors:
                error = r["error"] or "Unknown"
                error_types[error] = error_types.get(error, 0) + 1
            for error, count in error_types.items():
                print(f"  {error}: {count}")
        
        print("=" * 60)
        
        # Export results to JSON
        results_file = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "total_requests": total,
                "successful": successful,
                "failed": failed,
                "duration": total_duration,
                "throughput": throughput,
                "response_times": {
                    "min_ms": min(successful_times) * 1000 if successful_times else 0,
                    "max_ms": max(successful_times) * 1000 if successful_times else 0,
                    "mean_ms": statistics.mean(successful_times) * 1000 if successful_times else 0,
                    "p50_ms": p50 * 1000 if successful_times else 0,
                    "p95_ms": p95 * 1000 if successful_times else 0,
                    "p99_ms": p99 * 1000 if successful_times else 0,
                }
            }, f, indent=2)
        print(f"\n📄 Results saved to: {results_file}")


async def run_comprehensive_test(base_url: str):
    """Run comprehensive load tests on multiple endpoints"""
    print("🚀 Running Comprehensive Load Tests...")
    
    endpoints = [
        ("/health", "GET", 50, 500),  # endpoint, method, concurrent, total
        ("/api/health", "GET", 50, 500),
        ("/api/bots", "GET", 20, 200),
        ("/api/integrations/status", "GET", 20, 200),
    ]
    
    all_passed = True
    
    for endpoint, method, concurrent, total in endpoints:
        tester = LoadTester(base_url)
        await tester.run_load_test(
            endpoint=endpoint,
            method=method,
            concurrent_requests=concurrent,
            total_requests=total
        )
        tester.print_results()
        
        # Check if performance targets met
        successful = sum(1 for r in tester.results if r["success"])
        success_rate = successful / len(tester.results) * 100
        if success_rate < 95:
            all_passed = False
            print(f"❌ {endpoint}: Success rate {success_rate:.1f}% below 95% target")
        else:
            print(f"✅ {endpoint}: Success rate {success_rate:.1f}% meets target")
    
    return all_passed


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Load test CryptoOrchestrator API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--endpoint", default="/health", help="Endpoint to test")
    parser.add_argument("--method", default="GET", choices=["GET", "POST"], help="HTTP method")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--total", type=int, default=100, help="Total requests")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive test suite")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting load test at {datetime.now()}")
    
    if args.comprehensive:
        success = await run_comprehensive_test(args.url)
        return 0 if success else 1
    else:
        tester = LoadTester(args.url)
        print(f"   Target: {args.url}{args.endpoint}")
        
        await tester.run_load_test(
            endpoint=args.endpoint,
            method=args.method,
            concurrent_requests=args.concurrent,
            total_requests=args.total
        )
        
        tester.print_results()
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    import sys
    sys.exit(exit_code)

