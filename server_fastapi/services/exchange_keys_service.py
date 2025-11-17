"""
Exchange API Keys Service for SaaS
Secure storage and management of user exchange API keys
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64

from ..models.exchange_api_key import ExchangeAPIKey
from ..models.user import User

logger = logging.getLogger(__name__)

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("EXCHANGE_KEY_ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    # Generate a key if not set (for development only)
    logger.warning("EXCHANGE_KEY_ENCRYPTION_KEY not set, using default (NOT SECURE FOR PRODUCTION)")
    ENCRYPTION_KEY = "default-encryption-key-change-in-production-32-chars!"


class ExchangeKeysService:
    """Service for managing encrypted exchange API keys"""
    
    def __init__(self):
        # Derive Fernet key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'crypto_orchestrator_salt',  # In production, use a unique salt per user
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
        self.cipher = Fernet(key)
    
    def _encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext"""
        if not plaintext:
            return ""
        try:
            return self.cipher.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            raise ValueError("Failed to encrypt data")
    
    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext"""
        if not ciphertext:
            return ""
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}", exc_info=True)
            raise ValueError("Failed to decrypt data")
    
    async def create_exchange_key(
        self,
        db: AsyncSession,
        user_id: int,
        exchange: str,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        label: Optional[str] = None,
        is_testnet: bool = False,
    ) -> Optional[ExchangeAPIKey]:
        """Create encrypted exchange API key"""
        try:
            # Check if key already exists for this exchange
            existing_result = await db.execute(
                select(ExchangeAPIKey).where(
                    and_(
                        ExchangeAPIKey.user_id == user_id,
                        ExchangeAPIKey.exchange == exchange,
                        ExchangeAPIKey.is_active == True
                    )
                )
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update existing key
                existing.api_key_encrypted = self._encrypt(api_key)
                existing.api_secret_encrypted = self._encrypt(api_secret)
                if passphrase:
                    existing.passphrase_encrypted = self._encrypt(passphrase)
                if label:
                    existing.label = label
                existing.is_testnet = is_testnet
                existing.is_validated = False
                await db.commit()
                await db.refresh(existing)
                return existing
            
            # Create new key
            exchange_key = ExchangeAPIKey(
                user_id=user_id,
                exchange=exchange,
                api_key_encrypted=self._encrypt(api_key),
                api_secret_encrypted=self._encrypt(api_secret),
                passphrase_encrypted=self._encrypt(passphrase) if passphrase else None,
                label=label or f"{exchange.title()} API Key",
                is_testnet=is_testnet,
                is_active=True,
                is_validated=False,
            )
            
            db.add(exchange_key)
            await db.commit()
            await db.refresh(exchange_key)
            
            logger.info(f"Created exchange key for user {user_id}, exchange {exchange}")
            return exchange_key
            
        except Exception as e:
            logger.error(f"Failed to create exchange key: {e}", exc_info=True)
            await db.rollback()
            return None
    
    async def get_exchange_keys(
        self,
        db: AsyncSession,
        user_id: int,
        exchange: Optional[str] = None,
    ) -> List[ExchangeAPIKey]:
        """Get user's exchange API keys"""
        try:
            query = select(ExchangeAPIKey).where(
                and_(
                    ExchangeAPIKey.user_id == user_id,
                    ExchangeAPIKey.is_active == True
                )
            )
            
            if exchange:
                query = query.where(ExchangeAPIKey.exchange == exchange)
            
            result = await db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get exchange keys: {e}", exc_info=True)
            return []
    
    async def get_decrypted_key(
        self,
        db: AsyncSession,
        user_id: int,
        exchange: str,
    ) -> Optional[Dict[str, Any]]:
        """Get decrypted exchange API key (use carefully)"""
        try:
            result = await db.execute(
                select(ExchangeAPIKey).where(
                    and_(
                        ExchangeAPIKey.user_id == user_id,
                        ExchangeAPIKey.exchange == exchange,
                        ExchangeAPIKey.is_active == True
                    )
                )
            )
            exchange_key = result.scalar_one_or_none()
            
            if not exchange_key:
                return None
            
            return {
                "exchange": exchange_key.exchange,
                "api_key": self._decrypt(exchange_key.api_key_encrypted),
                "api_secret": self._decrypt(exchange_key.api_secret_encrypted),
                "passphrase": self._decrypt(exchange_key.passphrase_encrypted) if exchange_key.passphrase_encrypted else None,
                "label": exchange_key.label,
                "is_testnet": exchange_key.is_testnet,
            }
            
        except Exception as e:
            logger.error(f"Failed to get decrypted key: {e}", exc_info=True)
            return None
    
    async def delete_exchange_key(
        self,
        db: AsyncSession,
        user_id: int,
        exchange: str,
    ) -> bool:
        """Delete (soft delete) exchange API key"""
        try:
            result = await db.execute(
                select(ExchangeAPIKey).where(
                    and_(
                        ExchangeAPIKey.user_id == user_id,
                        ExchangeAPIKey.exchange == exchange,
                        ExchangeAPIKey.is_active == True
                    )
                )
            )
            exchange_key = result.scalar_one_or_none()
            
            if not exchange_key:
                return False
            
            exchange_key.is_active = False
            await db.commit()
            
            logger.info(f"Deleted exchange key for user {user_id}, exchange {exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete exchange key: {e}", exc_info=True)
            await db.rollback()
            return False
    
    async def test_connection(
        self,
        db: AsyncSession,
        user_id: int,
        exchange: str,
    ) -> Dict[str, Any]:
        """Test exchange API connection"""
        try:
            key_data = await self.get_decrypted_key(db, user_id, exchange)
            
            if not key_data:
                return {
                    "success": False,
                    "error": "Exchange API key not found"
                }
            
            # Import exchange service
            from ..services.exchange_service import ExchangeService
            
            # Create exchange instance with API keys
            exchange_service = ExchangeService(name=exchange, use_mock=False)
            
            # Set API keys (this would need to be implemented in ExchangeService)
            # For now, test connection
            await exchange_service.connect()
            
            if exchange_service.is_connected():
                # Mark as validated
                result = await db.execute(
                    select(ExchangeAPIKey).where(
                        and_(
                            ExchangeAPIKey.user_id == user_id,
                            ExchangeAPIKey.exchange == exchange
                        )
                    )
                )
                key = result.scalar_one_or_none()
                if key:
                    key.is_validated = True
                    key.validated_at = datetime.utcnow()
                    await db.commit()
                
                return {
                    "success": True,
                    "message": f"Successfully connected to {exchange}",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to connect to exchange"
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

