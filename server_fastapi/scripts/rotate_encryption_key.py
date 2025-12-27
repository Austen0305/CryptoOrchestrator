"""
Secret Rotation Script
Rotates encryption keys for exchange API keys and other secrets

Usage:
    python -m server_fastapi.scripts.rotate_encryption_key.py --old-key <old_key> --new-key <new_key>
    python -m server_fastapi.scripts.rotate_encryption_key.py --dry-run
"""

import os
import sys
import argparse
import logging
import secrets
from typing import Optional
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64

from server_fastapi.database import get_db_context
from sqlalchemy import select, text

# ExchangeAPIKey model removed - platform uses blockchain/DEX trading exclusively
# This script is kept for migrating existing exchange API keys in the database
# Note: Exchange API keys are no longer used, but data is kept for audit trail
try:
    from server_fastapi.models.exchange_api_key import ExchangeAPIKey

    EXCHANGE_API_KEY_AVAILABLE = True
except ImportError:
    # Model removed - use raw SQL if needed for migration
    ExchangeAPIKey = None
    EXCHANGE_API_KEY_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EncryptionKeyRotator:
    """Rotates encryption keys for exchange API keys"""

    def __init__(self, old_key: str, new_key: str):
        self.old_key = old_key
        self.new_key = new_key
        self.old_cipher = self._create_cipher(old_key)
        self.new_cipher = self._create_cipher(new_key)

    def _create_cipher(self, encryption_key: str) -> Fernet:
        """Create Fernet cipher from encryption key"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"crypto_orchestrator_salt",
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        return Fernet(key)

    def _decrypt_with_old_key(self, ciphertext: str) -> str:
        """Decrypt using old key"""
        try:
            return self.old_cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt with old key: {e}")
            raise

    def _encrypt_with_new_key(self, plaintext: str) -> str:
        """Encrypt using new key"""
        return self.new_cipher.encrypt(plaintext.encode()).decode()

    async def rotate_all_keys(self, dry_run: bool = False) -> dict:
        """Rotate all exchange API keys (REMOVED - platform uses blockchain/DEX trading exclusively)"""
        stats = {"total_keys": 0, "rotated": 0, "failed": 0, "errors": []}

        if not EXCHANGE_API_KEY_AVAILABLE:
            logger.warning(
                "ExchangeAPIKey model not available - platform uses DEX-only trading"
            )
            logger.info(
                "Exchange API keys removed - platform uses blockchain/DEX trading exclusively."
            )
            return stats

        try:
            async with get_db_context() as db:
                # Get all exchange API keys (if table still exists)
                try:
                    result = await db.execute(select(ExchangeAPIKey))
                    keys = result.scalars().all()
                except Exception as e:
                    logger.warning(f"Exchange API keys table may not exist: {e}")
                    logger.info(
                        "Exchange API keys removed - platform uses blockchain wallets"
                    )
                    return stats

                stats["total_keys"] = len(keys)
                logger.info(f"Found {len(keys)} exchange API keys to rotate")

                if dry_run:
                    logger.info("DRY RUN MODE - No changes will be made")
                    return stats

                # Rotate each key
                for key_obj in keys:
                    try:
                        # Decrypt with old key
                        api_key = self._decrypt_with_old_key(key_obj.api_key_encrypted)
                        api_secret = self._decrypt_with_old_key(
                            key_obj.api_secret_encrypted
                        )
                        passphrase = None
                        if key_obj.passphrase_encrypted:
                            passphrase = self._decrypt_with_old_key(
                                key_obj.passphrase_encrypted
                            )

                        # Encrypt with new key
                        key_obj.api_key_encrypted = self._encrypt_with_new_key(api_key)
                        key_obj.api_secret_encrypted = self._encrypt_with_new_key(
                            api_secret
                        )
                        if passphrase:
                            key_obj.passphrase_encrypted = self._encrypt_with_new_key(
                                passphrase
                            )

                        stats["rotated"] += 1
                        logger.info(
                            f"Rotated key {key_obj.id} for user {key_obj.user_id} on {key_obj.exchange}"
                        )

                    except Exception as e:
                        stats["failed"] += 1
                        error_msg = f"Failed to rotate key {key_obj.id}: {e}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg)

                # Commit all changes
                if stats["rotated"] > 0:
                    await db.commit()
                    logger.info(f"Successfully rotated {stats['rotated']} keys")

        except Exception as e:
            logger.error(f"Error during key rotation: {e}", exc_info=True)
            raise

        return stats


def generate_new_key() -> str:
    """Generate a new secure encryption key"""
    return secrets.token_urlsafe(32)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Rotate encryption keys for exchange API keys"
    )
    parser.add_argument(
        "--old-key",
        type=str,
        help="Old encryption key (or set EXCHANGE_KEY_ENCRYPTION_KEY_OLD env var)",
    )
    parser.add_argument(
        "--new-key",
        type=str,
        help="New encryption key (or set EXCHANGE_KEY_ENCRYPTION_KEY_NEW env var, or auto-generate)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--generate-key",
        action="store_true",
        help="Generate a new encryption key and print it",
    )

    args = parser.parse_args()

    # Generate key if requested
    if args.generate_key:
        new_key = generate_new_key()
        print(f"\nGenerated new encryption key:")
        print(f"EXCHANGE_KEY_ENCRYPTION_KEY={new_key}")
        print(
            f"\n[WARN]  Keep this key secure! Store it in your environment variables."
        )
        return

    # Get keys from args or environment
    old_key = args.old_key or os.getenv("EXCHANGE_KEY_ENCRYPTION_KEY_OLD")
    new_key = args.new_key or os.getenv("EXCHANGE_KEY_ENCRYPTION_KEY_NEW")

    if not old_key:
        logger.error(
            "Old encryption key not provided. Use --old-key or set EXCHANGE_KEY_ENCRYPTION_KEY_OLD"
        )
        sys.exit(1)

    if not new_key:
        logger.warning("New encryption key not provided. Generating a new one...")
        new_key = generate_new_key()
        print(f"\nGenerated new encryption key: {new_key}")
        print(
            f"[WARN]  Save this key! Set it as EXCHANGE_KEY_ENCRYPTION_KEY in your environment."
        )

        if not args.dry_run:
            response = input("\nContinue with rotation? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Rotation cancelled")
                return

    # Perform rotation
    try:
        rotator = EncryptionKeyRotator(old_key, new_key)
        stats = await rotator.rotate_all_keys(dry_run=args.dry_run)

        print("\n" + "=" * 60)
        print("Rotation Summary")
        print("=" * 60)
        print(f"Total keys: {stats['total_keys']}")
        print(f"Rotated: {stats['rotated']}")
        print(f"Failed: {stats['failed']}")

        if stats["errors"]:
            print("\nErrors:")
            for error in stats["errors"]:
                print(f"  - {error}")

        if args.dry_run:
            print("\n[WARN]  This was a dry run. No changes were made.")
        else:
            print("\n[OK] Rotation complete!")
            print(
                f"\n[WARN]  Don't forget to update EXCHANGE_KEY_ENCRYPTION_KEY={new_key}"
            )

    except Exception as e:
        logger.error(f"Rotation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
