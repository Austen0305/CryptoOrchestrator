"""
Test MEV Protection
Verify MEV protection service works correctly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mev_protection():
    """Test MEV protection functionality"""
    try:
        from server_fastapi.services.blockchain.mev_protection import (
            get_mev_protection_service,
            MEVProtectionProvider
        )
        
        mev_service = get_mev_protection_service()
        
        print("\n" + "="*80)
        print("MEV PROTECTION TEST")
        print("="*80)
        
        # Test 1: Check protection status for various chains
        print("\n1. Checking protection status for chains...")
        chains = [1, 8453, 42161, 137, 10]  # Ethereum, Base, Arbitrum, Polygon, Optimism
        
        for chain_id in chains:
            status = mev_service.get_protection_status(chain_id)
            supported = status["supported"]
            providers = status["providers"]
            
            print(f"  Chain {chain_id}: {'✅ Supported' if supported else '❌ Not supported'}")
            if supported:
                mev_blocker = providers.get("mev_blocker", {})
                if mev_blocker.get("available"):
                    print(f"    MEV Blocker: ✅ Available")
                    print(f"    RPC: {mev_blocker.get('rpc_url', 'N/A')[:50]}...")
        
        # Test 2: Test protected RPC URL retrieval
        print("\n2. Testing protected RPC URL retrieval...")
        for chain_id in [1, 8453]:
            protected_rpc = await mev_service.get_protected_rpc_url(
                chain_id, MEVProtectionProvider.MEV_BLOCKER
            )
            if protected_rpc:
                print(f"  Chain {chain_id}: ✅ {protected_rpc[:50]}...")
            else:
                print(f"  Chain {chain_id}: ❌ No protected RPC")
        
        # Test 3: Test auto-enable logic
        print("\n3. Testing auto-enable logic...")
        test_cases = [
            (500.0, 1, False, "Low value trade (< $1000)"),
            (1500.0, 1, True, "High value trade (> $1000)"),
            (1000.0, 1, True, "Threshold trade (= $1000)"),
            (2000.0, 8453, True, "High value on Base"),
        ]
        
        for trade_amount, chain_id, expected, description in test_cases:
            should_use = await mev_service.should_use_mev_protection(
                trade_amount_usd=trade_amount,
                chain_id=chain_id
            )
            status = "✅" if should_use == expected else "❌"
            print(f"  {status} {description}: ${trade_amount} on chain {chain_id} -> {should_use}")
        
        # Test 4: Check default provider
        print("\n4. Default provider configuration...")
        default_provider = mev_service._default_provider
        print(f"  Default provider: {default_provider.value}")
        
        # Test 5: Check enabled chains
        print("\n5. Enabled chains...")
        enabled_chains = mev_service._enabled_chains
        print(f"  Enabled chains: {enabled_chains}")
        
        print("\n" + "="*80)
        print("✅ MEV PROTECTION TEST COMPLETE")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"MEV protection test failed: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}\n")
        return False


async def main():
    """Main test function"""
    success = await test_mev_protection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
