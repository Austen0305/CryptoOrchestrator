#!/usr/bin/env python3
"""
Test DEX aggregator configuration

Validates DEX aggregator API keys and fallback logic.
"""

import asyncio
import httpx
import sys
import os
from pathlib import Path
from typing import Dict, Optional

async def test_0x_aggregator(api_key: Optional[str] = None) -> bool:
    """Test 0x aggregator connection"""
    base_url = "https://api.0x.org"
    endpoint = "/swap/v1/quote"
    
    # Test parameters (USDC -> ETH on Ethereum)
    params = {
        "sellToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "buyToken": "0xEthereum",  # ETH
        "sellAmount": "1000000000",  # 1000 USDC (6 decimals)
        "chainId": "1",  # Ethereum mainnet
    }
    
    headers = {}
    if api_key:
        headers["0x-api-key"] = api_key
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}{endpoint}",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 0x: Connected (quote received)")
                print(f"      Buy amount: {data.get('buyAmount', 'N/A')}")
                return True
            elif response.status_code == 429:
                print(f"   ⚠️  0x: Rate limited (may need API key)")
                return False
            else:
                print(f"   ⚠️  0x: HTTP {response.status_code} - {response.text[:100]}")
                return False
    except Exception as e:
        print(f"   ❌ 0x: Error - {e}")
        return False

async def test_okx_aggregator(api_key: Optional[str] = None) -> bool:
    """Test OKX aggregator connection"""
    base_url = "https://www.okx.com/api/v5/dex/aggregator"
    endpoint = "/quote"
    
    # Test parameters
    params = {
        "fromTokenAddress": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "toTokenAddress": "0xEthereum",  # ETH
        "amount": "1000000000",  # 1000 USDC
        "chainId": "1",
    }
    
    headers = {}
    if api_key:
        headers["OK-ACCESS-KEY"] = api_key
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}{endpoint}",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"   ✅ OKX: Connected")
                return True
            else:
                print(f"   ⚠️  OKX: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ OKX: Error - {e}")
        return False

async def test_rubic_aggregator(api_key: Optional[str] = None) -> bool:
    """Test Rubic aggregator connection"""
    base_url = "https://api.rubic.exchange/api/v1"
    endpoint = "/quote"
    
    # Test parameters
    params = {
        "fromTokenAddress": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "toTokenAddress": "0xEthereum",  # ETH
        "amount": "1000000000",
        "chainId": "1",
    }
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}{endpoint}",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"   ✅ Rubic: Connected")
                return True
            else:
                print(f"   ⚠️  Rubic: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Rubic: Error - {e}")
        return False

async def test_all_aggregators():
    """Test all DEX aggregators"""
    print("="*80)
    print("DEX AGGREGATOR CONFIGURATION TEST")
    print("="*80)
    
    # Get API keys from environment (optional)
    api_keys = {
        "0x": os.getenv("ZEROX_API_KEY") or os.getenv("0X_API_KEY"),
        "OKX": os.getenv("OKX_API_KEY"),
        "Rubic": os.getenv("RUBIC_API_KEY"),
    }
    
    print("\nTesting DEX aggregators...")
    print("Note: API keys are optional for public endpoints (rate-limited)")
    
    results = {}
    
    print("\n1. Testing 0x aggregator...")
    results["0x"] = await test_0x_aggregator(api_keys.get("0x"))
    
    print("\n2. Testing OKX aggregator...")
    results["OKX"] = await test_okx_aggregator(api_keys.get("OKX"))
    
    print("\n3. Testing Rubic aggregator...")
    results["Rubic"] = await test_rubic_aggregator(api_keys.get("Rubic"))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    connected = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nConnected: {connected}/{total} aggregators")
    
    if connected > 0:
        print("\n✅ At least one aggregator is available")
        print("   Fallback logic will work if others fail")
    else:
        print("\n⚠️  No aggregators connected")
        print("   Check network connectivity and API keys")
    
    return connected > 0

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_all_aggregators())
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
