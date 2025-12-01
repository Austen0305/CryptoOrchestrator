"""
Exchange API Key Service
Manages encryption and storage of exchange API keys
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as PBKDF2
except ImportError:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    except ImportError:
        # Fallback for older cryptography versions
        from cryptography.hazmat.primitives.kdf import PBKDF2HMAC as PBKDF2
from cryptography.hazmat.backends import default_backend
import base64

from ...database import get_db_context
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Import ExchangeAPIKey model with fallback
try:
    from ...models.exchange_api_key import ExchangeAPIKey
except ImportError:
    # Fallback: define a simple dict-based storage for development
    ExchangeAPIKey = None
    logger.warning("ExchangeAPIKey model not found, using in-memory storage")


class ExchangeKeyService:
    """Service for managing exchange API keys with encryption"""

    def __init__(self):
        # Get encryption key from environment
        encryption_key = os.getenv("EXCHANGE_KEY_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a key if not set (for development only)
            logger.warning("EXCHANGE_KEY_ENCRYPTION_KEY not set, using default (NOT SECURE FOR PRODUCTION)")
            encryption_key = "default-encryption-key-change-in-production-32-chars!"
        
        # Derive Fernet key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'crypto_orchestrator_salt',  # In production, use a unique salt per user
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        self.cipher = Fernet(key)

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext"""
        if not plaintext:
            return ""
        return self.cipher.encrypt(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext"""
        if not ciphertext:
            return ""
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            # Don't log the actual error message which might contain sensitive data
            logger.error("Failed to decrypt API key: decryption error")
            raise ValueError("Failed to decrypt API key")

    async def create_api_key(
        self,
        user_id: str,
        exchange: str,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        label: Optional[str] = None,
        permissions: Optional[str] = None,
        is_testnet: bool = False,
        ip_whitelist: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create and store encrypted exchange API key"""
        try:
            # Convert user_id to int if it's a string
            user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1  # Default to 1 if conversion fails
            
            if ExchangeAPIKey is None:
                # Fallback to in-memory storage
                import uuid
                key_id = str(uuid.uuid4())
                encrypted_key = self._encrypt(api_key)
                encrypted_secret = self._encrypt(api_secret)
                encrypted_passphrase = self._encrypt(passphrase) if passphrase else None
                
                api_key_obj = {
                    "id": key_id,
                    "user_id": user_id_int,
                    "exchange": exchange,
                    "api_key_encrypted": encrypted_key,
                    "api_secret_encrypted": encrypted_secret,
                    "passphrase_encrypted": encrypted_passphrase,
                    "label": label or f"{exchange.title()} API Key",
                    "permissions": permissions or "read,write,trade",
                    "is_active": True,
                    "is_testnet": is_testnet,
                    "is_validated": False,
                    "ip_whitelist": ip_whitelist,
                    "created_at": datetime.utcnow(),
                }
                # Store in memory (would be database in production)
                if not hasattr(self, '_memory_store'):
                    self._memory_store = {}
                self._memory_store[key_id] = api_key_obj
                logger.info(f"Created exchange API key for user {user_id_int} on {exchange} (in-memory)")
                return api_key_obj
            
            async with get_db_context() as db:
                # Encrypt credentials
                encrypted_key = self._encrypt(api_key)
                encrypted_secret = self._encrypt(api_secret)
                encrypted_passphrase = self._encrypt(passphrase) if passphrase else None

                # Create API key record
                api_key_obj = ExchangeAPIKey(
                    user_id=user_id_int,
                    exchange=exchange,
                    api_key_encrypted=encrypted_key,
                    api_secret_encrypted=encrypted_secret,
                    passphrase_encrypted=encrypted_passphrase,
                    label=label or f"{exchange.title()} API Key",
                    permissions=permissions or "read,write,trade",
                    is_active=True,
                    is_testnet=is_testnet,
                    is_validated=False,
                    ip_whitelist=ip_whitelist,
                )

                db.add(api_key_obj)
                await db.commit()
                await db.refresh(api_key_obj)

                logger.info(f"Created exchange API key for user {user_id_int} on {exchange}")
                return {
                    "id": str(api_key_obj.id),
                    "user_id": str(api_key_obj.user_id),
                    "exchange": api_key_obj.exchange,
                    "label": api_key_obj.label,
                    "permissions": api_key_obj.permissions,
                    "is_active": api_key_obj.is_active,
                    "is_testnet": api_key_obj.is_testnet,
                    "is_validated": api_key_obj.is_validated,
                    "created_at": api_key_obj.created_at.isoformat() if api_key_obj.created_at else None,
                }

        except Exception as e:
            logger.error(f"Failed to create exchange API key: {e}")
            raise

    async def get_api_key(
        self, user_id: str, exchange: str, include_secrets: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get exchange API key (decrypted if include_secrets is True)"""
        try:
            # Convert user_id to int if it's a string
            user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1
            
            if ExchangeAPIKey is None:
                # Fallback to in-memory storage
                if not hasattr(self, '_memory_store'):
                    return None
                for key_obj in self._memory_store.values():
                    if (key_obj.get("user_id") == user_id_int and 
                        key_obj.get("exchange") == exchange and 
                        key_obj.get("is_active", True)):
                        response = {
                            "id": key_obj["id"],
                            "user_id": key_obj["user_id"],
                            "exchange": key_obj["exchange"],
                            "label": key_obj.get("label"),
                            "permissions": key_obj.get("permissions"),
                            "is_active": key_obj.get("is_active", True),
                            "is_testnet": key_obj.get("is_testnet", False),
                            "is_validated": key_obj.get("is_validated", False),
                            "validated_at": key_obj.get("validated_at"),
                            "last_used_at": key_obj.get("last_used_at"),
                            "created_at": key_obj.get("created_at").isoformat() if isinstance(key_obj.get("created_at"), datetime) else None,
                        }
                        if include_secrets:
                            response["api_key"] = self._decrypt(key_obj["api_key_encrypted"])
                            response["api_secret"] = self._decrypt(key_obj["api_secret_encrypted"])
                            if key_obj.get("passphrase_encrypted"):
                                response["passphrase"] = self._decrypt(key_obj["passphrase_encrypted"])
                        return response
                return None
            
            async with get_db_context() as db:
                result = await db.execute(
                    select(ExchangeAPIKey).where(
                        ExchangeAPIKey.user_id == user_id_int,
                        ExchangeAPIKey.exchange == exchange,
                        ExchangeAPIKey.is_active == True,
                    )
                )
                api_key_obj = result.scalar_one_or_none()

                if not api_key_obj:
                    return None

                response = {
                    "id": str(api_key_obj.id),
                    "user_id": str(api_key_obj.user_id),
                    "exchange": api_key_obj.exchange,
                    "label": api_key_obj.label,
                    "permissions": api_key_obj.permissions,
                    "is_active": api_key_obj.is_active,
                    "is_testnet": api_key_obj.is_testnet,
                    "is_validated": api_key_obj.is_validated,
                    "validated_at": api_key_obj.validated_at.isoformat() if api_key_obj.validated_at else None,
                    "last_used_at": api_key_obj.last_used_at.isoformat() if api_key_obj.last_used_at else None,
                    "created_at": api_key_obj.created_at.isoformat() if api_key_obj.created_at else None,
                }

                if include_secrets:
                    response["api_key"] = self._decrypt(api_key_obj.api_key_encrypted)
                    response["api_secret"] = self._decrypt(api_key_obj.api_secret_encrypted)
                    if api_key_obj.passphrase_encrypted:
                        response["passphrase"] = self._decrypt(api_key_obj.passphrase_encrypted)

                return response

        except Exception as e:
            logger.error(f"Failed to get exchange API key: {e}")
            return None

    async def validate_api_key(self, user_id: str, exchange: str) -> bool:
        """Validate exchange API key by testing connection"""
        try:
            api_key_data = await self.get_api_key(user_id, exchange, include_secrets=True)
            if not api_key_data:
                return False

            # Test connection with exchange
            import ccxt
            exchange_class = getattr(ccxt, exchange, None)
            if not exchange_class:
                logger.error(f"Exchange {exchange} not found in ccxt")
                return False

            exchange_instance = exchange_class({
                "apiKey": api_key_data["api_key"],
                "secret": api_key_data["api_secret"],
                "enableRateLimit": True,
                "options": {
                    "testnet": api_key_data["is_testnet"],
                },
            })

            # Test connection by fetching balance
            await exchange_instance.load_markets()
            await exchange_instance.fetch_balance()

            # Convert user_id to int
            user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1
            
            # Update validation status
            if ExchangeAPIKey is None:
                # Fallback to in-memory storage
                if hasattr(self, '_memory_store'):
                    for key_obj in self._memory_store.values():
                        if (key_obj.get("user_id") == user_id_int and 
                            key_obj.get("exchange") == exchange):
                            key_obj["is_validated"] = True
                            key_obj["validated_at"] = datetime.utcnow()
            else:
                async with get_db_context() as db:
                    await db.execute(
                        update(ExchangeAPIKey)
                        .where(
                            ExchangeAPIKey.user_id == user_id_int,
                            ExchangeAPIKey.exchange == exchange,
                        )
                        .values(
                            is_validated=True,
                            validated_at=datetime.utcnow(),
                        )
                    )
                    await db.commit()

            logger.info(f"Validated exchange API key for user {user_id} on {exchange}")
            return True

        except Exception as e:
            logger.error(f"Failed to validate exchange API key: {e}")
            return False

    async def delete_api_key(self, user_id: str, exchange: str) -> bool:
        """Delete exchange API key"""
        try:
            # Convert user_id to int
            user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1
            
            if ExchangeAPIKey is None:
                # Fallback to in-memory storage
                if hasattr(self, '_memory_store'):
                    keys_to_delete = [
                        key_id for key_id, key_obj in self._memory_store.items()
                        if (key_obj.get("user_id") == user_id_int and 
                            key_obj.get("exchange") == exchange)
                    ]
                    for key_id in keys_to_delete:
                        del self._memory_store[key_id]
                    logger.info(f"Deleted exchange API key for user {user_id_int} on {exchange} (in-memory)")
                    return len(keys_to_delete) > 0
                return False
            
            async with get_db_context() as db:
                await db.execute(
                    delete(ExchangeAPIKey).where(
                        ExchangeAPIKey.user_id == user_id_int,
                        ExchangeAPIKey.exchange == exchange,
                    )
                )
                await db.commit()

            logger.info(f"Deleted exchange API key for user {user_id_int} on {exchange}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete exchange API key: {e}")
            return False

    async def list_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """List all exchange API keys for user"""
        try:
            # Convert user_id to int
            user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1
            
            if ExchangeAPIKey is None:
                # Fallback to in-memory storage
                if not hasattr(self, '_memory_store'):
                    return []
                return [
                    {
                        "id": key_obj["id"],
                        "exchange": key_obj["exchange"],
                        "label": key_obj.get("label"),
                        "permissions": key_obj.get("permissions"),
                        "is_active": key_obj.get("is_active", True),
                        "is_testnet": key_obj.get("is_testnet", False),
                        "is_validated": key_obj.get("is_validated", False),
                        "validated_at": key_obj.get("validated_at").isoformat() if isinstance(key_obj.get("validated_at"), datetime) else None,
                        "last_used_at": key_obj.get("last_used_at").isoformat() if isinstance(key_obj.get("last_used_at"), datetime) else None,
                        "created_at": key_obj.get("created_at").isoformat() if isinstance(key_obj.get("created_at"), datetime) else None,
                    }
                    for key_obj in self._memory_store.values()
                    if key_obj.get("user_id") == user_id_int and key_obj.get("is_active", True)
                ]
            
            async with get_db_context() as db:
                result = await db.execute(
                    select(ExchangeAPIKey).where(
                        ExchangeAPIKey.user_id == user_id_int,
                        ExchangeAPIKey.is_active == True,
                    )
                )
                api_keys = result.scalars().all()

                return [
                    {
                        "id": str(api_key.id),
                        "exchange": api_key.exchange,
                        "label": api_key.label,
                        "permissions": api_key.permissions,
                        "is_active": api_key.is_active,
                        "is_testnet": api_key.is_testnet,
                        "is_validated": api_key.is_validated,
                        "validated_at": api_key.validated_at.isoformat() if api_key.validated_at else None,
                        "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                        "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
                    }
                    for api_key in api_keys
                ]

        except Exception as e:
            logger.error(f"Failed to list exchange API keys: {e}")
            return []


# Global instance
exchange_key_service = ExchangeKeyService()

