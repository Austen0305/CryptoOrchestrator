#!/usr/bin/env python3
"""
Test Registration Without Shim
Tests the registration endpoint with shim disabled to verify fixes work
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"


async def test_registration(
    email: str, password: str, username: str, timeout: float = 10.0
) -> Dict[str, Any]:
    """Test a single registration request"""
    registration_data = {
        "email": email,
        "password": password,
        "username": username,
        "name": "Test User",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        start_time = time.time()
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
            )

            elapsed = time.time() - start_time

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "response": response.json() if response.status_code == 200 else response.text[:200],
            }
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "status_code": 0,
                "elapsed_time": elapsed,
                "error": "timeout",
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "status_code": 0,
                "elapsed_time": elapsed,
                "error": str(e),
            }


async def run_registration_tests(count: int = 10) -> List[Dict[str, Any]]:
    """Run multiple registration tests"""
    results = []
    
    print(f"\n{'='*60}")
    print(f"Running {count} Registration Tests")
    print(f"{'='*60}\n")
    
    for i in range(count):
        timestamp = int(time.time() * 1000) + i
        email = f"test{timestamp}@example.com"
        password = "SecurePass123!"
        username = f"testuser{timestamp}"
        
        print(f"Test {i+1}/{count}: {email[:30]}...", end=" ", flush=True)
        
        result = await test_registration(email, password, username)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {result['elapsed_time']:.3f}s")
        else:
            print(f"❌ {result.get('error', 'failed')} ({result['elapsed_time']:.3f}s)")
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    return results


async def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze test results"""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        avg_time = sum(r["elapsed_time"] for r in successful) / len(successful)
        min_time = min(r["elapsed_time"] for r in successful)
        max_time = max(r["elapsed_time"] for r in successful)
    else:
        avg_time = min_time = max_time = 0
    
    return {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(results) * 100 if results else 0,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "timeouts": len([r for r in failed if r.get("error") == "timeout"]),
    }


async def main():
    """Main test function"""
    print("Registration Test (Without Shim)")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: This test assumes the registration shim is")
    print("   temporarily disabled in server_fastapi/main.py")
    print()
    print("To disable shim:")
    print("  1. Comment out the @app.middleware('http') decorator")
    print("  2. Comment out the registration_shim function")
    print("  3. Restart the server")
    print()
    
    input("Press Enter to continue (or Ctrl+C to cancel)...")
    print()
    
    # Run tests
    results = await run_registration_tests(count=10)
    
    # Analyze results
    stats = await analyze_results(results)
    
    # Print summary
    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total Tests: {stats['total']}")
    print(f"Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"Failed: {stats['failed']}")
    print(f"Timeouts: {stats['timeouts']}")
    print()
    if stats['successful'] > 0:
        print("Response Times:")
        print(f"  Average: {stats['avg_time']:.3f}s")
        print(f"  Minimum: {stats['min_time']:.3f}s")
        print(f"  Maximum: {stats['max_time']:.3f}s")
    print()
    
    # Recommendations
    if stats['success_rate'] == 100 and stats['max_time'] < 2.0:
        print("✅ SUCCESS: All tests passed, response times acceptable")
        print("   The registration shim can likely be removed!")
    elif stats['success_rate'] >= 90:
        print("⚠️  WARNING: Most tests passed, but some failed")
        print("   Investigate failures before removing shim")
    elif stats['timeouts'] > 0:
        print("❌ FAILURE: Timeouts detected - middleware hang still present")
        print("   Do not remove shim yet - investigate further")
    else:
        print("❌ FAILURE: High failure rate")
        print("   Do not remove shim yet - investigate failures")
    
    print()
    print("Next Steps:")
    print("1. If all tests pass: Remove registration shim")
    print("2. If timeouts occur: Enable profiling and investigate")
    print("3. If failures occur: Check error messages and fix issues")


if __name__ == "__main__":
    asyncio.run(main())
