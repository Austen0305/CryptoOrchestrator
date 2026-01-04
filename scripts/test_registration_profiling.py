#!/usr/bin/env python3
"""
Test Registration Endpoint with Profiling
Profiles the registration endpoint to identify middleware bottlenecks
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


async def test_registration_with_profiling() -> Dict[str, Any]:
    """Test registration endpoint and get profiling stats"""
    
    # Enable profiling first
    async with httpx.AsyncClient() as client:
        try:
            # Note: This requires authentication - for testing, we'll check if profiling is enabled
            # In production, you'd need to authenticate first
            print("⚠️  Note: Profiling endpoints require authentication")
            print("   Set ENABLE_MIDDLEWARE_PROFILING=true in .env to enable profiling")
        except Exception as e:
            print(f"Could not enable profiling via API: {e}")
            print("   Make sure to set ENABLE_MIDDLEWARE_PROFILING=true in environment")
    
    # Test registration
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "SecurePass123!"
    test_username = f"testuser_{int(time.time())}"
    
    registration_data = {
        "email": test_email,
        "password": test_password,
        "username": test_username,
        "name": "Test User",
    }
    
    print(f"\n{'='*60}")
    print("Testing Registration Endpoint")
    print(f"{'='*60}")
    print(f"Email: {test_email}")
    print(f"URL: {BASE_URL}/api/auth/register")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
            )
            
            elapsed = time.time() - start_time
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Time: {elapsed:.3f}s")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Registration successful!")
                print(f"   User ID: {data.get('user', {}).get('id', 'N/A')}")
                print(f"   Token: {data.get('access_token', 'N/A')[:20]}...")
            else:
                print(f"❌ Registration failed")
                print(f"   Response: {response.text[:200]}")
            
            # Try to get profiling stats (if authenticated)
            try:
                # For testing, we'll just note that profiling should be checked manually
                print()
                print(f"{'='*60}")
                print("Profiling Analysis")
                print(f"{'='*60}")
                print("To view profiling stats:")
                print("  1. Set ENABLE_MIDDLEWARE_PROFILING=true in .env")
                print("  2. Restart the server")
                print("  3. Make registration requests")
                print("  4. View stats: GET /api/admin/profiling/stats")
                print()
                print("Or check server logs for profiling output")
            except Exception as e:
                print(f"Could not get profiling stats: {e}")
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "response_data": response.json() if response.status_code == 200 else None,
            }
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ Request timed out after {elapsed:.3f}s")
            print("   This indicates a middleware hang!")
            return {
                "success": False,
                "status_code": 0,
                "elapsed_time": elapsed,
                "error": "timeout",
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Request failed: {e}")
            return {
                "success": False,
                "status_code": 0,
                "elapsed_time": elapsed,
                "error": str(e),
            }


async def test_without_shim() -> Dict[str, Any]:
    """Test what happens if we bypass the shim (for comparison)"""
    print(f"\n{'='*60}")
    print("Testing Normal Registration Route (if shim removed)")
    print(f"{'='*60}")
    print("This test assumes the shim is temporarily disabled")
    print()
    
    # Same test as above
    return await test_registration_with_profiling()


async def main():
    """Main test function"""
    print("Registration Profiling Test")
    print("=" * 60)
    print()
    print("This script tests the registration endpoint to identify")
    print("middleware bottlenecks that might cause hangs.")
    print()
    
    # Test 1: With shim (current state)
    print("Test 1: Registration with shim middleware (current)")
    result1 = await test_registration_with_profiling()
    
    print()
    print("=" * 60)
    print("Recommendations:")
    print("=" * 60)
    print()
    
    if result1.get("elapsed_time", 0) > 5.0:
        print("⚠️  Registration took >5 seconds - potential middleware issue")
    elif result1.get("elapsed_time", 0) > 2.0:
        print("⚠️  Registration took >2 seconds - may indicate middleware delay")
    else:
        print("✅ Registration response time is acceptable")
    
    print()
    print("Next Steps:")
    print("1. Enable profiling: ENABLE_MIDDLEWARE_PROFILING=true")
    print("2. Test registration multiple times")
    print("3. Check profiling stats: GET /api/admin/profiling/stats")
    print("4. Identify slow middleware (>0.1s average)")
    print("5. Fix or disable problematic middleware")
    print("6. Remove registration shim once fixed")


if __name__ == "__main__":
    asyncio.run(main())
