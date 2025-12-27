#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Health Check Script
Checks all services, endpoints, and dependencies
"""

import os
import sys
import asyncio
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import httpx
    import aiohttp
except ImportError:
    print("❌ httpx or aiohttp not installed. Install with: pip install httpx aiohttp")
    sys.exit(1)

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


async def check_url(url: str, timeout: int = 5) -> Tuple[bool, Optional[Dict]]:
    """Check if URL is accessible"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.status_code < 500, {
                "status_code": response.status_code,
                "url": url
            }
    except Exception as e:
        return False, {"error": str(e), "url": url}


async def check_backend_health() -> bool:
    """Check backend health endpoints"""
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    print("\n🔍 Checking Backend Health...")
    print("-" * 60)
    
    endpoints = [
        f"{base_url}/health",
        f"{base_url}/healthz",
        f"{base_url}/api/health",
        f"{base_url}/api/health/aggregated",
    ]
    
    all_healthy = True
    for endpoint in endpoints:
        healthy, result = await check_url(endpoint)
        if healthy:
            print(f"  ✅ {endpoint} - Status: {result.get('status_code', 'OK')}")
        else:
            print(f"  ❌ {endpoint} - {result.get('error', 'Failed')}")
            all_healthy = False
    
    return all_healthy


async def check_frontend() -> bool:
    """Check frontend accessibility"""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    print("\n🔍 Checking Frontend...")
    print("-" * 60)
    
    healthy, result = await check_url(frontend_url, timeout=10)
    if healthy:
        print(f"  ✅ Frontend accessible at {frontend_url}")
    else:
        print(f"  ❌ Frontend not accessible: {result.get('error', 'Failed')}")
    
    return healthy


async def check_database_connection() -> bool:
    """Check database connection"""
    print("\n🔍 Checking Database Connection...")
    print("-" * 60)
    
    try:
        # Try to import and test database connection
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from server_fastapi.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            print("  ✅ Database connection successful")
            return True
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False


async def check_redis_connection() -> bool:
    """Check Redis connection (optional)"""
    redis_url = os.getenv("REDIS_URL")
    
    print("\n🔍 Checking Redis Connection...")
    print("-" * 60)
    
    if not redis_url:
        print("  ⚠️  Redis not configured (optional)")
        return True
    
    try:
        import redis.asyncio as redis
        
        client = redis.from_url(redis_url)
        await client.ping()
        await client.aclose()  # Use aclose() instead of deprecated close()
        print(f"  ✅ Redis connection successful ({redis_url.split('@')[-1] if '@' in redis_url else redis_url})")
        return True
    except ImportError:
        print("  ⚠️  redis package not installed (optional)")
        return True
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        return False


async def check_api_endpoints() -> bool:
    """Check critical API endpoints"""
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    print("\n🔍 Checking Critical API Endpoints...")
    print("-" * 60)
    
    # Critical endpoints that should respond (may require auth)
    endpoints = [
        f"{base_url}/api/health",
        f"{base_url}/docs",  # OpenAPI docs
        f"{base_url}/api/status",
    ]
    
    passed = 0
    failed = 0
    
    for endpoint in endpoints:
        healthy, result = await check_url(endpoint)
        if healthy:
            print(f"  ✅ {endpoint.split('/')[-1]}")
            passed += 1
        else:
            print(f"  ❌ {endpoint.split('/')[-1]}: {result.get('error', 'Failed')}")
            failed += 1
    
    print(f"\n  Summary: {passed} passed, {failed} failed")
    return failed == 0


async def check_websocket() -> bool:
    """Check WebSocket connectivity"""
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    
    print("\n🔍 Checking WebSocket Connection...")
    print("-" * 60)
    
    try:
        import websockets
        
        async with websockets.connect(ws_url, timeout=5) as ws:
            # Send ping
            await ws.send('{"action": "ping"}')
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"  ✅ WebSocket connection successful")
            return True
    except ImportError:
        print("  ⚠️  websockets package not installed, skipping WebSocket check")
        return True
    except Exception as e:
        print(f"  ❌ WebSocket connection failed: {e}")
        return False


async def comprehensive_health_check() -> bool:
    """Run comprehensive health check"""
    print("🏥 CryptoOrchestrator Comprehensive Health Check")
    print("=" * 60)
    
    results = {
        "backend": False,
        "frontend": False,
        "database": False,
        "redis": False,
        "api_endpoints": False,
        "websocket": False,
    }
    
    # Run all checks
    results["backend"] = await check_backend_health()
    results["frontend"] = await check_frontend()
    results["database"] = await check_database_connection()
    results["redis"] = await check_redis_connection()
    results["api_endpoints"] = await check_api_endpoints()
    results["websocket"] = await check_websocket()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Health Check Summary")
    print("-" * 60)
    
    for check_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name.replace('_', ' ').title()}")
    
    all_healthy = all(results.values())
    
    if all_healthy:
        print("\n✅ All health checks passed!")
    else:
        print("\n❌ Some health checks failed")
        print("\n💡 Troubleshooting:")
        print("  - Ensure all services are running")
        print("  - Check service logs for errors")
        print("  - Verify environment variables are set correctly")
    
    return all_healthy


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive health check for CryptoOrchestrator")
    parser.add_argument(
        "--backend-url",
        default=os.getenv("BACKEND_URL", "http://localhost:8000"),
        help="Backend URL"
    )
    parser.add_argument(
        "--frontend-url",
        default=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        help="Frontend URL"
    )
    
    args = parser.parse_args()
    
    os.environ["BACKEND_URL"] = args.backend_url
    os.environ["FRONTEND_URL"] = args.frontend_url
    
    success = asyncio.run(comprehensive_health_check())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
