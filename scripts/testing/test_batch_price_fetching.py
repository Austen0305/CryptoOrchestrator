"""
Test Batch Price Fetching
Verify batch price fetching works correctly
"""
import asyncio
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_batch_price_fetching():
    """Test batch price fetching functionality"""
    try:
        from server_fastapi.services.coingecko_service import CoinGeckoService
        
        coingecko = CoinGeckoService()
        
        print("\n" + "="*80)
        print("BATCH PRICE FETCHING TEST")
        print("="*80)
        
        # Test 1: Compare sequential vs batch fetching
        print("\n1. Performance comparison: Sequential vs Batch...")
        
        symbols = ["BTC/USD", "ETH/USD", "USDC/USD", "DAI/USD", "WBTC/USD"]
        
        # Sequential fetching
        print("  Sequential fetching...")
        start_time = time.time()
        sequential_prices = {}
        for symbol in symbols:
            price = await coingecko.get_price(symbol)
            sequential_prices[symbol] = price
        sequential_time = time.time() - start_time
        print(f"    Time: {sequential_time:.2f}s")
        print(f"    Prices fetched: {len([p for p in sequential_prices.values() if p is not None])}/{len(symbols)}")
        
        # Wait a bit to avoid rate limiting
        await asyncio.sleep(2)
        
        # Batch fetching
        print("  Batch fetching...")
        start_time = time.time()
        batch_prices = await coingecko.get_prices_batch(symbols)
        batch_time = time.time() - start_time
        print(f"    Time: {batch_time:.2f}s")
        print(f"    Prices fetched: {len([p for p in batch_prices.values() if p is not None])}/{len(symbols)}")
        
        # Calculate speedup
        if sequential_time > 0:
            speedup = sequential_time / batch_time if batch_time > 0 else float('inf')
            print(f"\n  Speedup: {speedup:.1f}x faster")
        
        # Test 2: Test with large symbol list (chunking)
        print("\n2. Testing chunking with large symbol list...")
        large_symbol_list = [f"TOKEN{i}/USD" for i in range(60)]  # 60 symbols (will be chunked)
        
        start_time = time.time()
        large_batch_prices = await coingecko.get_prices_batch(large_symbol_list)
        large_batch_time = time.time() - start_time
        
        print(f"  Fetched {len(large_symbol_list)} symbols in {large_batch_time:.2f}s")
        print(f"  Prices returned: {len([p for p in large_batch_prices.values() if p is not None])}")
        
        # Test 3: Test caching
        print("\n3. Testing caching...")
        cached_start = time.time()
        cached_prices = await coingecko.get_prices_batch(symbols[:3])  # Should use cache
        cached_time = time.time() - cached_start
        
        print(f"  Cached fetch time: {cached_time:.2f}s")
        if cached_time < 0.1:
            print("  ✅ Caching working (very fast)")
        else:
            print("  ⚠️ Caching may not be working optimally")
        
        # Test 4: Test with mix of cached/uncached
        print("\n4. Testing mixed cached/uncached symbols...")
        mixed_symbols = symbols[:3] + ["NEW/USD", "ANOTHER/USD"]  # 3 cached + 2 new
        
        start_time = time.time()
        mixed_prices = await coingecko.get_prices_batch(mixed_symbols)
        mixed_time = time.time() - start_time
        
        print(f"  Mixed fetch time: {mixed_time:.2f}s")
        print(f"  Prices returned: {len([p for p in mixed_prices.values() if p is not None])}/{len(mixed_symbols)}")
        
        print("\n" + "="*80)
        print("✅ BATCH PRICE FETCHING TEST COMPLETE")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Batch price fetching test failed: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}\n")
        return False


async def main():
    """Main test function"""
    success = await test_batch_price_fetching()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
