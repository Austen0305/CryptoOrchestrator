#!/usr/bin/env python3
"""
Performance Monitoring and Regression Detection
Tracks API performance metrics and alerts on regressions
"""
import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import Dict, List
import argparse
import os


class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.baseline_file = "performance_baseline.json"
        self.history_file = "performance_history.json"
    
    async def measure_endpoint(self, session: aiohttp.ClientSession, 
                               endpoint: str, method: str = "GET",
                               iterations: int = 10) -> Dict:
        """Measure endpoint performance"""
        response_times = []
        errors = 0
        
        for _ in range(iterations):
            start = time.time()
            try:
                if method == "GET":
                    async with session.get(f"{self.base_url}{endpoint}") as resp:
                        await resp.text()
                        status = resp.status
                elif method == "POST":
                    async with session.post(f"{self.base_url}{endpoint}", json={}) as resp:
                        await resp.text()
                        status = resp.status
                
                elapsed = (time.time() - start) * 1000  # Convert to ms
                
                if status < 500:  # Count only non-server-error responses
                    response_times.append(elapsed)
                else:
                    errors += 1
            except Exception as e:
                errors += 1
        
        if response_times:
            return {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'min': round(min(response_times), 2),
                'max': round(max(response_times), 2),
                'mean': round(statistics.mean(response_times), 2),
                'median': round(statistics.median(response_times), 2),
                'p95': round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 1 else round(response_times[0], 2),
                'p99': round(statistics.quantiles(response_times, n=100)[98], 2) if len(response_times) > 1 else round(response_times[0], 2),
                'errors': errors,
                'success_rate': round((iterations - errors) / iterations * 100, 1)
            }
        else:
            return {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'error': 'All requests failed',
                'errors': errors
            }
    
    async def run_performance_suite(self) -> Dict:
        """Run complete performance test suite"""
        print("🏃 Running Performance Test Suite...")
        print(f"   Target: {self.base_url}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        endpoints = [
            ('/health', 'GET'),
            ('/api/health', 'GET'),
            ('/api/bots', 'GET'),
            ('/api/integrations/status', 'GET'),
            ('/api/analytics/summary', 'GET'),
        ]
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'endpoints': {}
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints:
                print(f"\n   Testing {method} {endpoint}...")
                metric = await self.measure_endpoint(session, endpoint, method, iterations=20)
                results['endpoints'][endpoint] = metric
                
                if 'error' not in metric:
                    print(f"      ✓ p50: {metric['median']}ms | p95: {metric['p95']}ms | p99: {metric['p99']}ms")
                else:
                    print(f"      ✗ {metric['error']}")
        
        return results
    
    def save_baseline(self, results: Dict):
        """Save performance baseline"""
        with open(self.baseline_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Baseline saved to {self.baseline_file}")
    
    def load_baseline(self) -> Dict:
        """Load performance baseline"""
        if os.path.exists(self.baseline_file):
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_to_history(self, results: Dict):
        """Append results to history"""
        history = []
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        
        history.append(results)
        
        # Keep last 100 runs
        history = history[-100:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def compare_with_baseline(self, current: Dict, baseline: Dict, threshold: float = 1.2):
        """Compare current results with baseline"""
        print("\n" + "=" * 60)
        print("📊 Performance Regression Analysis")
        print("=" * 60)
        
        regressions = []
        improvements = []
        
        for endpoint, current_metrics in current['endpoints'].items():
            if 'error' in current_metrics:
                continue
            
            baseline_metrics = baseline['endpoints'].get(endpoint)
            if not baseline_metrics or 'error' in baseline_metrics:
                print(f"\n{endpoint}: ⚠️  No baseline (NEW)")
                continue
            
            current_p95 = current_metrics['p95']
            baseline_p95 = baseline_metrics['p95']
            
            change_pct = ((current_p95 - baseline_p95) / baseline_p95) * 100
            
            print(f"\n{endpoint}:")
            print(f"   p95: {current_p95}ms (baseline: {baseline_p95}ms)")
            print(f"   Change: {change_pct:+.1f}%")
            
            if current_p95 > baseline_p95 * threshold:
                print(f"   ❌ REGRESSION: {change_pct:.1f}% slower than baseline!")
                regressions.append({
                    'endpoint': endpoint,
                    'current_p95': current_p95,
                    'baseline_p95': baseline_p95,
                    'change_pct': change_pct
                })
            elif current_p95 < baseline_p95 * 0.8:
                print(f"   ✅ IMPROVEMENT: {-change_pct:.1f}% faster than baseline")
                improvements.append({
                    'endpoint': endpoint,
                    'current_p95': current_p95,
                    'baseline_p95': baseline_p95,
                    'change_pct': change_pct
                })
            else:
                print(f"   ✓ OK: Within acceptable range")
        
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"   Regressions: {len(regressions)}")
        print(f"   Improvements: {len(improvements)}")
        print(f"   Threshold: {(threshold - 1) * 100}% slower")
        print("=" * 60)
        
        if regressions:
            print("\n⚠️  PERFORMANCE REGRESSIONS DETECTED!")
            print("These endpoints are significantly slower:")
            for r in regressions:
                print(f"   - {r['endpoint']}: {r['current_p95']}ms (was {r['baseline_p95']}ms)")
            return False
        else:
            print("\n✅ No performance regressions detected")
            return True
    
    def generate_report(self, results: Dict):
        """Generate performance report"""
        print("\n" + "=" * 60)
        print("📈 Performance Report")
        print("=" * 60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Base URL: {results['base_url']}")
        print("\nEndpoint Performance:")
        
        for endpoint, metrics in results['endpoints'].items():
            if 'error' in metrics:
                print(f"\n{endpoint}: ❌ {metrics['error']}")
            else:
                print(f"\n{endpoint}:")
                print(f"   Mean: {metrics['mean']}ms")
                print(f"   Median (p50): {metrics['median']}ms")
                print(f"   p95: {metrics['p95']}ms")
                print(f"   p99: {metrics['p99']}ms")
                print(f"   Success Rate: {metrics['success_rate']}%")
        
        print("=" * 60)


async def main():
    """Main CLI"""
    parser = argparse.ArgumentParser(description='Monitor API performance and detect regressions')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='Base URL')
    parser.add_argument('--set-baseline', action='store_true', help='Set current as baseline')
    parser.add_argument('--compare', action='store_true', help='Compare with baseline')
    parser.add_argument('--threshold', type=float, default=1.2, help='Regression threshold (default: 1.2 = 20% slower)')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(base_url=args.url)
    
    # Run performance tests
    results = await monitor.run_performance_suite()
    
    # Save to history
    monitor.save_to_history(results)
    
    # Set baseline if requested
    if args.set_baseline:
        monitor.save_baseline(results)
    
    # Compare with baseline if requested
    if args.compare:
        baseline = monitor.load_baseline()
        if baseline:
            passed = monitor.compare_with_baseline(results, baseline, args.threshold)
            if not passed:
                exit(1)
        else:
            print("\n⚠️  No baseline found. Run with --set-baseline first.")
    
    # Generate report if requested
    if args.report:
        monitor.generate_report(results)
    
    print("\n✅ Performance monitoring complete!")
    print(f"   Results saved to: {monitor.history_file}")
    if os.path.exists(monitor.baseline_file):
        print(f"   Baseline: {monitor.baseline_file}")


if __name__ == "__main__":
    asyncio.run(main())
