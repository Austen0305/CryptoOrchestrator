#!/usr/bin/env python3
"""
Automated Health Monitor
Continuously monitors application health and sends alerts on failures.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import sys

class HealthMonitor:
    """Monitor application health endpoints continuously."""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 interval: int = 60, alert_threshold: int = 3):
        self.base_url = base_url
        self.interval = interval  # Check interval in seconds
        self.alert_threshold = alert_threshold  # Failures before alert
        self.health_history = []
        self.history_file = Path("health_history.json")
        self.consecutive_failures = {}
        self.load_history()
        
    def load_history(self):
        """Load health check history."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    self.health_history = json.load(f)
                    # Keep last 1000 checks
                    self.health_history = self.health_history[-1000:]
            except:
                self.health_history = []
    
    def save_history(self):
        """Save health check history."""
        with open(self.history_file, 'w') as f:
            json.dump(self.health_history, f, indent=2)
    
    async def check_endpoint(self, session: aiohttp.ClientSession, 
                            endpoint: str, name: str) -> Dict:
        """Check a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        start = time.time()
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                duration = (time.time() - start) * 1000  # ms
                
                return {
                    "name": name,
                    "endpoint": endpoint,
                    "status": "healthy" if resp.status == 200 else "unhealthy",
                    "status_code": resp.status,
                    "response_time_ms": round(duration, 2),
                    "timestamp": datetime.now().isoformat(),
                    "error": None
                }
        except Exception as e:
            duration = (time.time() - start) * 1000
            return {
                "name": name,
                "endpoint": endpoint,
                "status": "unhealthy",
                "status_code": 0,
                "response_time_ms": round(duration, 2),
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def run_health_checks(self) -> Dict:
        """Run all health checks."""
        endpoints = [
            ("/health", "Health Check"),
            ("/api/integrations/health", "Integrations Health"),
            ("/api/analytics/health", "Analytics Health"),
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.check_endpoint(session, ep, name) for ep, name in endpoints]
            results = await asyncio.gather(*tasks)
        
        overall_status = "healthy" if all(r["status"] == "healthy" for r in results) else "unhealthy"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "checks": results
        }
    
    def check_alert_condition(self, check_name: str, status: str) -> bool:
        """Check if alert should be triggered."""
        if status == "unhealthy":
            self.consecutive_failures[check_name] = self.consecutive_failures.get(check_name, 0) + 1
            if self.consecutive_failures[check_name] >= self.alert_threshold:
                return True
        else:
            self.consecutive_failures[check_name] = 0
        
        return False
    
    def send_alert(self, check_name: str, check_data: Dict):
        """Send alert (print to console for now)."""
        print("\n" + "=" * 80)
        print(f"🚨 ALERT: {check_name} is UNHEALTHY")
        print(f"Consecutive failures: {self.consecutive_failures[check_name]}")
        print(f"Endpoint: {check_data['endpoint']}")
        print(f"Status Code: {check_data['status_code']}")
        print(f"Error: {check_data.get('error', 'N/A')}")
        print(f"Time: {check_data['timestamp']}")
        print("=" * 80 + "\n")
    
    def print_status(self, health_data: Dict):
        """Print current health status."""
        print(f"\n[{health_data['timestamp']}] Overall Status: {health_data['overall_status'].upper()}")
        
        for check in health_data['checks']:
            status_icon = "✅" if check['status'] == "healthy" else "❌"
            print(f"  {status_icon} {check['name']}: {check['status']} "
                  f"({check['response_time_ms']:.2f}ms)")
            
            if check['error']:
                print(f"     Error: {check['error']}")
    
    async def monitor_loop(self, duration: Optional[int] = None):
        """Main monitoring loop."""
        print(f"🔍 Starting Health Monitor")
        print(f"Base URL: {self.base_url}")
        print(f"Check Interval: {self.interval}s")
        print(f"Alert Threshold: {self.alert_threshold} consecutive failures")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            while True:
                # Run health checks
                health_data = await self.run_health_checks()
                
                # Print status
                self.print_status(health_data)
                
                # Check for alerts
                for check in health_data['checks']:
                    if self.check_alert_condition(check['name'], check['status']):
                        self.send_alert(check['name'], check)
                
                # Save to history
                self.health_history.append(health_data)
                self.save_history()
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    print(f"\n✅ Monitoring duration complete ({duration}s)")
                    break
                
                # Wait for next check
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
        finally:
            self.generate_summary()
    
    def generate_summary(self):
        """Generate monitoring summary."""
        if not self.health_history:
            return
        
        print("\n" + "=" * 80)
        print("MONITORING SUMMARY")
        print("=" * 80)
        
        total_checks = len(self.health_history)
        healthy_checks = sum(1 for h in self.health_history if h['overall_status'] == 'healthy')
        uptime_percent = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"Total Health Checks: {total_checks}")
        print(f"Healthy: {healthy_checks}")
        print(f"Unhealthy: {total_checks - healthy_checks}")
        print(f"Uptime: {uptime_percent:.2f}%")
        
        # Per-endpoint stats
        endpoint_stats = {}
        for health in self.health_history:
            for check in health['checks']:
                name = check['name']
                if name not in endpoint_stats:
                    endpoint_stats[name] = {'total': 0, 'healthy': 0, 'response_times': []}
                
                endpoint_stats[name]['total'] += 1
                if check['status'] == 'healthy':
                    endpoint_stats[name]['healthy'] += 1
                endpoint_stats[name]['response_times'].append(check['response_time_ms'])
        
        print("\nPer-Endpoint Statistics:")
        for name, stats in endpoint_stats.items():
            uptime = (stats['healthy'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_response = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            
            print(f"  {name}:")
            print(f"    Uptime: {uptime:.2f}%")
            print(f"    Avg Response Time: {avg_response:.2f}ms")
        
        print("=" * 80)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor application health continuously")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to monitor")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--threshold", type=int, default=3, help="Alert after N consecutive failures")
    parser.add_argument("--duration", type=int, help="Run for N seconds (default: infinite)")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(
        base_url=args.url,
        interval=args.interval,
        alert_threshold=args.threshold
    )
    
    asyncio.run(monitor.monitor_loop(duration=args.duration))

if __name__ == "__main__":
    main()
