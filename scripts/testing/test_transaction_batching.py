"""
Test Transaction Batching
Verify transaction batching works correctly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_transaction_batching():
    """Test transaction batching functionality"""
    try:
        from server_fastapi.services.blockchain.transaction_batcher import get_transaction_batcher
        
        batcher = get_transaction_batcher()
        
        print("\n" + "="*80)
        print("TRANSACTION BATCHING TEST")
        print("="*80)
        
        # Test 1: Add swaps to batch
        print("\n1. Adding swaps to batch...")
        
        swap_results = []
        for i in range(5):
            result = await batcher.add_swap(
                user_id=1,
                sell_token="0xA0b86991c6218b36c1d19D4a2e9Eb0c3606eB48",  # USDC
                buy_token="0x0000000000000000000000000000000000000000",  # ETH
                sell_amount=str(1000 * 10**6),  # 1000 USDC (6 decimals)
                chain_id=1,
                slippage_percentage=0.5,
                swap_id=f"test_swap_{i}",
                force_immediate=False,
            )
            swap_results.append(result)
            print(f"  Swap {i+1}: {result.get('status', 'unknown')}")
        
        # Test 2: Check pending count
        pending_count = batcher.get_pending_count(chain_id=1)
        print(f"\n2. Pending swaps: {pending_count}")
        
        # Test 3: Test gas savings estimation
        print("\n3. Gas savings estimation:")
        for batch_size in [2, 5, 10]:
            savings = batcher._estimate_gas_savings(batch_size)
            print(f"  {batch_size} swaps: {savings*100:.1f}% savings")
        
        # Test 4: Force immediate execution
        print("\n4. Testing force immediate execution...")
        immediate_result = await batcher.add_swap(
            user_id=1,
            sell_token="0xA0b86991c6218b36c1d19D4a2e9Eb0c3606eB48",
            buy_token="0x0000000000000000000000000000000000000000",
            sell_amount=str(1000 * 10**6),
            chain_id=1,
            slippage_percentage=0.5,
            swap_id="test_immediate",
            force_immediate=True,
        )
        print(f"  Immediate swap status: {immediate_result.get('status', 'unknown')}")
        
        # Test 5: Flush pending batches
        print("\n5. Flushing pending batches...")
        flush_result = await batcher.flush_pending(chain_id=1)
        print(f"  Flush result: {flush_result.get('status', 'unknown')}")
        
        print("\n" + "="*80)
        print("✅ TRANSACTION BATCHING TEST COMPLETE")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Transaction batching test failed: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}\n")
        return False


async def main():
    """Main test function"""
    success = await test_transaction_batching()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
