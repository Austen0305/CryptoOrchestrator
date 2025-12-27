"""
Quick Test Check
Quick verification that all enhancements are importable and basic functionality works
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*80)
print("QUICK TEST CHECK - CryptoOrchestrator Enhancements")
print("="*80)

results = []

# Test 1: Token Registry
try:
    from server_fastapi.services.blockchain.token_registry import get_token_registry
    registry = get_token_registry()
    print("✅ Token Registry: Import successful")
    results.append(("Token Registry", True))
except Exception as e:
    print(f"❌ Token Registry: Import failed - {e}")
    results.append(("Token Registry", False))

# Test 2: Transaction Batcher
try:
    from server_fastapi.services.blockchain.transaction_batcher import get_transaction_batcher
    batcher = get_transaction_batcher()
    print("✅ Transaction Batcher: Import successful")
    results.append(("Transaction Batcher", True))
except Exception as e:
    print(f"❌ Transaction Batcher: Import failed - {e}")
    results.append(("Transaction Batcher", False))

# Test 3: MEV Protection
try:
    from server_fastapi.services.blockchain.mev_protection import get_mev_protection_service
    mev_service = get_mev_protection_service()
    print("✅ MEV Protection: Import successful")
    results.append(("MEV Protection", True))
except Exception as e:
    print(f"❌ MEV Protection: Import failed - {e}")
    results.append(("MEV Protection", False))

# Test 4: DEX Position Model
try:
    from server_fastapi.models.dex_position import DEXPosition
    print("✅ DEX Position Model: Import successful")
    results.append(("DEX Position Model", True))
except Exception as e:
    print(f"❌ DEX Position Model: Import failed - {e}")
    results.append(("DEX Position Model", False))

# Test 5: DEX Position Service
try:
    from server_fastapi.services.trading.dex_position_service import DEXPositionService
    print("✅ DEX Position Service: Import successful")
    results.append(("DEX Position Service", True))
except Exception as e:
    print(f"❌ DEX Position Service: Import failed - {e}")
    results.append(("DEX Position Service", False))

# Test 6: CoinGecko Batch Fetching
try:
    from server_fastapi.services.integrations.coingecko_service import CoinGeckoService
    coingecko = CoinGeckoService()
    if hasattr(coingecko, 'get_prices_batch'):
        print("✅ CoinGecko Batch Fetching: Method exists")
        results.append(("CoinGecko Batch Fetching", True))
    else:
        print("❌ CoinGecko Batch Fetching: Method not found")
        results.append(("CoinGecko Batch Fetching", False))
except Exception as e:
    print(f"❌ CoinGecko Batch Fetching: Import failed - {e}")
    results.append(("CoinGecko Batch Fetching", False))

# Test 7: Rubic Retry Logic
try:
    from server_fastapi.services.integrations.rubic_service import RubicService
    rubic = RubicService()
    if hasattr(rubic, 'max_retries') and hasattr(rubic, 'check_bridge_status'):
        print("✅ Rubic Retry Logic: Methods exist")
        results.append(("Rubic Retry Logic", True))
    else:
        print("❌ Rubic Retry Logic: Methods not found")
        results.append(("Rubic Retry Logic", False))
except Exception as e:
    print(f"❌ Rubic Retry Logic: Import failed - {e}")
    results.append(("Rubic Retry Logic", False))

# Test 8: API Routes
try:
    from server_fastapi.routes.dex_positions import router as positions_router
    from server_fastapi.routes.mev_protection import router as mev_router
    print("✅ API Routes: Import successful")
    results.append(("API Routes", True))
except Exception as e:
    print(f"❌ API Routes: Import failed - {e}")
    results.append(("API Routes", False))

# Test 9: Migration Files
migration_files = [
    "alembic/versions/convert_bot_exchange_to_chain_id.py",
    "alembic/versions/add_dex_positions_table.py"
]

migrations_exist = all((project_root / f).exists() for f in migration_files)
if migrations_exist:
    print("✅ Migration Files: All exist")
    results.append(("Migration Files", True))
else:
    print("❌ Migration Files: Some missing")
    results.append(("Migration Files", False))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

total = len(results)
passed = sum(1 for _, success in results if success)
failed = total - passed

for name, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {name}: {status}")

print(f"\nTotal: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed == 0:
    print("\n✅ ALL CHECKS PASSED!")
    sys.exit(0)
else:
    print(f"\n❌ {failed} CHECK(S) FAILED")
    sys.exit(1)
