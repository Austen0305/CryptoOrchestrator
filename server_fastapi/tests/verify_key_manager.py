import asyncio
import sys
import os
import json
import logging
from eth_account import Account

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from server_fastapi.services.blockchain.key_management import get_key_management_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_key_management():
    print("Testing Key Management Service (Local Encrypted)...")

    kms = get_key_management_service()

    # 1. Generate Test Data
    acct = Account.create()
    wallet_address = acct.address
    private_key = acct.key.hex()

    print(f"Generated Wallet: {wallet_address}")

    # 2. Store Key
    print("Storing Key...")
    success = await kms.store_private_key(wallet_address, 1, private_key)
    assert success
    print("[PASS] Key stored successfully")

    # 3. Retrieve Key
    print("Retrieving Key...")
    retrieved_key = await kms.get_private_key(wallet_address, 1)

    print(f"Original: {private_key}")
    print(f"Retrieved: {retrieved_key}")

    assert retrieved_key == private_key
    print("[PASS] Key retrieved matches original")

    # 4. Verify Encryption on Disk
    print("Verifying Encryption on Disk...")
    keys_file_path = "data/secure/keys.json"
    assert os.path.exists(keys_file_path), "Keys file does not exist"

    with open(keys_file_path, "r") as f:
        data = json.load(f)

    encrypted_val = data.get(wallet_address.lower())
    assert encrypted_val is not None
    assert encrypted_val != private_key
    assert (
        "0x" not in encrypted_val
    )  # Highly unlikely to appear in fernet token by chance in a way that looks like private key
    assert len(encrypted_val) > len(private_key)

    print(f"[PASS] Disk verification passed. Stored value: {encrypted_val[:20]}...")

    # Cleanup (optional, but good for cleanliness)
    # Could remove key from file, but for now we leave it as artifact of test


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_key_management())
    loop.close()
