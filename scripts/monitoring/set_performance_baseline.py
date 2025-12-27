#!/usr/bin/env python3
"""
Performance Baseline Script
Sets performance baseline for regression detection.

Usage:
    python scripts/monitoring/set_performance_baseline.py
    python scripts/monitoring/set_performance_baseline.py --endpoint /api/bots
    python scripts/monitoring/set_performance_baseline.py --force
"""

import asyncio
import argparse
import sys
import json
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # If reconfiguration fails, continue without it
        pass
try:
    import httpx
except ImportError:
    print("ERROR: httpx package not installed.")
    print("   Install with: pip install httpx>=0.25.2")
    print("   Or install all requirements: pip install -r requirements.txt")
    sys.exit(1)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class PerformanceBaseline:
    """Sets performance baseline for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.baseline_file = project_root / "test-results" / "performance_baseline.json"
        self.baseline_file.parent.mkdir(exist_ok=True)
        
        # Endpoints to baseline
        self.endpoints = [
            {"path": "/api/bots", "method": "GET", "name": "Get Bots"},
            {"path": "/api/portfolio", "method": "GET", "name": "Get Portfolio"},
            {"path": "/api/trades", "method": "GET", "name": "Get Trades"},
            {"path": "/api/wallets", "method": "GET", "name": "Get Wallets"},
            {"path": "/api/health", "method": "GET", "name": "Health Check"},
        ]
    
    async def measure_endpoint(self, endpoint: Dict[str, str], iterations: int = 10) -> Dict[str, any]:
        """Measure endpoint performance."""
        url = f"{self.base_url}{endpoint['path']}"
        times = []
        errors = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                try:
                    start = asyncio.get_event_loop().time()
                    response = await client.request(
                        method=endpoint["method"],
                        url=url,
                        headers={"Content-Type": "application/json"}
                    )
                    elapsed = (asyncio.get_event_loop().time() - start) * 1000  # Convert to ms
                    
                    if response.status_code < 400:
                        times.append(elapsed)
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
                    print(f"  [WARN] Error on iteration {i+1}: {e}")
        
        if not times:
            return {
                "endpoint": endpoint["name"],
                "path": endpoint["path"],
                "method": endpoint["method"],
                "error": "All requests failed"
            }
        
        times.sort()
        return {
            "endpoint": endpoint["name"],
            "path": endpoint["path"],
            "method": endpoint["method"],
            "iterations": iterations,
            "successful": len(times),
            "errors": errors,
            "min": round(min(times), 2),
            "max": round(max(times), 2),
            "mean": round(sum(times) / len(times), 2),
            "median": round(times[len(times) // 2], 2),
            "p50": round(times[len(times) // 2], 2),
            "p95": round(times[int(len(times) * 0.95)], 2),
            "p99": round(times[int(len(times) * 0.99)] if len(times) > 1 else times[0], 2),
        }
    
    async def set_baseline(self, endpoint_filter: str = None, force: bool = False):
        """Set performance baseline for all endpoints."""
        print("\n[INFO] Setting Performance Baseline")
        print("=" * 60)
        
        # Load existing baseline
        existing_baseline = {}
        if self.baseline_file.exists() and not force:
            try:
                with open(self.baseline_file, "r") as f:
                    existing_baseline = json.load(f)
                print(f"[INFO] Existing baseline found: {existing_baseline.get('timestamp', 'unknown')}")
            except Exception as e:
                print(f"[WARN] Could not load existing baseline: {e}")
        
        # Filter endpoints if specified
        endpoints = self.endpoints
        if endpoint_filter:
            endpoints = [e for e in endpoints if endpoint_filter in e["path"]]
            if not endpoints:
                print(f"[ERROR] No endpoints match filter: {endpoint_filter}")
                return
        
        print(f"\n[INFO] Measuring {len(endpoints)} endpoint(s)...")
        
        baseline = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_url": self.base_url,
            "endpoints": {}
        }
        
        for endpoint in endpoints:
            print(f"\n[TEST] Measuring: {endpoint['name']} ({endpoint['path']})")
            result = await self.measure_endpoint(endpoint)
            
            if "error" in result:
                print(f"  [FAIL] {result['error']}")
            else:
                print(f"  [OK] Success: {result['successful']}/{result['iterations']}")
                print(f"     Mean: {result['mean']}ms | P95: {result['p95']}ms | P99: {result['p99']}ms")
                baseline["endpoints"][endpoint["path"]] = result
        
        # Save baseline
        with open(self.baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)
        
        print(f"\n[SAVED] Baseline saved to: {self.baseline_file}")
        print(f"[INFO] Baseline includes {len(baseline['endpoints'])} endpoint(s)")
        
        # Compare with existing if available
        if existing_baseline and existing_baseline.get("endpoints"):
            print("\n[COMPARE] Comparison with Previous Baseline:")
            print("-" * 60)
            for path, new_metrics in baseline["endpoints"].items():
                if path in existing_baseline["endpoints"]:
                    old_metrics = existing_baseline["endpoints"][path]
                    p95_diff = new_metrics["p95"] - old_metrics.get("p95", 0)
                    p95_change = (p95_diff / old_metrics.get("p95", 1)) * 100 if old_metrics.get("p95") else 0
                    
                    if abs(p95_change) > 10:  # 10% threshold
                        status = "[WARN]" if p95_change > 0 else "[OK]"
                        print(f"{status} {new_metrics['endpoint']}: P95 changed by {p95_change:+.1f}% ({p95_diff:+.1f}ms)")


async def main():
    parser = argparse.ArgumentParser(description="Set Performance Baseline")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API"
    )
    parser.add_argument(
        "--endpoint",
        help="Filter to specific endpoint path"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing baseline"
    )
    
    args = parser.parse_args()
    
    baseline = PerformanceBaseline(base_url=args.base_url)
    await baseline.set_baseline(endpoint_filter=args.endpoint, force=args.force)


if __name__ == "__main__":
    asyncio.run(main())
