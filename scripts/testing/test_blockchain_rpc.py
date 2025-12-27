#!/usr/bin/env python3
"""
Test blockchain RPC connections

Validates RPC provider connections for configured chains.
"""

import asyncio
import httpx
import sys
import os
from pathlib import Path
from typing import Dict, Optional

async def test_rpc_connection(rpc_url: str, chain_name: str) -> bool:
    """Test connection to a specific RPC provider"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test with eth_blockNumber (standard JSON-RPC call)
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            response = await client.post(rpc_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    block_number = int(data["result"], 16)
                    print(f"   ✅ {chain_name}: Connected (block #{block_number})")
                    return True
                else:
                    print(f"   ⚠️  {chain_name}: Response received but no result: {data}")
                    return False
            else:
                print(f"   ❌ {chain_name}: HTTP {response.status_code}")
                return False
    except httpx.TimeoutException:
        print(f"   ❌ {chain_name}: Connection timeout")
        return False
    except httpx.ConnectError:
        print(f"   ❌ {chain_name}: Cannot connect to {rpc_url}")
        return False
    except Exception as e:
        print(f"   ❌ {chain_name}: Error - {e}")
        return False

async def test_all_rpc_connections():
    """Test all configured RPC connections"""
    print("="*80)
    print("BLOCKCHAIN RPC CONNECTION TEST")
    print("="*80)
    
    # Get RPC URLs from environment
    rpc_configs = {
        "Ethereum": os.getenv("ETHEREUM_RPC_URL") or os.getenv("ETH_RPC_URL"),
        "Base": os.getenv("BASE_RPC_URL"),
        "Arbitrum": os.getenv("ARBITRUM_RPC_URL") or os.getenv("ARB_RPC_URL"),
        "Polygon": os.getenv("POLYGON_RPC_URL"),
        "Optimism": os.getenv("OPTIMISM_RPC_URL"),
        "Avalanche": os.getenv("AVALANCHE_RPC_URL"),
        "BNB Chain": os.getenv("BNB_RPC_URL") or os.getenv("BSC_RPC_URL"),
    }
    
    print("\nTesting RPC connections...")
    print("Note: RPC URLs should be configured in .env file")
    
    results = {}
    for chain_name, rpc_url in rpc_configs.items():
        if rpc_url:
            print(f"\n{chain_name}: {rpc_url[:50]}...")
            results[chain_name] = await test_rpc_connection(rpc_url, chain_name)
        else:
            print(f"\n{chain_name}: ⚠️  Not configured (skipped)")
            results[chain_name] = None
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    connected = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    print(f"\nConnected: {connected}/{total} configured chains")
    
    if connected == 0 and total == 0:
        print("\n⚠️  No RPC URLs configured in .env file")
        print("   Add RPC URLs to .env:")
        print("   ETHEREUM_RPC_URL=https://...")
        print("   BASE_RPC_URL=https://...")
        print("   etc.")
    
    return connected > 0 or total == 0

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_all_rpc_connections())
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
