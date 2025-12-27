#!/usr/bin/env python3
"""
Test Authentication Endpoints
Tests user registration, login, logout, and token refresh
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"[OK] Health check: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {data.get('status', 'unknown')}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Health check failed: {e}")
            return False


async def test_register_user(email: str = "test@example.com", password: str = "Test123!@#Password"):
    """Test user registration"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            payload = {
                "email": email,
                "password": password,
                "username": "testuser",
                "full_name": "Test User"
            }
            response = await client.post(f"{BASE_URL}/api/auth/register", json=payload)
            print(f"\n📝 Registration test:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"   [OK] User registered: {data.get('email', 'unknown')}")
                return data
            else:
                print(f"   Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"   [ERROR] Registration failed: {e}")
            return None


async def test_login(email: str = "test@example.com", password: str = "Test123!@#Password"):
    """Test user login"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            payload = {
                "email": email,
                "password": password
            }
            response = await client.post(f"{BASE_URL}/api/auth/login", json=payload)
            print(f"\n🔐 Login test:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token') or data.get('token')
                if token:
                    print(f"   ✅ Login successful, token received")
                    return token, data
                else:
                    print(f"   ⚠️ Login successful but no token in response")
                    print(f"   Response keys: {list(data.keys())}")
                    return None, data
            else:
                print(f"   Response: {response.text[:200]}")
                return None, None
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            return None, None


async def test_get_current_user(token: str):
    """Test getting current user info"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{BASE_URL}/api/auth/me", headers=headers)
            print(f"\n👤 Get current user test:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] User info retrieved: {data.get('email', 'unknown')}")
                return data
            else:
                print(f"   Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"   [ERROR] Get user failed: {e}")
            return None


async def test_logout(token: str):
    """Test user logout"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(f"{BASE_URL}/api/auth/logout", headers=headers)
            print(f"\n🚪 Logout test:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 204]:
                print(f"   [OK] Logout successful")
                return True
            else:
                print(f"   Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"   [ERROR] Logout failed: {e}")
            return False


async def main():
    """Run all authentication tests"""
    print("=" * 60)
    print("Authentication Endpoints Testing")
    print("=" * 60)
    
    # Test health check first
    health_ok = await test_health_check()
    if not health_ok:
        print("\n[ERROR] Server is not running. Please start the backend server first:")
        print("   npm run dev:fastapi")
        print("   or")
        print("   python -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Test registration
    user_data = await test_register_user()
    
    # Test login
    token, login_data = await test_login()
    
    if token:
        # Test get current user
        await test_get_current_user(token)
        
        # Test logout
        await test_logout(token)
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
